from fastapi import APIRouter
from app.api import auth, chat, conversations

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
