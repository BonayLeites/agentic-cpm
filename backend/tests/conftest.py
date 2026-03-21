"""Central fixtures for CPM backend tests."""

import os
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base
from app.llm.gateway import LLMResponse

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/cpm_test",
)


# ---------------------------------------------------------------------------
# Engine y session factory (scope=session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def test_engine():
    """Create cpm_test DB if it does not exist, then drop/recreate all tables."""
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'cpm_test'"))
        if not result.scalar():
            await conn.execute(text("CREATE DATABASE cpm_test"))
    await admin_engine.dispose()

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """Session factory for tests."""
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Seed data (scope=session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def seeded_db(test_session_factory):
    """Seed test data once per session."""
    from app.db.seed.case1_data import seed_case1_data
    from app.db.seed.case2_data import seed_case2_data
    from app.db.seed.documents import seed_documents
    from app.db.seed.entities import seed_chart_of_accounts, seed_entities

    async with test_session_factory() as session:
        async with session.begin():
            entity_ids = await seed_entities(session)
            account_ids = await seed_chart_of_accounts(session)
            await seed_case1_data(session, entity_ids, account_ids)
            await seed_case2_data(session, entity_ids, account_ids)
            await seed_documents(session)
    return True


# ---------------------------------------------------------------------------
# Per-test session
# ---------------------------------------------------------------------------

@pytest.fixture
async def db_session(test_session_factory, seeded_db) -> AsyncGenerator[AsyncSession, None]:
    """DB session per test (read-only over seeded data)."""
    async with test_session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# LLM mock helpers
# ---------------------------------------------------------------------------

def make_llm_response(content: str, model: str = "gpt-4o") -> LLMResponse:
    """Create an LLMResponse with sensible default values."""
    return LLMResponse(
        content=content,
        prompt_tokens=100,
        completion_tokens=200,
        total_tokens=300,
        cost=0.005,
        model=model,
        duration_ms=500,
    )
