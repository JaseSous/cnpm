from app.grpc_clients.poi_service_client import poi_grpc_client, POIServiceClient
from app.grpc_clients.chatbot_service_client import chatbot_grpc_client, ChatbotServiceClient

__all__ = [
    "poi_grpc_client",
    "POIServiceClient",
    "chatbot_grpc_client",
    "ChatbotServiceClient"
]
