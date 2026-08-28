import asyncio
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models import SecurityEvent, Threat, AuditLedger, DetectionRule, SystemSetting
from app.main import seed_defaults

async def main():
    print("Connecting to PostgreSQL and creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully:")
    print(" - security_events")
    print(" - threats")
    print(" - audit_ledger")
    print(" - detection_rules")
    print(" - system_settings")
    
    print("\nSeeding detection rules and default system thresholds...")
    await seed_defaults()
    print("Seeding complete.")
    
    await engine.dispose()
    print("\nDatabase initialization complete!")

if __name__ == "__main__":
    asyncio.run(main())
