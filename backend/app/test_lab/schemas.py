"""
Pydantic Schemas for QDS Attack / Test Lab.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AttackTypeEnum(str, Enum):
    normal = "normal"
    replay = "replay"
    manipulation = "manipulation"
    forgery = "forgery"
    impersonation = "impersonation"
    measurement_anomaly = "measurement_anomaly"
    pns = "pns"
    blinding = "blinding"
    repudiation = "repudiation"
    evasion = "evasion"


class TestLabRunRequest(BaseModel):
    attack_type: AttackTypeEnum = AttackTypeEnum.replay
    runs: int = Field(default=10, ge=1, le=200, description="Number of simulation iterations")
    attack_intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="Attack injection perturbation probability")
    replay_window: int = Field(default=60, ge=10, le=600, description="Replay temporal window in seconds")
    measurement_perturbation: float = Field(default=0.2, ge=0.0, le=1.0, description="Quantum state noise perturbation factor")


class TestLabRunResponse(BaseModel):
    test_id: str
    status: str
    attack_type: str
    runs: int
    message: str


class TestRunMetrics(BaseModel):
    total_runs: int
    attacks_injected: int
    normal_injected: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    detected_attacks: int
    missed_attacks: int
    detection_rate: float
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    average_risk_score: float
    max_risk_score: float
    min_risk_score: float
    average_detection_time_ms: float
    average_measurement_deviation: float


class TestResultDetail(BaseModel):
    id: int
    test_id: str
    run_index: int
    event_id: str
    attack_injected: bool
    threat_detected: bool
    threat_id: Optional[str] = None
    risk_score: Optional[float] = None
    severity: Optional[str] = None
    detection_rule: Optional[str] = None
    detection_time_ms: float = 0.0
    measurement_deviation: Optional[float] = None
    expected_measurement: Optional[float] = None
    observed_measurement: Optional[float] = None
    created_at: datetime
    source_node: Optional[str] = None
    session_id: Optional[str] = None
    verification_result: Optional[bool] = None

    class Config:
        from_attributes = True


class TestRunSummary(BaseModel):
    id: int
    test_id: str
    attack_type: str
    total_runs: int
    status: str
    params: Optional[Dict[str, Any]] = None
    metrics: Optional[TestRunMetrics] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestRunDetailResponse(BaseModel):
    summary: TestRunSummary
    metrics: Optional[TestRunMetrics] = None
    recent_results: List[TestResultDetail] = []
