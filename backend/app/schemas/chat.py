from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from uuid import UUID


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[UUID] = None
    
    # Optional design parameters
    linear_meters: Optional[float] = None
    kitchen_shape: Optional[str] = None  # L, U, I, G, parallel
    style: Optional[str] = None  # modern, classic, rustic, minimalist, industrial
    materials: Optional[List[str]] = None
    budget: Optional[str] = None  # low, medium, high, premium


class ArtifactData(BaseModel):
    type: Literal["image", "specs", "cost_estimate", "floor_plan"]
    title: str
    content: Optional[str] = None
    image_data: Optional[str] = None  # base64 encoded
    metadata: dict = {}


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    content: str
    artifacts: List[ArtifactData] = []
    design_version: Optional[int] = None


class StreamChunk(BaseModel):
    type: Literal["text", "artifact_start", "artifact_data", "artifact_end", "done", "error"]
    content: Optional[str] = None
    artifact: Optional[ArtifactData] = None
    conversation_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
