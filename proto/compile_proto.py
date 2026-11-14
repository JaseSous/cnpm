"""
Script biên dịch các định nghĩa protobuf (.proto) thành mã nguồn Python stubs cho các services.
Yêu cầu: pip install grpcio-tools protobuf
Cách dùng: python proto/compile_proto.py
"""

import sys
import subprocess
from pathlib import Path

def compile_protos():
    root_dir = Path(__file__).resolve().parent.parent
    proto_dir = root_dir / "proto"
    
    proto_files = [
        proto_dir / "poi_service.proto",
        proto_dir / "chatbot_service.proto",
    ]
    
    target_dirs = [
        root_dir / "backend" / "poi-service" / "app" / "grpc_server",
        root_dir / "backend" / "chatbot-service" / "app" / "grpc_server",
        root_dir / "backend" / "data-pipeline-service" / "app" / "grpc_clients",
    ]
    
    for target in target_dirs:
        target.mkdir(parents=True, exist_ok=True)
        init_file = target / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# gRPC stubs package\n", encoding="utf-8")
        
        for proto_file in proto_files:
            cmd = [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"-I{proto_dir}",
                f"--python_out={target}",
                f"--grpc_python_out={target}",
                str(proto_file),
            ]
            print(f"Compiling {proto_file.name} -> {target.relative_to(root_dir)}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Lỗi khi biên dịch {proto_file.name}:", result.stderr)
            else:
                print(f"Thành công: {proto_file.name} -> {target.relative_to(root_dir)}")

if __name__ == "__main__":
    compile_protos()
