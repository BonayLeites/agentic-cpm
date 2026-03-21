from pathlib import Path

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document

KNOWLEDGE_PACKS_DIR = Path(__file__).parent / "knowledge_packs"

# File -> (doc_type, associated workflow) mapping
DOCUMENT_REGISTRY = [
    ("consolidation_policy.md", "policy", "consolidation"),
    ("close_notes_feb_2026.md", "notes", "consolidation"),
    ("ic_elimination_rules.md", "rules", "consolidation"),
    ("fpa_commentary_q1_2026.md", "commentary", "performance"),
    ("board_agenda_template.md", "template", "performance"),
    ("market_benchmarks_2026.md", "benchmarks", "performance"),
    ("management_commentary_q4_2025.md", "commentary", "performance"),
]


async def seed_documents(session: AsyncSession) -> None:
    """Load the 7 knowledge pack documents from markdown files."""
    rows = []
    for filename, doc_type, workflow_type in DOCUMENT_REGISTRY:
        filepath = KNOWLEDGE_PACKS_DIR / filename
        content = filepath.read_text(encoding="utf-8")

        # Title: filename without extension, formatted
        title = filename.replace(".md", "").replace("_", " ").title()

        rows.append({
            "title": title,
            "doc_type": doc_type,
            "content": content,
            "doc_metadata": {"workflow_type": workflow_type, "source_file": filename},
        })

    await session.execute(insert(Document), rows)
    await session.flush()
