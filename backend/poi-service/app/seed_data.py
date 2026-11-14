import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import POI, POILocalization, SupportedLanguage, SystemMetadata

logger = logging.getLogger("poi-seed")

SAMPLE_REAL_POIS = [
    {
        "title": "Tượng Phật Bà Quan Âm Bãi Bụt",
        "description": "Tượng Bồ Tát Quán Thế Âm tại Chùa Linh Ứng Bãi Bụt có chiều cao 67 mét, đường kính tòa sen 35 mét, tương đương tòa nhà 30 tầng. Tượng đứng tựa lưng vào đỉnh núi Sơn Trà, mặt hướng ra biển Đông rộng lớn, một tay bắt ấn tam muội, tay kia cầm bình nước cam lộ như rưới an lành cho ngư dân vùng biển Đà Nẵng.",
        "latitude": 16.1005,
        "longitude": 108.2772,
        "trigger_radius": 50,
        "thumbnail_url": "https://images.unsplash.com/photo-1599818816752-60453c072c41?auto=format&fit=crop&w=800&q=80"
    },
    {
        "title": "Chánh Điện Chùa Linh Ứng",
        "description": "Chánh điện được xây dựng với kiến trúc mái ngói uốn cong hình rồng thanh thoát, cột trụ vững chãi khắc nổi họa tiết tinh xảo. Gian giữa thờ Đức Phật Thích Ca Mâu Ni, bên phải thờ Quán Thế Âm Bồ Tát, bên trái thờ Địa Tạng Vương Bồ Tát. Không gian nơi đây trang nghiêm, trầm mặc, phảng phất hương trầm thanh tịnh.",
        "latitude": 16.1008,
        "longitude": 108.2768,
        "trigger_radius": 30,
        "thumbnail_url": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80"
    },
    {
        "title": "Vườn Thập Bát La Hán",
        "description": "Hai bên đường dẫn vào Chánh điện là 18 pho tượng Thập Bát La Hán được tạc bằng đá hoa cương nguyên khối do các nghệ nhân làng đá mỹ nghệ Non Nước dày công chế tác. Mỗi bức tượng thể hiện một sắc thái biểu cảm hỷ, nộ, ái, ố tinh tế, mang triết lý nhân sinh sâu sắc của đạo Phật.",
        "latitude": 16.1003,
        "longitude": 108.2765,
        "trigger_radius": 40,
        "thumbnail_url": "https://images.unsplash.com/photo-1563897539633-7374c276c212?auto=format&fit=crop&w=800&q=80"
    },
    {
        "title": "Bảo Tháp Xá Lợi",
        "description": "Bảo tháp Xá Lợi cao 9 tầng nằm uy nghiêm trong khuôn viên chùa, là nơi lưu giữ xá lợi Phật và các bậc cao tăng đắc đạo. Từ trên bảo tháp, du khách có thể phóng tầm mắt ngắm trọn vẹn toàn cảnh bờ biển Mỹ Khê và thành phố Đà Nẵng lung linh từ trên cao.",
        "latitude": 16.1010,
        "longitude": 108.2770,
        "trigger_radius": 25,
        "thumbnail_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=800&q=80"
    },
    {
        "title": "Cổng Tam Quan",
        "description": "Cổng Tam Quan là lối vào chính của Chùa Linh Ứng Bãi Bụt, xây dựng theo lối kiến trúc truyền thống Á Đông với ba cửa: Không môn, Giới môn và Vô tướng môn. Bước qua Tam Quan là bước vào không gian thanh tịnh, gác lại mọi âu lo phiền muộn của chốn hồng trần.",
        "latitude": 16.0998,
        "longitude": 108.2775,
        "trigger_radius": 20,
        "thumbnail_url": "https://images.unsplash.com/photo-1508807526345-15e9b5f4eaff?auto=format&fit=crop&w=800&q=80"
    },
    {
        "title": "Vườn Lâm Tỳ Ni",
        "description": "Khu vườn tái hiện lại khung cảnh đức Phật Thích Ca Mâu Ni đản sinh dưới cội hoa Vô Ưu tại vườn Lâm Tỳ Ni cổ xưa. Không gian rợp bóng mát cây xanh, tiểu cảnh suối reo và đàn chim câu thân thiện, mang lại cảm giác an yên cho mọi bước chân hành hương.",
        "latitude": 16.1006,
        "longitude": 108.2762,
        "trigger_radius": 25,
        "thumbnail_url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80"
    }
]

