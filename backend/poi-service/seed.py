import asyncio
from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import SupportedLanguage, SystemMetadata

async def seed_poi_data():
    print("🌱 Bắt đầu khởi tạo dữ liệu mẫu cho POI DB...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Seed 15 Supported Languages
        languages = [
            {"code": "vi", "name": "Vietnamese", "native": "Tiếng Việt", "fallback": True, "tts": True},
            {"code": "en", "name": "English", "native": "English", "fallback": False, "tts": True},
            {"code": "zh", "name": "Chinese", "native": "中文 (简体)", "fallback": False, "tts": True},
            {"code": "ja", "name": "Japanese", "native": "日本語", "fallback": False, "tts": True},
            {"code": "ko", "name": "Korean", "native": "한국어", "fallback": False, "tts": True},
            {"code": "fr", "name": "French", "native": "Français", "fallback": False, "tts": True},
            {"code": "de", "name": "German", "native": "Deutsch", "fallback": False, "tts": True},
            {"code": "es", "name": "Spanish", "native": "Español", "fallback": False, "tts": True},
            {"code": "th", "name": "Thai", "native": "ไทย", "fallback": False, "tts": True},
            {"code": "ru", "name": "Russian", "native": "Русский", "fallback": False, "tts": True},
            {"code": "pt", "name": "Portuguese", "native": "Português", "fallback": False, "tts": True},
            {"code": "it", "name": "Italian", "native": "Italiano", "fallback": False, "tts": True},
            {"code": "id", "name": "Indonesian", "native": "Bahasa Indonesia", "fallback": False, "tts": True},
            {"code": "ar", "name": "Arabic", "native": "العربية", "fallback": False, "tts": True},
            {"code": "hi", "name": "Hindi", "native": "हिन्दी", "fallback": False, "tts": True},
        ]

        for lang in languages:
            res = await session.execute(
                select(SupportedLanguage).where(SupportedLanguage.language_code == lang["code"])
            )
            existing = res.scalars().first()
            if not existing:
                new_lang = SupportedLanguage(
                    language_code=lang["code"],
                    language_name=lang["name"],
                    native_name=lang["native"],
                    is_fallback=lang["fallback"],
                    tts_supported=lang["tts"],
                    is_active=True
                )
                session.add(new_lang)
                print(f" -> Đã thêm ngôn ngữ: {lang['code']} ({lang['native']})")

        # 2. Seed SystemMetadata (poi_data_version = 1)
        res_meta = await session.execute(
            select(SystemMetadata).where(SystemMetadata.config_key == "poi_data_version")
        )
        existing_meta = res_meta.scalars().first()
        if not existing_meta:
            new_meta = SystemMetadata(
                config_key="poi_data_version",
                data_version=1,
                updated_at=datetime.utcnow()
            )
            session.add(new_meta)
            print(" -> Đã tạo SystemMetadata: poi_data_version = 1")
        else:
            print(" -> SystemMetadata đã tồn tại, bỏ qua.")

        await session.commit()
    print("✅ Hoàn thành khởi tạo dữ liệu mẫu cho POI DB!")

if __name__ == "__main__":
    asyncio.run(seed_poi_data())
