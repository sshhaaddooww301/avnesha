from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# --- Enums ---

class SeverityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ThreatStatusEnum(str, Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"
    false_positive = "false_positive"


class SimulationMode(str, Enum):
    normal = "normal"
    attack_mix = "attack_mix"
    replay = "replay"
    mitm = "mitm"
    forgery = "forgery"
    impersonation = "impersonation"
    anomaly = "anomaly"
    pns = "pns"
    blinding = "blinding"
    repudiation = "repudiation"
    evasion = "evasion"


# --- Security Event Schemas ---

class SecurityEventCreate(BaseModel):
    session_id: str
    source_node: str
    event_type: str
    quantum_state: Optional[str] = None
    expected_measurement: Optional[float] = None
    observed_measurement: Optional[float] = None
    verification_result: Optional[bool] = None
    signature_hash: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class SecurityEventResponse(BaseModel):
    id: int
    event_id: str
    timestamp: datetime
    session_id: str
    source_node: str
    event_type: str
    quantum_state: Optional[str] = None
    expected_measurement: Optional[float] = None
    observed_measurement: Optional[float] = None
    measurement_deviation: Optional[float] = None
    verification_result: Optional[bool] = None
    signature_hash: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityEventDetail(SecurityEventResponse):
    threats: List["ThreatResponse"] = []
    audit_block: Optional["AuditBlockResponse"] = None


# --- Threat Schemas ---

class ThreatResponse(BaseModel):
    id: int
    threat_id: str
    event_id: str
    threat_type: str
    severity: str
    risk_score: float
    detection_rule: str
    confidence: float
    status: str
    evidence: Optional[Dict[str, Any]] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ThreatDetail(ThreatResponse):
    event: Optional[SecurityEventResponse] = None
    audit_block: Optional["AuditBlockResponse"] = None
    quantum_analysis: Optional[Dict[str, Any]] = None
    statistical_analysis: Optional[Dict[str, Any]] = None


class ThreatStatusUpdate(BaseModel):
    status: ThreatStatusEnum


# --- Audit Ledger Schemas ---

class AuditBlockResponse(BaseModel):
    id: int
    block_index: int
    event_id: str
    event_hash: str
    previous_hash: str
    block_hash: str
    timestamp: datetime
    payload_hash: str

    class Config:
        from_attributes = True


class LedgerVerificationResponse(BaseModel):
    valid: bool
    total_blocks: int
    verified_blocks: int
    first_invalid_block: Optional[int] = None
    message: str


class LedgerStatusResponse(BaseModel):
    total_blocks: int
    last_block_index: Optional[int] = None
    last_block_hash: Optional[str] = None
    last_block_timestamp: Optional[datetime] = None
    integrity: str  # "VALID", "COMPROMISED", "EMPTY"


# --- Dashboard Schemas ---

class DashboardSummary(BaseModel):
    total_events: int
    total_threats: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    open_threats: int
    verification_success_rate: Optional[float] = None
    ledger_integrity: str


class TimelinePoint(BaseModel):
    timestamp: str
    count: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class SeverityDistribution(BaseModel):
    severity: str
    count: int
    percentage: float


class TopOffense(BaseModel):
    threat_type: str
    count: int
    percentage: float


# --- Simulator Schemas ---

class SimulatorRequest(BaseModel):
    mode: SimulationMode = SimulationMode.normal
    count: int = Field(default=10, ge=1, le=100)
    interval_ms: int = Field(default=500, ge=100, le=10000)


class SimulatorResponse(BaseModel):
    status: str
    events_generated: int
    threats_detected: int
    message: str


# --- Report Schemas ---

class ReportSummary(BaseModel):
    total_events: int
    total_threats: int
    threat_distribution: List[Dict[str, Any]]
    severity_distribution: List[SeverityDistribution]
    verification_success_count: int
    verification_failure_count: int
    verification_success_rate: Optional[float] = None
    most_frequent_attack: Optional[str] = None
    measurement_stats: Optional[Dict[str, float]] = None
    ledger_integrity: str
    ledger_total_blocks: int
    detection_trends: List[Dict[str, Any]]


# --- Settings Schemas ---

class SeverityThresholdsUpdate(BaseModel):
    low_max: Optional[int] = Field(None, ge=1, le=90)
    medium_max: Optional[int] = Field(None, ge=5, le=95)
    high_max: Optional[int] = Field(None, ge=10, le=99)


class RiskWeightsUpdate(BaseModel):
    weight_deviation: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_verification: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_frequency: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_anomaly: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_hash_mismatch: Optional[float] = Field(None, ge=0.0, le=1.0)


class DetectionThresholdsUpdate(BaseModel):
    deviation_threshold: Optional[float] = Field(None, ge=0.01, le=1.0)
    zscore_threshold: Optional[float] = Field(None, ge=0.5, le=10.0)
    replay_window_seconds: Optional[int] = Field(None, ge=10, le=86400)
    anomaly_sensitivity: Optional[float] = Field(None, ge=0.01, le=1.0)


class SettingsResponse(BaseModel):
    severity_thresholds: Dict[str, int]
    risk_weights: Dict[str, float]
    detection_thresholds: Dict[str, Any]
    detection_rules: List[Dict[str, Any]]


class SettingsUpdate(BaseModel):
    severity_thresholds: Optional[SeverityThresholdsUpdate] = None
    risk_weights: Optional[RiskWeightsUpdate] = None
    detection_thresholds: Optional[DetectionThresholdsUpdate] = None
    severity_low_max: Optional[int] = Field(None, ge=1, le=90)
    severity_medium_max: Optional[int] = Field(None, ge=5, le=95)
    severity_high_max: Optional[int] = Field(None, ge=10, le=99)
    weight_deviation: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_verification: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_frequency: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_anomaly: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_hash_mismatch: Optional[float] = Field(None, ge=0.0, le=1.0)
    deviation_threshold: Optional[float] = Field(None, ge=0.01, le=1.0)
    zscore_threshold: Optional[float] = Field(None, ge=0.5, le=10.0)
    replay_window_seconds: Optional[int] = Field(None, ge=10, le=86400)
    anomaly_sensitivity: Optional[float] = Field(None, ge=0.01, le=1.0)


# --- Pagination ---

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Forward reference resolution
SecurityEventDetail.model_rebuild()
ThreatDetail.model_rebuild()
