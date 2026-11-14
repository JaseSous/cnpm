# Protobuf & gRPC Definitions (`proto/`)

Thư mục này chứa các tệp định nghĩa Protobuf (`.proto`) chuẩn hóa giao tiếp nội bộ giữa các microservices:
- `poi_service.proto`: Giao diện gRPC của POI Service (cập nhật kết quả dịch thuật, audio, cảnh báo pipeline, kiểm tra tính duy nhất idempotency).
- `chatbot_service.proto`: Giao diện gRPC của Chatbot AI Service (đồng bộ/xóa vector chunks vào Qdrant, xóa cache FAQ).

## Biên dịch Stubs sang Python

Cài đặt công cụ biên dịch:
```powershell
pip install grpcio-tools protobuf
```

Chạy script tự động biên dịch vào các services:
```powershell
python proto/compile_proto.py
```
Mã nguồn sinh ra (`*_pb2.py`, `*_pb2_grpc.py`) đã được thêm vào `.gitignore` để không lưu rác vào git repository.
