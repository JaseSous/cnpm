import logging
from typing import List, Dict, Any
from app.services.gemini_service import gemini_service
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger("chatbot-knowledge")

# Kho tri thức tổng hợp về Chùa Linh Ứng (Bãi Bụt, Sơn Trà, TP. Đà Nẵng)
GENERAL_KNOWLEDGE_DATA: List[Dict[str, Any]] = [
    {
        "chunk_id": "gk_hours_tickets_vi",
        "lang": "vi",
        "title": "Giờ mở cửa và Giá vé tham quan Chùa Linh Ứng Bãi Bụt",
        "text": (
            "Thời gian mở cửa và vé tham quan Chùa Linh Ứng Bãi Bụt:\n"
            "- Giờ mở cửa: Chùa mở cửa đón du khách và phật tử từ 6h00 sáng đến 21h00 tối hàng ngày, "
            "tất cả các ngày trong tuần, kể cả ngày thứ Bảy, Chủ Nhật và các dịp lễ, Tết.\n"
            "- Giá vé: Hoàn toàn MIỄN PHÍ vé vào cổng tham quan và chiêm bái. Nhà chùa không thu bất kỳ khoản phí vé nào.\n"
            "- Du khách có thể tự do vãng cảnh, lễ Phật, chiêm bái tượng Phật Bà Quan Âm 67m và ngắm cảnh biển Đà Nẵng."
        )
    },
    {
        "chunk_id": "gk_hours_tickets_en",
        "lang": "en",
        "title": "Opening Hours and Ticket Admission - Linh Ung Pagoda",
        "text": (
            "Opening hours and admission for Linh Ung Pagoda Bai But:\n"
            "- Opening Hours: Open daily from 6:00 AM to 9:00 PM, 7 days a week, including weekends and public holidays.\n"
            "- Admission Fee: COMPLETELY FREE of charge. The pagoda does not charge any entrance fee.\n"
            "- Visitors are welcome to sightsee, worship, admire the 67m Lady Buddha Statue, and enjoy panoramic sea views."
        )
    },
    {
        "chunk_id": "gk_dresscode_etiquette_vi",
        "lang": "vi",
        "title": "Quy định trang phục và Ứng xử khi vào Chùa Linh Ứng",
        "text": (
            "Quy định trang phục và nếp sống trang nghiêm tại Chùa Linh Ứng Bãi Bụt:\n"
            "1. Trang phục: Ăn mặc lịch sự, trang nghiêm, kín đáo. Tuyệt đối không mặc váy ngắn, quần đùi trên gối, "
            "áo hai dây, áo sát nách hay áo hở lưng khi bước vào Chánh Điện và các điện thờ.\n"
            "2. Giày dép và mũ nón: Vui lòng tháo giày dép, nón, mũ, kính râm và để gọn gàng bên ngoài trước khi bước vào Chánh Điện.\n"
            "3. Ứng xử chốn thiền môn: Đi nhẹ, nói khẽ, giữ gìn trật tự thanh tịnh; không cười đùa to tiếng, không văng tục chửi bậy.\n"
            "4. Vệ sinh & An toàn: Không hút thuốc lá trong khuôn viên chùa; bỏ rác đúng nơi quy định; không sờ tay vào các pho tượng hay hiện vật thờ cúng.\n"
            "5. Thắp nhang: Mỗi người chỉ nên thắp 1 nén nhang tại các lư hương lớn đặt ngoài trời để tránh ngột ngạt và nguy cơ hỏa hoạn."
        )
    },
    {
        "chunk_id": "gk_dresscode_etiquette_en",
        "lang": "en",
        "title": "Dress Code and Temple Etiquette - Linh Ung Pagoda",
        "text": (
            "Dress code and visitor guidelines at Linh Ung Pagoda Bai But:\n"
            "1. Dress Code: Wear modest, respectful clothing covering shoulders and knees. Shorts, short skirts, sleeveless shirts, "
            "and tank tops are strictly prohibited inside the Main Sanctuary and prayer halls.\n"
            "2. Footwear & Hats: Remove shoes, hats, and sunglasses before entering temple halls.\n"
            "3. Behavior: Maintain peace and silence; speak softly; avoid loud laughter or disruptive behavior.\n"
            "4. Cleanliness: No smoking anywhere on pagoda grounds; place trash in designated bins; do not touch sacred statues.\n"
            "5. Incense: Please light only 1 incense stick at outdoor main urns to prevent smoke buildup and fire hazards."
        )
    },
    {
        "chunk_id": "gk_history_origins_vi",
        "lang": "vi",
        "title": "Lịch sử hình thành và Xây dựng Chùa Linh Ứng Bãi Bụt",
        "text": (
            "Lịch sử khởi dựng Chùa Linh Ứng Bãi Bụt (Bán đảo Sơn Trà, TP. Đà Nẵng):\n"
            "- Khởi công: Ngày 19 tháng 6 năm 2004 (âm lịch).\n"
            "- Khánh thành: Ngày 30 tháng 7 năm 2010 sau 6 năm miệt mài thi công.\n"
            "- Trụ trì khai sơn: Cố Đại lão Hòa thượng Thích Thiện Nguyện - người đã phát tâm nguyện lớn lao đặt viên đá đầu tiên "
            "kiến tạo ngôi đại tự này, cùng sự trợ duyên của chính quyền thành phố Đà Nẵng và đông đảo phật tử trong và ngoài nước.\n"
            "- Vị trí và Quy mô: Tọa lạc trên diện tích rộng 20 héc-ta trên sườn núi bán đảo Sơn Trà, ở độ cao 693m so với mực nước biển. "
            "Đây là ngôi chùa lớn nhất và có kiến trúc bề thế nhất tại thành phố Đà Nẵng."
        )
    },
    {
        "chunk_id": "gk_history_origins_en",
        "lang": "en",
        "title": "History and Foundation of Linh Ung Pagoda Bai But",
        "text": (
            "History and origins of Linh Ung Pagoda Bai But on Son Tra Peninsula:\n"
            "- Groundbreaking: June 19, 2004 (Lunar calendar).\n"
            "- Inauguration: July 30, 2010, after 6 years of meticulous construction.\n"
            "- Founding Abbot: The late Most Venerable Thich Thien Nguyen, who initiated the construction with support "
            "from Da Nang authorities and Buddhist donors worldwide.\n"
            "- Location & Scale: Situated on a 20-hectare site on the slope of Son Tra Mountain, 693 meters above sea level. "
            "It is the largest and most magnificent Buddhist pagoda in Da Nang City."
        )
    },
    {
        "chunk_id": "gk_legend_baibut_vi",
        "lang": "vi",
        "title": "Sự tích tên gọi Bãi Bụt - Cõi Phật giữa nhân gian",
        "text": (
            "Sự tích tên gọi Bãi Bụt gắn liền với Chùa Linh Ứng Sơn Trà:\n"
            "- Nguồn gốc: Vào thời vua Minh Mạng triều Nguyễn (thế kỷ 19), dân chài lưới ven biển bán đảo Sơn Trà phát hiện một pho tượng Phật "
            "bằng gỗ trôi dạt vào bờ cát một buổi sớm mai.\n"
            "- Ý nghĩa: Ngư dân cho là điềm lành linh thiêng, đồng lòng rước tượng lên bãi cát lập am thờ tự khói nhang sớm tối.\n"
            "- Từ đó, sóng yên biển lặng, bão tố tan biến, các chuyến ra khơi của ngư dân đều thuận buồm xuôi gió, bội thu tôm cá.\n"
            "- Tên gọi 'Bãi Bụt': 'Bụt' là từ cổ trong tiếng Việt chỉ Đức Phật. Bãi Bụt nghĩa là 'Bãi đất có Phật ngự trị', "
            "cõi Phật bình an giữa chốn nhân gian."
        )
    },
    {
        "chunk_id": "gk_legend_baibut_en",
        "lang": "en",
        "title": "The Legend of Bai But - Realm of the Buddha",
        "text": (
            "The legend behind the name 'Bai But' at Linh Ung Pagoda:\n"
            "- Origins: During the reign of King Minh Mang (19th century, Nguyen Dynasty), local fishermen on Son Tra Peninsula discovered "
            "a Buddha statue drifting onto the sandy shore.\n"
            "- The Miracle: Believing it to be a divine blessing, the villagers enshrined the statue in a small sanctuary. "
            "From that day onward, violent sea storms subsided, ocean waves calmed, and fishermen returned safely with bountiful catches.\n"
            "- Meaning of 'Bai But': 'But' is an ancient Vietnamese word for Buddha. Bai But translates to 'The Beach of the Buddha', "
            "representing a peaceful sanctuary of the Buddha among mortals."
        )
    },
    {
        "chunk_id": "gk_three_pagodas_vi",
        "lang": "vi",
        "title": "Tam giác tâm linh - Ba ngôi Chùa Linh Ứng tại Đà Nẵng",
        "text": (
            "Bộ ba ngôi chùa cùng mang tên Linh Ứng tạo thành tam giác tâm linh bảo hộ thành phố Đà Nẵng:\n"
            "1. Chùa Linh Ứng Non Nước (Ngũ Hành Sơn): Ngôi chùa cổ kính nhất, xây dựng từ thế kỷ 19 thời vua Gia Long và Minh Mạng trên ngọn Thủy Sơn.\n"
            "2. Chùa Linh Ứng Bà Nà (Bà Nà Hills): Tọa lạc trên đỉnh núi Chúa ở độ cao 1.500m, nổi tiếng với bức tượng Đức Phật Thích Ca ngồi thiền cao 27m giữa biển mây.\n"
            "3. Chùa Linh Ứng Bãi Bụt (Sơn Trà): Ngôi chùa lớn nhất, tựa lưng vào núi Sơn Trà, hướng nhìn ra biển Đông, sở hữu tượng Phật Bà Quan Âm cao 67m."
        )
    },
    {
        "chunk_id": "gk_amenities_food_water_vi",
        "lang": "vi",
        "title": "Ẩm thực chay, Nước uống và Tiện ích phục vụ du khách",
        "text": (
            "Tiện ích và dịch vụ phục vụ du khách tại Chùa Linh Ứng Bãi Bụt:\n"
            "- Nước uống miễn phí: Chùa có các bình nước lọc mát miễn phí đặt tại khu vực nhà Tăng và lối đi sân chùa.\n"
            "- Cơm chay: Vào ngày Rằm (15 âm lịch), mồng Một (1 âm lịch) và các ngày đại lễ Phật đản, Vu Lan, nhà chùa có phục vụ cơm chay thanh đạm "
            "miễn phí cho khách thập phương (du khách có thể tùy tâm cúng dường công đức).\n"
            "- Nhà vệ sinh công cộng: Khu vệ sinh sạch sẽ nằm phía sau bãi đỗ xe và gần khu vực nhà Tăng.\n"
            "- Quầy phát hành văn hóa phẩm: Nơi thỉnh chuỗi hạt bồ đề, tranh tượng Phật và sách báo Phật học."
        )
    },
    {
        "chunk_id": "gk_transport_parking_vi",
        "lang": "vi",
        "title": "Đường đi, Phương tiện di chuyển và Bãi gửi xe Chùa Linh Ứng",
        "text": (
            "Hướng dẫn di chuyển và bãi giữ xe Chùa Linh Ứng Bãi Bụt:\n"
            "- Vị trí: Đường Hoàng Sa, Bán đảo Sơn Trà, phường Thọ Quang, quận Sơn Trà, TP. Đà Nẵng (cách trung tâm khoảng 10km về phía Đông Bắc).\n"
            "- Đường đi: Tuyến đường ven biển Võ Nguyên Giáp - Hoàng Sa dọc bờ biển Mỹ Khê nối dài lên chân núi Sơn Trà rất đẹp và thông thoáng.\n"
            "- Phương tiện: Có thể đi bằng xe máy (ngắm cảnh biển đẹp nhất), taxi, ôtô cá nhân hoặc xe tour du lịch.\n"
            "- Bãi đỗ xe: Chùa có bãi đỗ xe máy và bãi đậu xe ôtô rộng rãi ngay trước cổng Tam Quan, có bảo vệ hướng dẫn đỗ xe an toàn."
        )
    },
    {
        "chunk_id": "gk_statue_details_vi",
        "lang": "vi",
        "title": "Kiến trúc và Ý nghĩa Tượng Phật Bà Quan Âm 67m Bãi Bụt",
        "text": (
            "Chi tiết về Tượng Bồ Tát Quán Thế Âm cao 67m tại Chùa Linh Ứng Bãi Bụt:\n"
            "- Chiều cao: 67 mét, đường kính tòa sen rộng 35 mét, tương đương tòa nhà cao 30 tầng (tượng Phật Bà cao nhất Việt Nam).\n"
            "- Cấu trúc bên trong: Trong lòng tượng có 17 tầng, mỗi tầng đều có bàn thờ thờ tổng cộng 21 bức tượng Phật với tư thế diện mạo khác nhau gọi là 'Phật trung hữu Phật'.\n"
            "- Dáng tượng: Tựa lưng vào núi Sơn Trà nguyên sinh, đôi mắt từ bi hướng nhìn ra biển Đông; tay bắt ấn tam muội, tay cầm bình nước cam lộ "
            "rưới bình an cho nhân gian và che chở ngư dân miền Trung vượt qua sóng gió bão tố."
        )
    }
]

