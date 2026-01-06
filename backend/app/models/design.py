from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from app.database import Base


class DesignIteration(Base):
    __tablename__ = "design_iterations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    parent_iteration_id = Column(UUID(as_uuid=True), ForeignKey("design_iterations.id"), nullable=True)
    prompt_used = Column(Text, nullable=False)
    image_data = Column(LargeBinary)
    image_url = Column(Text)
    parameters = Column(JSONB, default={})
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="design_iterations")
    parent = relationship("DesignIteration", remote_side=[id], backref="children")


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    preferred_styles = Column(JSONB, default=[])
    preferred_materials = Column(JSONB, default=[])
    budget_range = Column(JSONB, default={})
    notes = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class MemoryEmbedding(Base):
    __tablename__ = "memory_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))
    memory_type = Column(String(50), default="preference")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="memory_embeddings")
