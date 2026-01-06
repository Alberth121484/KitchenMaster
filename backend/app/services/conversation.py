from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message, Artifact
from app.models.design import DesignIteration
from app.schemas.conversation import ConversationCreate, MessageCreate, ArtifactCreate


class ConversationService:
    @staticmethod
    async def create_conversation(
        db: AsyncSession, 
        user_id: UUID, 
        data: ConversationCreate
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=data.title or "Nueva Cocina"
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation
    
    @staticmethod
    async def get_conversation(
        db: AsyncSession, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> Optional[Conversation]:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages).selectinload(Message.artifacts))
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_conversations(
        db: AsyncSession, 
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: UUID,
        role: str,
        content: str
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        
        # Update conversation timestamp
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one()
        conversation.updated_at = func.now()
        
        await db.commit()
        await db.refresh(message)
        return message
    
    @staticmethod
    async def add_artifact(
        db: AsyncSession,
        message_id: UUID,
        artifact_type: str,
        title: str = None,
        content: str = None,
        image_url: str = None,
        image_data: bytes = None,
        metadata: dict = None
    ) -> Artifact:
        artifact = Artifact(
            message_id=message_id,
            artifact_type=artifact_type,
            title=title,
            content=content,
            image_url=image_url,
            image_data=image_data,
            metadata=metadata or {}
        )
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)
        return artifact
    
    @staticmethod
    async def save_design_iteration(
        db: AsyncSession,
        conversation_id: UUID,
        prompt: str,
        image_data: bytes = None,
        image_url: str = None,
        parameters: dict = None,
        parent_id: UUID = None
    ) -> DesignIteration:
        # Get current version number
        result = await db.execute(
            select(func.max(DesignIteration.version))
            .where(DesignIteration.conversation_id == conversation_id)
        )
        max_version = result.scalar() or 0
        
        iteration = DesignIteration(
            conversation_id=conversation_id,
            parent_iteration_id=parent_id,
            prompt_used=prompt,
            image_data=image_data,
            image_url=image_url,
            parameters=parameters or {},
            version=max_version + 1
        )
        db.add(iteration)
        await db.commit()
        await db.refresh(iteration)
        return iteration
    
    @staticmethod
    async def get_latest_design(
        db: AsyncSession,
        conversation_id: UUID
    ) -> Optional[DesignIteration]:
        result = await db.execute(
            select(DesignIteration)
            .where(DesignIteration.conversation_id == conversation_id)
            .order_by(desc(DesignIteration.version))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_conversation_title(
        db: AsyncSession,
        conversation_id: UUID,
        title: str
    ) -> Conversation:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one()
        conversation.title = title
        await db.commit()
        await db.refresh(conversation)
        return conversation
    
    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID
    ) -> bool:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            await db.delete(conversation)
            await db.commit()
            return True
        return False