async def sync_knowledge_base_to_qdrant() -> int:
    """
    Tự động nhúng (embedding) và đồng bộ toàn bộ kho tri thức cẩm nang chung vào Qdrant Vector DB (poi_id=0).
    Giúp Chatbot AI trả lời chuẩn xác các câu hỏi về giờ mở cửa, giá vé, trang phục, lịch sử, ẩm thực chay...
    """
    logger.info("Bắt đầu đồng bộ kho tri thức cẩm nang Chùa Linh Ứng vào Qdrant...")
    qdrant_service.ensure_collection_exists()

    by_lang: Dict[str, List[Dict[str, Any]]] = {}

    for item in GENERAL_KNOWLEDGE_DATA:
        lang = item["lang"]
        if lang not in by_lang:
            by_lang[lang] = []

        chunk_id = item["chunk_id"]
        title = item["title"]
        text = item["text"]

        embedding = await gemini_service.get_embedding(text)

        chunk_dict = {
            "chunk_id": chunk_id,
            "chunk_text": text,
            "embedding": embedding,
            "metadata": {
                "poi_id": "0",
                "language_code": lang,
                "revision": "1",
                "title": title,
                "category": "general_knowledge"
            }
        }
        by_lang[lang].append(chunk_dict)

    total_upserted = 0
    for lang, chunks in by_lang.items():
        count = qdrant_service.upsert_poi_vectors(
            poi_id=0,
            revision=1,
            language_code=lang,
            chunks=chunks
        )
        total_upserted += count

    logger.info(f"Hoàn thành đồng bộ {total_upserted} đoạn tri thức cẩm nang vào Qdrant!")
    return total_upserted

