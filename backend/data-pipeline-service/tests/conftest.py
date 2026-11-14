import os
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

# Đảm bảo đường dẫn import tới app của data-pipeline-service
current_dir = Path(__file__).resolve().parent
service_root = current_dir.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

import app.grpc_clients.poi_service_client
import app.grpc_clients.chatbot_service_client
import app.consumers.guard
import app.consumers.poi_deleted
import app.consumers.poi_upserted
import app.services.embedding_service

@pytest.fixture
def mock_poi_grpc(monkeypatch):
    """Mock POI Service gRPC Client"""
    mock = MagicMock()
    mock.check_processed_event = AsyncMock(return_value=False)
    mock.mark_event_processed = AsyncMock(return_value=True)
    mock.update_localization_status = AsyncMock(return_value=True)
    mock.update_vector_status = AsyncMock(return_value=True)
    mock.create_pipeline_alert = AsyncMock(return_value=1)
    
    monkeypatch.setattr(sys.modules["app.grpc_clients.poi_service_client"], "poi_grpc_client", mock)
    monkeypatch.setattr(sys.modules["app.consumers.guard"], "poi_grpc_client", mock)
    monkeypatch.setattr(sys.modules["app.consumers.poi_deleted"], "poi_grpc_client", mock)
    monkeypatch.setattr(sys.modules["app.consumers.poi_upserted"], "poi_grpc_client", mock)
    monkeypatch.setattr(sys.modules["app.services.embedding_service"], "poi_grpc_client", mock)
    
    return mock

@pytest.fixture
def mock_chatbot_grpc(monkeypatch):
    """Mock Chatbot Service gRPC Client"""
    mock = MagicMock()
    mock.upsert_vectors = AsyncMock(return_value=True)
    mock.delete_vectors = AsyncMock(return_value=True)
    mock.invalidate_faq_cache = AsyncMock(return_value=True)
    
    monkeypatch.setattr(sys.modules["app.grpc_clients.chatbot_service_client"], "chatbot_grpc_client", mock)
    monkeypatch.setattr(sys.modules["app.consumers.poi_deleted"], "chatbot_grpc_client", mock)
    monkeypatch.setattr(sys.modules["app.consumers.poi_upserted"], "chatbot_grpc_client", mock)
    monkeypatch.setattr(sys.modules["app.services.embedding_service"], "chatbot_grpc_client", mock)
    
    return mock
