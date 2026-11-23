from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShipmentCreate(BaseModel):
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tracking_code: str
    origin: str
    destination: str
    status: str
    created_at: datetime
    updated_at: datetime


class ShipmentStatusUpdate(BaseModel):
    status: str = Field(min_length=1)


