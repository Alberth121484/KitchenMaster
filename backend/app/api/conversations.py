from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate, 
    ConversationResponse, 
    ConversationList
)
from app.services.conversation import ConversationService

router = APIRouter()


@router.get("", response_model=List[ConversationList])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all conversations for current user."""
    
    conversations = await ConversationService.get_user_conversations(
        db, 
        current_user.id,
        limit=limit,
        offset=offset
    )
    
    result = []
    for conv in conversations:
        last_msg = conv.messages[-1].content if conv.messages else None
        result.append(ConversationList(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages) if hasattr(conv, 'messages') else 0,
            last_message=last_msg[:100] if last_msg else None
        ))
    
    return result


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation."""
    
    if data is None:
        data = ConversationCreate()
    
    conversation = await ConversationService.create_conversation(
        db,
        current_user.id,
        data
    )
    
    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation with all messages."""
    
    conversation = await ConversationService.get_conversation(
        db,
        conversation_id,
        current_user.id
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada"
        )
    
    return conversation


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: UUID,
    title: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update conversation title."""
    
    conversation = await ConversationService.get_conversation(
        db,
        conversation_id,
        current_user.id
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada"
        )
    
    updated = await ConversationService.update_conversation_title(
        db,
        conversation_id,
        title
    )
    
    return {"id": str(updated.id), "title": updated.title}


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation."""
    
    deleted = await ConversationService.delete_conversation(
        db,
        conversation_id,
        current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada"
        )
    
    return None
