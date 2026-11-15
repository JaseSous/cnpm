import asyncio
import json
import logging
from typing import Optional
import aio_pika
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("data-pipeline-worker")

class PipelineWorker:
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.exchange: Optional[aio_pika.RobustExchange] = None
        self.is_running = False

    async def connect_rabbitmq(self):
        """Kết nối tới RabbitMQ và cấu hình các exchanges và queues"""
        logger.info(f"Đang kết nối tới RabbitMQ Broker: {settings.AMQP_URL}")
        self.connection = await aio_pika.connect_robust(
            settings.AMQP_URL,
            timeout=5
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=5)

        # 1. Declare Dead-Letter Exchange (DLX) và Queue (DLQ)
        dlx_exchange = await self.channel.declare_exchange(
            "poi_dlx",
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        dlq_queue = await self.channel.declare_queue("poi.dlq", durable=True)
        await dlq_queue.bind(dlx_exchange, routing_key="dlq")

        # 2. Declare Topic Exchange chính
        self.exchange = await self.channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        # 3. Declare và bind 3 hàng đợi chính
        queue_args = {
            "x-dead-letter-exchange": "poi_dlx",
            "x-dead-letter-routing-key": "dlq"
        }
        self.queue_upserted = await self.channel.declare_queue(
            "poi.upserted", durable=True, arguments=queue_args
        )
        await self.queue_upserted.bind(self.exchange, routing_key="poi.upserted")

        self.queue_deleted = await self.channel.declare_queue(
            "poi.deleted", durable=True, arguments=queue_args
        )
        await self.queue_deleted.bind(self.exchange, routing_key="poi.deleted")

        self.queue_retry = await self.channel.declare_queue(
            "poi.retry", durable=True, arguments=queue_args
        )
        await self.queue_retry.bind(self.exchange, routing_key="poi.retry")

        logger.info("Đã thiết lập thành công 3 hàng đợi: poi.upserted, poi.deleted, poi.retry và DLQ!")

    async def on_message_upserted(self, message: aio_pika.IncomingMessage):
        """Tiêu thụ tin nhắn poi.upserted"""
        async with message.process(ignore_processed=True):
            try:
                payload = json.loads(message.body.decode("utf-8"))
                logger.info(f"Nhận sự kiện poi.upserted: POI #{payload.get('poi_id')} (v{payload.get('revision')})")
                from app.consumers.poi_upserted import process_poi_upserted
                await process_poi_upserted(payload, channel=self.channel)
            except Exception as e:
                logger.error(f"Lỗi khi xử lý tin nhắn poi.upserted: {e}")

    async def on_message_deleted(self, message: aio_pika.IncomingMessage):
        """Tiêu thụ tin nhắn poi.deleted"""
        async with message.process(ignore_processed=True):
            try:
                payload = json.loads(message.body.decode("utf-8"))
                logger.info(f"Nhận sự kiện poi.deleted: POI #{payload.get('poi_id')}")
                from app.consumers.poi_deleted import handle_poi_deleted
                await handle_poi_deleted(payload)
            except Exception as e:
                logger.error(f"Lỗi khi xử lý poi.deleted: {e}")

    async def on_message_retry(self, message: aio_pika.IncomingMessage):
        """Tiêu thụ tin nhắn poi.retry"""
        async with message.process(ignore_processed=True):
            try:
                payload = json.loads(message.body.decode("utf-8"))
                logger.info(f"Nhận sự kiện poi.retry: POI #{payload.get('poi_id')} (attempt {payload.get('attempt_count', 0)})")
                from app.consumers.poi_upserted import process_poi_upserted
                await process_poi_upserted(payload, channel=self.channel)
            except Exception as e:
                logger.error(f"Lỗi khi xử lý tin nhắn poi.retry: {e}")

    async def start(self):
        """Khởi động worker lắng nghe 3 hàng đợi"""
        self.is_running = True
        while self.is_running:
            try:
                await self.connect_rabbitmq()
                await self.queue_upserted.consume(self.on_message_upserted)
                await self.queue_deleted.consume(self.on_message_deleted)
                await self.queue_retry.consume(self.on_message_retry)
                logger.info("Data Pipeline Worker đã sẵn sàng tiêu thụ tin nhắn!")
                # Giữ loop chạy
                while self.is_running:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Lỗi kết nối RabbitMQ ({e}). Đang thử kết nối lại sau 5 giây...")
                await asyncio.sleep(5)

    async def stop(self):
        self.is_running = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Data Pipeline Worker đã dừng.")

from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
import os

worker = PipelineWorker()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi chạy Worker tiêu thụ RabbitMQ trong background task
    task = asyncio.create_task(worker.start())
    logger.info("Data Pipeline Worker background task đã khởi động.")
    yield
    # Dừng worker khi tắt container
    await worker.stop()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Chùa Linh Ứng - Data Pipeline Service",
    description="Worker tiêu thụ RabbitMQ: dịch thuật, sinh TTS audio và đồng bộ Vector embeddings",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health", tags=["System"])
async def health_check():
    has_gemini = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ("your-gemini-api-key", "dummy", ""))
    return {
        "status": "healthy",
        "service": "data-pipeline-service",
        "is_running": worker.is_running,
        "gemini_configured": has_gemini,
        "version": "1.2.0"
    }

async def main():
    try:
        await worker.start()
    except (KeyboardInterrupt, SystemExit):
        await worker.stop()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
