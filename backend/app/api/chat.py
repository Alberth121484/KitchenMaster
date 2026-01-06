import json
import asyncio
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.database import get_db, AsyncSessionLocal
from app.api.deps import get_current_user, get_redis
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, StreamChunk, ArtifactData
from app.schemas.conversation import ConversationCreate
from app.services.conversation import ConversationService
from app.services.auth import AuthService
from app.agent.kitchen_agent import KitchenDesignAgent

router = APIRouter()

# Store agent instances per user session
agent_cache = {}


def get_or_create_agent(user_id: str) -> KitchenDesignAgent:
    """Get or create agent instance for user."""
    if user_id not in agent_cache:
        agent_cache[user_id] = KitchenDesignAgent()
    return agent_cache[user_id]


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Send a message and get a response from the kitchen design agent.
    """
    
    # Get or create conversation
    if request.conversation_id:
        conversation = await ConversationService.get_conversation(
            db,
            request.conversation_id,
            current_user.id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversación no encontrada"
            )
    else:
        conversation = await ConversationService.create_conversation(
            db,
            current_user.id,
            ConversationCreate(title="Nueva Cocina")
        )
    
    # Save user message
    user_message = await ConversationService.add_message(
        db,
        conversation.id,
        "user",
        request.message
    )
    
    # Get agent state from Redis
    state_key = f"agent_state:{current_user.id}:{conversation.id}"
    existing_state = await redis_client.get(state_key)
    existing_state = json.loads(existing_state) if existing_state else None
    
    # Run agent
    agent = get_or_create_agent(str(current_user.id))
    
    try:
        result = await agent.run(
            user_message=request.message,
            user_id=str(current_user.id),
            conversation_id=str(conversation.id),
            existing_state=existing_state
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error del agente: {str(e)}"
        )
    
    # Save agent response
    assistant_message = await ConversationService.add_message(
        db,
        conversation.id,
        "assistant",
        result["response_text"]
    )
    
    # Save artifacts
    artifacts_response = []
    for artifact in result.get("artifacts", []):
        saved_artifact = await ConversationService.add_artifact(
            db,
            assistant_message.id,
            artifact_type=artifact["type"],
            title=artifact.get("title"),
            content=artifact.get("content"),
            image_url=artifact.get("image_url"),
            image_data=artifact.get("image_data", "").encode() if artifact.get("image_data") else None,
            metadata=artifact.get("metadata", {})
        )
        
        artifacts_response.append(ArtifactData(
            type=artifact["type"],
            title=artifact.get("title", ""),
            content=artifact.get("content"),
            image_data=artifact.get("image_data"),
            metadata=artifact.get("metadata", {})
        ))
    
    # Save design iteration if image was generated
    if result.get("state", {}).get("current_image"):
        await ConversationService.save_design_iteration(
            db,
            conversation.id,
            prompt=request.message,
            image_data=result["state"]["current_image"].encode(),
            parameters={
                "linear_meters": result["state"].get("linear_meters"),
                "shape": result["state"].get("shape"),
                "style": result["state"].get("style")
            }
        )
    
    # Save state to Redis
    await redis_client.set(
        state_key,
        json.dumps(result.get("state", {})),
        ex=86400 * 7  # 7 days expiry
    )
    
    # Update conversation title if first design
    if result.get("state", {}).get("design_version") == 1:
        linear_m = result["state"].get("linear_meters", "")
        shape = result["state"].get("shape", "")
        style = result["state"].get("style", "")
        new_title = f"Cocina {style} {shape} - {linear_m}m"
        await ConversationService.update_conversation_title(db, conversation.id, new_title)
    
    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        content=result["response_text"],
        artifacts=artifacts_response,
        design_version=result.get("state", {}).get("design_version")
    )


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: UUID,
    token: str
):
    """
    WebSocket endpoint for streaming chat responses.
    """
    await websocket.accept()
    
    # Validate token
    payload = AuthService.decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    
    async with AsyncSessionLocal() as db:
        user = await AuthService.get_user_by_id(db, UUID(user_id))
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return
        
        # Verify conversation belongs to user
        conversation = await ConversationService.get_conversation(
            db,
            conversation_id,
            user.id
        )
        if not conversation:
            await websocket.close(code=4004, reason="Conversation not found")
            return
        
        agent = get_or_create_agent(str(user.id))
        redis_client = redis.from_url("redis://redis:6379", decode_responses=True)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_json()
                message = data.get("message", "")
                
                if not message:
                    continue
                
                # Send typing indicator
                await websocket.send_json({
                    "type": "status",
                    "content": "thinking"
                })
                
                # Save user message
                user_msg = await ConversationService.add_message(
                    db,
                    conversation_id,
                    "user",
                    message
                )
                
                # Get state
                state_key = f"agent_state:{user.id}:{conversation_id}"
                existing_state = await redis_client.get(state_key)
                existing_state = json.loads(existing_state) if existing_state else None
                
                # Run agent
                try:
                    result = await agent.run(
                        user_message=message,
                        user_id=str(user.id),
                        conversation_id=str(conversation_id),
                        existing_state=existing_state
                    )
                    
                    # Send text response
                    await websocket.send_json({
                        "type": "text",
                        "content": result["response_text"]
                    })
                    
                    # Send artifacts
                    for artifact in result.get("artifacts", []):
                        await websocket.send_json({
                            "type": "artifact",
                            "artifact": {
                                "type": artifact["type"],
                                "title": artifact.get("title", ""),
                                "content": artifact.get("content"),
                                "image_data": artifact.get("image_data"),
                                "metadata": artifact.get("metadata", {})
                            }
                        })
                    
                    # Save to database
                    assistant_msg = await ConversationService.add_message(
                        db,
                        conversation_id,
                        "assistant",
                        result["response_text"]
                    )
                    
                    # Save state
                    await redis_client.set(
                        state_key,
                        json.dumps(result.get("state", {})),
                        ex=86400 * 7
                    )
                    
                    # Send done
                    await websocket.send_json({
                        "type": "done",
                        "message_id": str(assistant_msg.id),
                        "design_version": result.get("state", {}).get("design_version")
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "content": str(e)
                    })
                    
        except WebSocketDisconnect:
            pass
        finally:
            await redis_client.close()


@router.get("/history/{conversation_id}/designs")
async def get_design_history(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all design iterations for a conversation."""
    
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
    
    # Get design iterations
    from sqlalchemy import select
    from app.models.design import DesignIteration
    
    result = await db.execute(
        select(DesignIteration)
        .where(DesignIteration.conversation_id == conversation_id)
        .order_by(DesignIteration.version)
    )
    iterations = result.scalars().all()
    
    return [
        {
            "id": str(it.id),
            "version": it.version,
            "prompt": it.prompt_used,
            "parameters": it.parameters,
            "created_at": it.created_at.isoformat(),
            "has_image": it.image_data is not None or it.image_url is not None
        }
        for it in iterations
    ]
