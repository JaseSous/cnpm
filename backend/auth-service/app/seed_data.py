import asyncio
import logging
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import User, TicketPackage
from app.services.security import hash_password

logger = logging.getLogger("auth-seed")

async def seed_data():
    logger.info("🌱 Bắt đầu khởi tạo dữ liệu mẫu cho Auth & Payment DB...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Seed Users (Admin & Staff)
        users_to_seed = [
            {
                "username": "admin",
                "password": "admin123",
                "role": "admin",
                "is_active": True
            },
            {
                "username": "staff",
                "password": "staff123",
                "role": "staff",
                "is_active": True
            },
            {
                "username": "staff01",
                "password": "staff123",
                "role": "staff",
                "is_active": True
            }
        ]

        for u in users_to_seed:
            result = await session.execute(select(User).where(User.username == u["username"]))
            existing_user = result.scalars().first()
            if not existing_user:
                new_user = User(
                    username=u["username"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                    is_active=u["is_active"]
                )
                session.add(new_user)
                logger.info(f" -> Đã tạo tài khoản {u['role']}: {u['username']}")
            else:
                logger.info(f" -> Tài khoản {u['username']} đã tồn tại, bỏ qua.")

        # 2. Seed TicketPackages
        packages_to_seed = [
            {
                "package_name": "Vé tham quan Chùa Linh Ứng",
                "price": 50000.00,
                "description": "Vé tiêu chuẩn tham quan các điểm di tích kèm hệ thống thuyết minh tự động GPS",
                "is_active": True
            },
            {
                "package_name": "Vé VIP Thuyết minh tự động",
                "price": 100000.00,
                "description": "Vé VIP tham quan trọn gói, thuyết minh đa ngôn ngữ và hỏi đáp Chatbot AI không giới hạn",
                "is_active": True
            }
        ]

        for pkg in packages_to_seed:
            result = await session.execute(
                select(TicketPackage).where(TicketPackage.package_name == pkg["package_name"])
            )
            existing_pkg = result.scalars().first()
            if not existing_pkg:
                new_pkg = TicketPackage(
                    package_name=pkg["package_name"],
                    price=pkg["price"],
                    description=pkg["description"],
                    is_active=pkg["is_active"]
                )
                session.add(new_pkg)
                logger.info(f" -> Đã tạo gói vé: {pkg['package_name']} ({pkg['price']:,.0f} VNĐ)")
            else:
                logger.info(f" -> Gói vé '{pkg['package_name']}' đã tồn tại, bỏ qua.")

        await session.commit()
    logger.info("✅ Hoàn thành khởi tạo dữ liệu mẫu Auth & Payment!")

if __name__ == "__main__":
    asyncio.run(seed_data())
