from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class ArtifactCreate(BaseModel):
    artifact_type: str = Field(..., pattern="^(image|specs|cost_estimate|floor_plan)$")
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    metadata: dict = {}


class ArtifactResponse(BaseModel):
    id: UUID
    artifact_type: str
    title: Optional[str]
    content: Optional[str]
    image_url: Optional[str]
    metadata: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    artifacts: List[ArtifactResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: Optional[str] = "Nueva Cocina"


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True


class ConversationList(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: Optional[str] = None
    
    class Config:
        from_attributes = True