SUPPORTED_LANGUAGES_INIT = [
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

async def seed_real_pois() -> int:
    """Nạp dữ liệu thực tế 6 điểm tham quan nổi bật của Chùa Linh Ứng"""
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Đảm bảo Supported Languages tồn tại
        langs_check = await session.execute(select(SupportedLanguage))
        if not langs_check.scalars().first():
            for lang in SUPPORTED_LANGUAGES_INIT:
                session.add(SupportedLanguage(
                    language_code=lang["code"],
                    language_name=lang["name"],
                    native_name=lang["native"],
                    is_fallback=lang["fallback"],
                    tts_supported=lang["tts"],
                    is_active=True
                ))
            await session.commit()

        # Kiểm tra xem đã có POI nào chưa
        existing = await session.execute(select(POI))
        if existing.scalars().first():
            logger.info("Dữ liệu POIs đã tồn tại sẵn, bỏ qua seed.")
            return 0

        # Lấy danh sách ngôn ngữ hỗ trợ
        langs_res = await session.execute(select(SupportedLanguage).where(SupportedLanguage.is_active == True))
        active_langs = langs_res.scalars().all()
        now = datetime.utcnow()

        inserted_count = 0
        for poi_data in SAMPLE_REAL_POIS:
            poi = POI(
                original_language_code="vi",
                original_title=poi_data["title"],
                original_description=poi_data["description"],
                latitude=poi_data["latitude"],
                longitude=poi_data["longitude"],
                trigger_radius=poi_data["trigger_radius"],
                thumbnail_url=poi_data["thumbnail_url"],
                revision=1,
                vector_status="Synced",
                created_at=now,
                updated_at=now
            )
            session.add(poi)
            await session.flush()  # Nhận poi_id

            # Tạo bản địa hóa tiếng Việt (gốc - Done)
            vi_loc = POILocalization(
                poi_id=poi.poi_id,
                language_code="vi",
                translated_title=poi_data["title"],
                translated_description=poi_data["description"],
                audio_url=f"/media/audios/poi_{poi.poi_id}_vi_rev1.mp3",
                applied_revision=1,
                status="Done",
                updated_at=now
            )
            session.add(vi_loc)

            # Tạo bản địa hóa các ngôn ngữ khác (trạng thái Done/Ready)
            for lang in active_langs:
                if lang.language_code == "vi":
                    continue
                loc = POILocalization(
                    poi_id=poi.poi_id,
                    language_code=lang.language_code,
                    translated_title=f"[{lang.language_code.upper()}] {poi_data['title']}",
                    translated_description=f"[{lang.language_code.upper()}] {poi_data['description']}",
                    audio_url=f"/media/audios/poi_{poi.poi_id}_{lang.language_code}_rev1.mp3",
                    applied_revision=1,
                    status="Done",
                    updated_at=now
                )
                session.add(loc)

            inserted_count += 1

        # Cập nhật SystemMetadata version
        meta_res = await session.execute(select(SystemMetadata).where(SystemMetadata.config_key == "poi_data_version"))
        meta = meta_res.scalars().first()
        if meta:
            meta.data_version = inserted_count
            meta.updated_at = now
        else:
            session.add(SystemMetadata(config_key="poi_data_version", data_version=inserted_count, updated_at=now))

        await session.commit()
        logger.info(f"Đã seed thành công {inserted_count} POI thực tế cho Chùa Linh Ứng!")
        return inserted_count

if __name__ == "__main__":
    asyncio.run(seed_real_pois())
