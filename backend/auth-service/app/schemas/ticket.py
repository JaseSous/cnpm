from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class CreateTicketRequest(BaseModel):
    package_id: Optional[int] = Field(None, description="Mã gói vé đã chọn")
    amount: float = Field(..., gt=0, description="Số tiền thanh toán thực thu (VNĐ)")
    payment_method: str = Field("cash", description="Phương thức thanh toán: mặc định 'cash'")

class TicketResponse(BaseModel):
    shorted_code: str = Field(..., description="Mã vé 10 ký tự ngẫu nhiên")
    session_id: str = Field(..., description="UUID phiên thanh toán")
    amount: float
    package_id: Optional[int] = None
    expires_in: int = Field(..., description="Thời gian sống của mã vé tính bằng giây")
    created_at: datetime

class TicketPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    package_id: int
    package_name: str
    price: float
    description: Optional[str] = None
    is_active: bool
