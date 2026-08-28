import asyncio
from sqlalchemy import text
from app.database import async_session_factory, engine

async def get_db_stats():
    async with async_session_factory() as session:
        is_sqlite = "sqlite" in str(engine.url)
        if is_sqlite:
            query = text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        else:
            query = text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            
        result = await session.execute(query)
        tables = [row[0] for row in result.fetchall()]
        
        print("=" * 55)
        print(f"DATABASE TYPE : {engine.url.drivername}")
        print(f"TOTAL TABLES  : {len(tables)}")
        print("=" * 55)
        
        total_rows = 0
        for table in sorted(tables):
            count_res = await session.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            count = count_res.scalar()
            total_rows += count
            print(f"• {table:<28} : {count:>6} rows")
            
        print("=" * 55)
        print(f"TOTAL ROWS ACROSS ALL TABLES : {total_rows:>6}")
        print("=" * 55)

if __name__ == "__main__":
    asyncio.run(get_db_stats())
