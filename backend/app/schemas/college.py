from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CollegeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)


class CollegeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
