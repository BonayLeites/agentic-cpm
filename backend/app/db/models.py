from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    country = Column(String(50))
    currency = Column(String(3), nullable=False)
    parent_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    ownership_pct = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    parent = relationship("Entity", remote_side=[id], back_populates="children")
    children = relationship("Entity", back_populates="parent")


class ChartOfAccounts(Base):
    __tablename__ = "chart_of_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_code = Column(String(20), unique=True, nullable=False)
    account_name = Column(String(100), nullable=False)
    account_type = Column(String(20), nullable=False)  # revenue, expense, asset, liability, equity
    parent_account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=True)


class TrialBalance(Base):
    __tablename__ = "trial_balances"
    __table_args__ = (
        UniqueConstraint("entity_id", "account_id", "period", name="uq_tb_entity_account_period"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    period = Column(String(7), nullable=False)  # "YYYY-MM"
    debit = Column(Numeric(18, 2), default=0)
    credit = Column(Numeric(18, 2), default=0)

    entity = relationship("Entity")
    account = relationship("ChartOfAccounts")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_number = Column(String(20), unique=True, nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    period = Column(String(7), nullable=False)
    entry_date = Column(Date, nullable=False)
    description = Column(Text)
    posted_by = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    entity = relationship("Entity")
    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    debit = Column(Numeric(18, 2), default=0)
    credit = Column(Numeric(18, 2), default=0)
    description = Column(Text)

    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("ChartOfAccounts")


class IntercompanyTransaction(Base):
    __tablename__ = "intercompany_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    to_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    transaction_type = Column(String(50))  # services, royalties
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    period = Column(String(7), nullable=False)
    invoice_date = Column(Date)
    recorded_date = Column(Date)
    from_amount = Column(Numeric(18, 2))
    to_amount = Column(Numeric(18, 2))
    to_amount_jpy = Column(Numeric(18, 2))
    mismatch_amount = Column(Numeric(18, 2), default=0)

    from_entity = relationship("Entity", foreign_keys=[from_entity_id])
    to_entity = relationship("Entity", foreign_keys=[to_entity_id])


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint(
            "from_currency", "to_currency", "rate_type", "effective_date",
            name="uq_fx_rate",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate_type = Column(String(20), nullable=False)  # average, closing
    rate = Column(Numeric(12, 6), nullable=False)
    effective_date = Column(Date, nullable=False)


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    period = Column(String(7), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)

    entity = relationship("Entity")
    account = relationship("ChartOfAccounts")


class KPI(Base):
    __tablename__ = "kpis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    kpi_name = Column(String(50), nullable=False)
    kpi_value = Column(Numeric(18, 4), nullable=False)
    kpi_target = Column(Numeric(18, 4), nullable=True)
    period = Column(String(7), nullable=False)
    unit = Column(String(20))  # pct, days, score, count, currency code

    entity = relationship("Entity")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    doc_type = Column(String(50))  # policy, notes, rules, commentary, template, benchmarks
    content = Column(Text, nullable=False)
    doc_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_type = Column(String(20), nullable=False)  # consolidation, performance
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_duration_ms = Column(Integer, nullable=True)
    total_findings = Column(Integer, default=0)
    total_cost = Column(Numeric(8, 4), nullable=True)
    overall_confidence = Column(Numeric(5, 2), nullable=True)
    config_snapshot = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    steps = relationship("WorkflowStep", back_populates="run", cascade="all, delete-orphan", order_by="WorkflowStep.step_order")
    findings = relationship("Finding", back_populates="run", cascade="all, delete-orphan")
    summaries = relationship("ExecutiveSummary", back_populates="run", cascade="all, delete-orphan")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("workflow_runs.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    agent_name = Column(String(50), nullable=False)
    status = Column(String(20), default="queued")  # queued, running, completed, failed, escalated
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    tools_used = Column(JSONB, nullable=True)
    llm_calls = Column(JSONB, nullable=True)
    finding_count = Column(Integer, default=0)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    cost = Column(Numeric(8, 4), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    run = relationship("WorkflowRun", back_populates="steps")
    findings = relationship("Finding", back_populates="step")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("workflow_runs.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=True)
    title = Column(String(500), nullable=False)
    severity = Column(String(10), nullable=False)  # high, medium, low
    status = Column(String(20), default="open")  # open, needs_review, in_progress, resolved
    category = Column(String(50))
    entity_code = Column(String(50), nullable=True)
    description = Column(Text)
    impact_amount = Column(Numeric(18, 2), nullable=True)
    impact_currency = Column(String(10), default="JPY")
    rule_triggered = Column(String(200), nullable=True)
    evidence = Column(JSONB)
    suggested_questions = Column(JSONB)
    suggested_actions = Column(JSONB)
    confidence = Column(Numeric(5, 2))
    escalation_needed = Column(Boolean, default=False)
    escalation_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    run = relationship("WorkflowRun", back_populates="findings")
    step = relationship("WorkflowStep", back_populates="findings")


class ExecutiveSummary(Base):
    __tablename__ = "executive_summaries"
    __table_args__ = (
        UniqueConstraint("run_id", "audience", name="uq_summary_run_audience"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("workflow_runs.id"), nullable=False)
    audience = Column(String(20), nullable=False)  # controller, executive
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    run = relationship("WorkflowRun", back_populates="summaries")
