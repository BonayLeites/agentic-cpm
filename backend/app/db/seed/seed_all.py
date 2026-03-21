"""Master seeder: drops all data and recreates from scratch.

Usage: python -m app.db.seed.seed_all
"""

import asyncio

from sqlalchemy import text

from app.db.models import Base
from app.db.session import async_session, engine
from app.db.seed.case1_data import seed_case1_data
from app.db.seed.case2_data import seed_case2_data
from app.db.seed.documents import seed_documents
from app.db.seed.entities import seed_chart_of_accounts, seed_entities


async def run_seed() -> None:
    """Run the full seed: drop + recreate + populate."""
    # Recreate all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("Tables recreated.")

    async with async_session() as session:
        async with session.begin():
            entity_ids = await seed_entities(session)
            account_ids = await seed_chart_of_accounts(session)
            print(f"Entities: {list(entity_ids.keys())}")
            print(f"Accounts: {len(account_ids)} created")

            await seed_case1_data(session, entity_ids, account_ids)
            print("Case 1 data (TB, IC, FX, JE) seeded.")

            await seed_case2_data(session, entity_ids, account_ids)
            print("Case 2 data (budgets, actuals Q1, KPIs) seeded.")

            await seed_documents(session)
            print("7 knowledge pack documents seeded.")

    print("\nSeed completed successfully.")


if __name__ == "__main__":
    asyncio.run(run_seed())
