import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    session_id = Column(String(64), nullable=False, index=True)
    source_node = Column(String(128), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    quantum_state = Column(Text, nullable=True)
    expected_measurement = Column(Float, nullable=True)
    observed_measurement = Column(Float, nullable=True)
    measurement_deviation = Column(Float, nullable=True)
    verification_result = Column(Boolean, nullable=True)
    signature_hash = Column(String(128), nullable=True)
    metadata_json = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    threats = relationship("Threat", back_populates="event", lazy="selectin")

    __table_args__ = (
        Index("ix_security_events_timestamp", "timestamp"),
        Index("ix_security_events_signature_hash", "signature_hash"),
    )


class Threat(Base):
    __tablename__ = "threats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    threat_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("security_events.event_id"), nullable=False, index=True)
    threat_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    detection_rule = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), nullable=False, default="open", index=True)
    evidence = Column(JSONB, nullable=True, default=dict)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    event = relationship("SecurityEvent", back_populates="threats", lazy="selectin")

    __table_args__ = (
        Index("ix_threats_detected_at", "detected_at"),
        Index("ix_threats_severity_status", "severity", "status"),
    )


class AuditLedger(Base):
    __tablename__ = "audit_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    block_index = Column(Integer, unique=True, nullable=False)
    event_id = Column(String(36), nullable=False, index=True)
    event_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=False)
    block_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    payload_hash = Column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_audit_ledger_block_index", "block_index"),
    )


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(32), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    parameters = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False)
    value = Column(JSONB, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    attack_type = Column(String(64), nullable=False, index=True)
    total_runs = Column(Integer, nullable=False, default=10)
    status = Column(String(32), nullable=False, default="pending", index=True)  # pending, running, completed, failed
    params = Column(JSONB, nullable=True, default=dict)
    metrics = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    results = relationship("TestResult", back_populates="test_run", cascade="all, delete-orphan", lazy="selectin")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(36), ForeignKey("test_runs.test_id", ondelete="CASCADE"), nullable=False, index=True)
    run_index = Column(Integer, nullable=False)
    event_id = Column(String(36), ForeignKey("security_events.event_id"), nullable=False, index=True)
    attack_injected = Column(Boolean, nullable=False, default=False)
    threat_detected = Column(Boolean, nullable=False, default=False)
    threat_id = Column(String(36), nullable=True)
    risk_score = Column(Float, nullable=True)
    severity = Column(String(16), nullable=True)
    detection_rule = Column(String(32), nullable=True)
    detection_time_ms = Column(Float, nullable=True, default=0.0)
    measurement_deviation = Column(Float, nullable=True)
    expected_measurement = Column(Float, nullable=True)
    observed_measurement = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    test_run = relationship("TestRun", back_populates="results")
    event = relationship("SecurityEvent", foreign_keys=[event_id], lazy="selectin")

