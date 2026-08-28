import asyncio
from app.database import engine, Base, async_session_factory
from app.main import seed_defaults
from app.models import SecurityEvent, Threat, AuditLedger, DetectionRule, SystemSetting

async def test_startup():
    print("Testing table creation and seeding...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")
    await seed_defaults()
    print("Default rules and settings seeded successfully!")
    await engine.dispose()
    print("Backend test completed perfectly!")

if __name__ == "__main__":
    asyncio.run(test_startup())
