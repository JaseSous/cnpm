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

REAL_LOCALIZATIONS_POI_1 = {
    "en": {
        "title": "Lady Buddha Statue of Bai But",
        "description": "The statue of Bodhisattva Avalokiteshvara at Linh Ung Bai But Pagoda has a height of 67 meters and a lotus pedestal diameter of 35 meters, equivalent to a 30-story building. The statue stands with its back against the Son Tra mountain peak, facing the vast East Sea, one hand making the samadhi seal and the other holding a vase of nectar as if sprinkling peace upon the fishermen of the Da Nang sea."
    },
    "zh": {
        "title": "拜佛观音佛像",
        "description": "灵应寺的观世音菩萨像高67米，莲花座直径35米，相当于30层楼高。佛像背靠山茶山顶，面朝辽阔的东海，一手结三昧印，一手持甘露瓶，宛如为岘港海域的渔民播撒安宁。"
    },
    "ja": {
        "title": "バイブットの観音菩薩像",
        "description": "リンウン・バイブット寺の観世音菩薩像は、高さ67メートル、蓮華座の直径35メートルを誇り、30階建てのビルに相当します。ソンチャ山の頂を背にし、広大な東シナ海を望み、片手で三昧の印を結び、もう一方の手で甘露の壺を持ち、ダナンの海の漁民たちに安らぎを降り注ぐかのように佇んでいます。"
    },
    "ko": {
        "title": "바이붓 관음보살상",
        "description": "린응 바이붓 사원의 관세음보살상은 높이 67m, 연화대 지름 35m로 30층 건물 높이에 달합니다. 손짜 산 정상에 등을 대고 광활한 동해를 바라보며, 한 손에는 삼매인을 맺고 다른 한 손에는 감로수 병을 들고 있어 다낭 해역의 어민들에게 평안을 뿌려주는 듯합니다."
    },
    "fr": {
        "title": "Statue de la Bodhisattva Avalokiteshvara de Bai But",
        "description": "La statue du Bodhisattva Avalokiteshvara à la pagode Linh Ung Bai But mesure 67 mètres de haut avec un socle de lotus de 35 mètres de diamètre, équivalent à un édifice de 30 étages. Adossée au mont Son Tra et faisant face à la mer Orientale, elle tient un vase de nectar bénissant les marins de Da Nang."
    },
    "de": {
        "title": "Guanyin-Statue in Bai But",
        "description": "Die Statue des Bodhisattva Avalokiteshvara in der Linh-Ung-Bai-But-Pagode ist 67 Meter hoch mit einem Lotossockel von 35 Metern Durchmesser. Sie blickt auf das Ostmeer und segnet die Fischer von Da Nang."
    },
    "es": {
        "title": "Estatua de la Bodhisattva Guanyin de Bai But",
        "description": "La estatua de la Bodhisattva Avalokiteshvara en la Pagoda Linh Ung Bai But tiene una altura de 67 metros y una base de loto de 35 metros de diámetro, equivalente a un edificio de 30 pisos."
    },
    "th": {
        "title": "รูปปั้นพระโพธิสัตว์กวนอิมแห่งลานบุต (Bai But)",
        "description": "รูปปั้นพระโพธิสัตว์กวนอิม ณ วัดลิงอึ้ง ลานบุต มีความสูง 67 เมตร เส้นผ่านศูนย์กลางฐานบัว 35 เมตร เทียบเท่าอาคาร 30 ชั้น ยืนพิงยอดเขาเซินตร่า หันหน้าออกสู่ทะเลตะวันออกอันกว้างใหญ่"
    },
    "ru": {
        "title": "Статуя Бодхисаттвы Куаньинь в Байбут",
        "description": "Статуя Бодхисаттвы Авалокитешвары в пагоде Линь Ынг Байбут имеет высоту 67 метров и диаметр лотосового пьедестала 35 метров, что эквивалентно 30-этажному зданию."
    },
    "pt": {
        "title": "Estátua da Bodhisattva Guanyin de Bai But",
        "description": "A estátua do Bodhisattva Avalokiteshvara no Pagode Linh Ung Bai But tem 67 metros de altura e uma base de lótus com 35 metros de diâmetro, abençoando as águas de Da Nang."
    },
    "it": {
        "title": "Statua della Bodhisattva Guanyin di Bai But",
        "description": "La statua del Bodhisattva Avalokiteshvara presso la pagoda Linh Ung Bai But ha un'altezza di 67 metri e un diametro del piedistallo di loto di 35 metri."
    },
    "id": {
        "title": "Patung Bodhisattva Avalokiteshvara Bai But",
        "description": "Patung Bodhisattva Avalokiteshvara di Pagoda Linh Ung Bai But memiliki ketinggian 67 meter dan diameter teratai 35 meter, setara dengan gedung 30 lantai."
    },
    "ar": {
        "title": "تمثال البوذيساتفا غوانين في باي بوت",
        "description": "يبلغ ارتفاع تمثال البوذيساتفا أفالوكيتشفارا في معبد لين أونغ باي بوت 67 متراً ويبلغ قطر قاعدة اللوتس 35 متراً، وهو ما يعادل مبنى مكوناً من 30 طابقاً."
    },
    "hi": {
        "title": "बाई बुत की बोधिसत्व अवलोकितेश्वर (गुआनयिन) मूर्ति",
        "description": "लिन्ह उंग बाई बुत पगोडा में बोधिसत्व अवलोकितेश्वर की मूर्ति 67 मीटर ऊंची है और इसके कमल के आसन का व्यास 35 मीटर है, जो 30 मंजिला इमारत के बराबर है।"
    }
}

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
                
                # Nếu là POI #1, lấy bản dịch Phật giáo chuẩn xác
                real_loc = REAL_LOCALIZATIONS_POI_1.get(lang.language_code) if poi.poi_id == 1 else None
                t_title = real_loc["title"] if real_loc else f"[{lang.language_code.upper()}] {poi_data['title']}"
                t_desc = real_loc["description"] if real_loc else f"[{lang.language_code.upper()}] {poi_data['description']}"
                
                loc = POILocalization(
                    poi_id=poi.poi_id,
                    language_code=lang.language_code,
                    translated_title=t_title,
                    translated_description=t_desc,
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
