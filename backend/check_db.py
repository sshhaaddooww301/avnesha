import asyncio
import asyncpg

async def check_and_setup_db():
    print("Checking PostgreSQL connection on port 5436 with user postgres...")
    try:
        conn = await asyncpg.connect("postgresql://postgres:postgres123@localhost:5436/postgres")
        print("Connected to PostgreSQL successfully!")
        
        row = await conn.fetchrow("SELECT 1 FROM pg_database WHERE datname = 'qds_siem'")
        if not row:
            print("Database qds_siem not found. Creating it now...")
            await conn.execute("CREATE DATABASE qds_siem")
            print("Database qds_siem created successfully!")
        else:
            print("Database qds_siem already exists!")
        await conn.close()
    except Exception as e:
        print(f"PostgreSQL connection error: {e}")

if __name__ == "__main__":
    asyncio.run(check_and_setup_db())
