export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type ThreatStatus = 'open' | 'investigating' | 'resolved' | 'false_positive';

export interface SecurityEvent {
  id: number;
  event_id: string;
  timestamp: string;
  session_id: string;
  source_node: string;
  event_type: string;
  quantum_state?: string;
  expected_measurement?: number;
  observed_measurement?: number;
  measurement_deviation?: number;
  verification_result?: boolean;
  signature_hash?: string;
  has_threats?: boolean;
  threat_count?: number;
  threat_severity?: Severity;
  metadata_json?: Record<string, any>;
  created_at?: string;
}

export interface Threat {
  id: number;
  threat_id: string;
  event_id: string;
  threat_type: string;
  severity: Severity;
  risk_score: number;
  detection_rule: string;
  confidence: number;
  status: ThreatStatus;
  detected_at: string;
  resolved_at?: string;
  source_node?: string;
  session_id?: string;
  evidence?: {
    source_ip?: string;
    risk_breakdown?: {
      risk_score: number;
      formula: string;
      factors: Record<string, any>;
    };
    triggered_rules?: Array<{ rule_id: string; confidence: number }>;
    primary_evidence?: Record<string, any>;
    all_triggered?: string[];
    [key: string]: any;
  };
  event?: SecurityEvent;
  quantum_analysis?: {
    quantum_state?: string;
    expected_measurement?: number;
    observed_measurement?: number;
    deviation_ratio?: number;
    deviation_percentage?: number;
    verification_result?: boolean;
    signature_hash?: string;
  };
  statistical_analysis?: {
    sample_size: number;
    mean_deviation: number;
    std_deviation: number;
    variance: number;
    z_score: number;
  };
  audit_block?: AuditBlock;
}

export interface AuditBlock {
  id?: number;
  block_index: number;
  event_id: string;
  event_hash: string;
  previous_hash: string;
  block_hash: string;
  payload_hash: string;
  timestamp: string;
}

export interface DashboardSummary {
  total_events: number;
  total_threats: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  open_threats: number;
  verification_success_rate?: number;
  ledger_integrity: string;
}

export interface TimelinePoint {
  timestamp: string;
  count: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface SeverityDistribution {
  severity: string;
  count: number;
  percentage: number;
}

export interface TopOffense {
  threat_type: string;
  count: number;
  percentage: number;
}

export interface SystemSettings {
  severity_thresholds: {
    low_max: number;
    medium_max: number;
    high_max: number;
  };
  risk_weights: {
    weight_deviation: number;
    weight_verification: number;
    weight_frequency: number;
    weight_anomaly: number;
    weight_hash_mismatch: number;
  };
  detection_thresholds: {
    deviation_threshold: number;
    zscore_threshold: number;
    replay_window_seconds: number;
    anomaly_sensitivity: number;
  };
  detection_rules: Array<{
    rule_id: string;
    name: string;
    description: string;
    enabled: boolean;
    parameters?: Record<string, any>;
  }>;
}

export interface ReportSummary {
  report_period_days: number;
  generated_at: string;
  total_events: number;
  total_threats: number;
  verification_success_count: number;
  verification_failure_count: number;
  verification_success_rate?: number;
  most_frequent_attack?: string;
  severity_distribution: SeverityDistribution[];
  threat_distribution: Array<{ threat_type: string; count: number; percentage: number }>;
  measurement_stats?: {
    sample_count: number;
    mean_deviation_pct: number;
    std_deviation_pct: number;
    variance: number;
    max_deviation_pct: number;
    min_deviation_pct: number;
  };
  ledger_integrity: string;
  ledger_total_blocks: number;
}

export interface SimulatorStatus {
  engine: string;
  qiskit_installed: boolean;
  available_modes: Array<{
    id: string;
    name: string;
    description: string;
  }>;
  node_pool_size: number;
}

// --- Test Lab Types ---

export type AttackScenarioType =
  | "normal"
  | "replay"
  | "manipulation"
  | "forgery"
  | "impersonation"
  | "measurement_anomaly"
  | "pns"
  | "blinding"
  | "repudiation"
  | "evasion";

export interface TestLabRunParams {
  attack_type: AttackScenarioType;
  runs: number;
  attack_intensity: number;
  replay_window: number;
  measurement_perturbation: number;
}

export interface TestRunMetrics {
  total_runs: number;
  attacks_injected: number;
  normal_injected: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  detected_attacks: number;
  missed_attacks: number;
  detection_rate: number;
  precision: number;
  recall: number;
  f1_score: number;
  accuracy: number;
  average_risk_score: number;
  max_risk_score: number;
  min_risk_score: number;
  average_detection_time_ms: number;
  average_measurement_deviation: number;
}

export interface TestResultDetail {
  id: number;
  run_index: number;
  event_id: string;
  attack_injected: boolean;
  threat_detected: boolean;
  threat_id?: string | null;
  risk_score?: number | null;
  severity?: string | null;
  detection_rule?: string | null;
  detection_time_ms: number;
  measurement_deviation?: number | null;
  expected_measurement?: number | null;
  observed_measurement?: number | null;
  source_ip?: string | null;
  source_node?: string | null;
  session_id?: string | null;
  ips_action?: string | null;
  created_at: string;
}

export interface TestRunSummary {
  id: number;
  test_id: string;
  attack_type: string;
  attack_name?: string;
  total_runs: number;
  status: "pending" | "running" | "completed" | "failed";
  params?: Record<string, any>;
  metrics?: TestRunMetrics;
  created_at: string;
  completed_at?: string;
}

export interface TestRunDetailResponse {
  summary: TestRunSummary;
  metrics?: TestRunMetrics;
  results_count: number;
  results: TestResultDetail[];
}

export interface TestScenarioInfo {
  id: string;
  name: string;
  description: string;
  detection_rule: string;
}

