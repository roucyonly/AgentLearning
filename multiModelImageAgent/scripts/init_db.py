#!/usr/bin/env python
"""Initialize database"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def init_db():
    """Initialize database"""
    from app.db.session import engine
    from app.models.base import Base

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("[OK] Database tables created successfully")


async def main():
    print("Starting database initialization...")
    await init_db()
    print("[DONE] Initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
