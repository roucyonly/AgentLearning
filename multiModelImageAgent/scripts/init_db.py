#!/usr/bin/env python
"""初始化数据库"""
import asyncio
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def init_db():
    """初始化数据库"""
    from app.db.session import engine
    from app.models.base import Base

    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库表创建成功")


async def main():
    print("🚀 开始初始化数据库...")
    await init_db()
    print("✅ 初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
