from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResultPublicationCreate(BaseModel):
    class_id: int = Field(gt=0)
    academic_session_id: int = Field(gt=0)
    term_id: int = Field(gt=0)


class ResultPublicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_id: int
    academic_session_id: int
    term_id: int
    status: str
    published_by_user_id: int
    published_at: datetime
    updated_at: datetime
