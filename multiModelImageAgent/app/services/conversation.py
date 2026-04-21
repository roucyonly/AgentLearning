from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, ConversationMessage
from app.repositories.conversation import ConversationRepository, ConversationMessageRepository


class ConversationService:
    """对话服务"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = ConversationMessageRepository(session)

    async def create_conversation(
        self,
        user_id: str,
        context: Dict[str, Any] = None
    ) -> Conversation:
        """创建对话"""
        conversation = await self.conversation_repo.create({
            "user_id": user_id,
            "context": context or {}
        })
        return conversation

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str = None
    ) -> Optional[Conversation]:
        """获取对话"""
        if user_id:
            return await self.conversation_repo.get_by_user_and_id(user_id, conversation_id)
        return await self.conversation_repo.get(conversation_id)

    async def get_conversation_with_messages(
        self,
        conversation_id: str
    ) -> Optional[Conversation]:
        """获取对话及其消息"""
        return await self.conversation_repo.get_with_messages(conversation_id)

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        task_ids: List[str] = None
    ) -> ConversationMessage:
        """添加消息"""
        message = await self.message_repo.create({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "task_ids": task_ids or []
        })

        # 更新对话的 updated_at（通过更新 conversation）
        conversation = await self.conversation_repo.get(conversation_id)
        if conversation:
            await self.conversation_repo.update(conversation_id, {"context": conversation.context})

        return message

    async def get_history(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConversationMessage]:
        """获取对话历史"""
        return await self.message_repo.get_by_conversation(conversation_id, skip, limit)

    async def get_latest_messages(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[ConversationMessage]:
        """获取最新消息"""
        return await self.message_repo.get_latest_messages(conversation_id, limit)

    async def get_or_create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Conversation:
        """获取或创建对话"""
        if conversation_id:
            conversation = await self.get_conversation(conversation_id, user_id)
            if conversation:
                return conversation

        return await self.create_conversation(user_id)

    async def list_user_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        """列出用户的所有对话"""
        return await self.conversation_repo.get_user_conversations(user_id, skip, limit)

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str = None
    ) -> bool:
        """删除对话"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False

        return await self.conversation_repo.delete(conversation_id)
