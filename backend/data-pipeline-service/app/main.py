import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("data-pipeline-worker")

async def main():
    logger.info("Khởi động Data Pipeline Worker cho Chùa Linh Ứng...")
    logger.info("Worker đang ở trạng thái chờ kết nối RabbitMQ...")
    # Giữ loop chạy để container không tắt ngay
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Dừng Data Pipeline Worker.")
