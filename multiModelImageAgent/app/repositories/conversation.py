from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.conversation import Conversation, ConversationMessage


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def get_user_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Conversation.updated_at.desc())
        )
        return result.scalars().all()

    async def get_with_messages(self, conversation_id: str) -> Optional[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_id(
        self,
        user_id: str,
        conversation_id: str
    ) -> Optional[Conversation]:
        """获取用户特定的对话"""
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()


class ConversationMessageRepository(BaseRepository[ConversationMessage]):
    def __init__(self, session: AsyncSession):
        super().__init__(ConversationMessage, session)

    async def get_by_conversation(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConversationMessage]:
        result = await self.session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .offset(skip)
            .limit(limit)
            .order_by(ConversationMessage.created_at)
        )
        return result.scalars().all()

    async def get_latest_messages(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[ConversationMessage]:
        """获取最新的消息"""
        result = await self.session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        # 反转以按时间顺序返回
        messages = result.scalars().all()
        return list(reversed(messages))

    async def count_by_conversation(self, conversation_id: str) -> int:
        """统计对话中的消息数量"""
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(ConversationMessage.id)).where(
                ConversationMessage.conversation_id == conversation_id
            )
        )
        return result.scalar() or 0
