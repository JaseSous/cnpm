from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class CreatePOIRequest(BaseModel):
    original_language_code: str = Field("vi", min_length=2, max_length=10, description="Mã ngôn ngữ bài thuyết minh gốc")
    original_title: str = Field(..., min_length=2, max_length=255, description="Tiêu đề điểm tham quan")
    original_description: str = Field(..., min_length=10, description="Bài thuyết minh gốc")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Vĩ độ GPS")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Kinh độ GPS")
    trigger_radius: float = Field(30.0, gt=0, description="Bán kính kích hoạt tự động tính bằng mét")
    thumbnail_url: Optional[str] = Field(None, description="Đường dẫn ảnh thu nhỏ")

class UpdatePOIRequest(BaseModel):
    original_language_code: Optional[str] = Field(None, min_length=2, max_length=10)
    original_title: Optional[str] = Field(None, min_length=2, max_length=255)
    original_description: Optional[str] = Field(None, min_length=10)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    trigger_radius: Optional[float] = Field(None, gt=0)
    thumbnail_url: Optional[str] = None

class POILocalizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language_code: str
    translated_title: Optional[str] = None
    translated_description: Optional[str] = None
    audio_url: Optional[str] = None
    status: str
    applied_revision: int

class POIResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    poi_id: int
    original_language_code: str
    original_title: str
    original_description: str
    latitude: float
    longitude: float
    trigger_radius: float
    thumbnail_url: Optional[str] = None
    revision: int
    vector_status: str
    created_at: datetime
    updated_at: datetime
    localizations: List[POILocalizationResponse] = []

class CustomerPOIItem(BaseModel):
    poi_id: int
    title: str
    description: str
    latitude: float
    longitude: float
    trigger_radius: float
    thumbnail_url: Optional[str] = None
    audio_url: Optional[str] = None
    language_code: str
    fallback: bool = False

class CustomerPOIListResponse(BaseModel):
    pois: List[CustomerPOIItem]
    data_version: int

class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language_code: str
    language_name: str
    native_name: str
    is_fallback: bool
    tts_supported: bool
    is_active: bool

class RetryPipelineRequest(BaseModel):
    language_codes: Optional[List[str]] = Field(default_factory=list, description="Danh sách mã ngôn ngữ cần retry")
    retry_vector: bool = Field(False, description="Có kích hoạt retry đồng bộ Vector DB không")
