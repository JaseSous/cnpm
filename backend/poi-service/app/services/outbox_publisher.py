import asyncio
import logging
from datetime import datetime
import aio_pika
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import OutboxEvent

logger = logging.getLogger("outbox-publisher")

class OutboxPublisher:
    def __init__(self):
        self._running = False
        self._task = None
        self._connection = None
        self._channel = None
        self._exchange = None

    async def connect_rabbitmq(self) -> bool:
        """Kết nối tới RabbitMQ và thiết lập exchange/queues"""
        try:
            self._connection = await aio_pika.connect_robust(
                settings.AMQP_URL,
                timeout=3
            )
            self._channel = await self._connection.channel()

            # Declare Dead-Letter Exchange và Queue
            dlx_exchange = await self._channel.declare_exchange(
                "poi_dlx",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            dlq_queue = await self._channel.declare_queue("poi.dlq", durable=True)
            await dlq_queue.bind(dlx_exchange, routing_key="dlq")

            # Declare Exchange chính poi_events
            self._exchange = await self._channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            # Declare và bind các queue chính kèm Dead-Letter Exchange
            queue_args = {
                "x-dead-letter-exchange": "poi_dlx",
                "x-dead-letter-routing-key": "dlq"
            }
            for event_type in ["poi.upserted", "poi.deleted", "poi.retry"]:
                queue = await self._channel.declare_queue(
                    event_type,
                    durable=True,
                    arguments=queue_args
                )
                await queue.bind(self._exchange, routing_key=event_type)

            logger.info("Kết nối RabbitMQ và khởi tạo Exchanges/Queues thành công!")
            return True
        except Exception as e:
            logger.warning(f"Chưa thể kết nối tới RabbitMQ ({e}). Outbox Publisher sẽ thử lại ở chu kỳ tiếp theo.")
            return False

    async def publish_pending_events(self):
        """Quét và phát hành các sự kiện OutboxEvents chưa published"""
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.is_published == False)
                .order_by(OutboxEvent.created_at)
                .limit(50)
            )
            pending_events = res.scalars().all()

            if not pending_events:
                return

            if not self._exchange:
                connected = await self.connect_rabbitmq()
                if not connected:
                    return

            for event in pending_events:
                try:
                    message = aio_pika.Message(
                        body=event.payload_json.encode("utf-8"),
                        content_type="application/json",
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        headers={
                            "event_id": event.event_id,
                            "poi_id": event.poi_id,
                            "revision": event.revision,
                            "event_type": event.event_type
                        }
                    )
                    await self._exchange.publish(message, routing_key=event.event_type)
                    event.is_published = True
                    logger.info(f"Đã publish thành công sự kiện {event.event_type} [id={event.event_id}] lên RabbitMQ.")
                except Exception as e:
                    logger.error(f"Lỗi khi publish sự kiện {event.event_id}: {e}")
                    break

            await session.commit()

    async def run_loop(self):
        """Vòng lặp chạy ngầm mỗi 5 giây"""
        self._running = True
        logger.info("Outbox Publisher worker đã bắt đầu chạy.")
        while self._running:
            try:
                await self.publish_pending_events()
            except Exception as e:
                logger.error(f"Lỗi không mong muốn trong Outbox Publisher: {e}")
            await asyncio.sleep(5)

    def start(self):
        if not self._task:
            self._task = asyncio.create_task(self.run_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("Outbox Publisher worker đã dừng.")

outbox_publisher = OutboxPublisher()
