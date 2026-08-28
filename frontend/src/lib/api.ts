import {
  DashboardSummary,
  TimelinePoint,
  SeverityDistribution,
  TopOffense,
  SecurityEvent,
  Threat,
  SystemSettings,
  ReportSummary,
  SimulatorStatus,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API Error ${res.status}: ${errorBody || res.statusText}`);
  }

  return res.json();
}

export const api = {
  // Dashboard
  getSummary: () => fetcher<DashboardSummary>("/api/dashboard/summary"),
  getTimeline: (range = "24h") => fetcher<TimelinePoint[]>(`/api/dashboard/timeline?range=${range}`),
  getSeverityDistribution: () => fetcher<SeverityDistribution[]>("/api/dashboard/severity-distribution"),
  getTopOffenses: (limit = 5) => fetcher<TopOffense[]>(`/api/dashboard/top-offenses?limit=${limit}`),
  getRecentIncidents: (limit = 10) => fetcher<any[]>(`/api/dashboard/recent-incidents?limit=${limit}`),
  getLogTimeline: (limit = 20) => fetcher<any[]>(`/api/dashboard/log-timeline?limit=${limit}`),

  // Events
  getEvents: (params?: Record<string, any>) => {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") {
          query.append(k, String(v));
        }
      });
    }
    return fetcher<{ items: SecurityEvent[]; total: number; page: number; page_size: number; total_pages: number }>(
      `/api/events?${query.toString()}`
    );
  },
  getEventDetail: (eventId: string) => fetcher<SecurityEvent>(`/api/events/${eventId}`),

  // Threats
  getThreats: (params?: Record<string, any>) => {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") {
          query.append(k, String(v));
        }
      });
    }
    return fetcher<{ items: Threat[]; total: number; page: number; page_size: number; total_pages: number }>(
      `/api/threats?${query.toString()}`
    );
  },
  getThreatDetail: (threatId: string) => fetcher<Threat>(`/api/threats/${threatId}`),
  updateThreatStatus: (threatId: string, status: string) =>
    fetcher<{ threat_id: string; status: string }>(`/api/threats/${threatId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  // Simulator
  getSimulatorStatus: () => fetcher<SimulatorStatus>("/api/simulator/status"),
  runSimulator: (mode: string, count = 10, interval_ms = 500) =>
    fetcher<{ status: string; events_generated: number; threats_detected: number; message: string }>(
      "/api/simulator/run",
      {
        method: "POST",
        body: JSON.stringify({ mode, count, interval_ms }),
      }
    ),

  // Ledger
  getLedgerStatus: () => fetcher<{ total_blocks: number; last_block_index?: number; last_block_hash?: string; integrity: string }>("/api/ledger/status"),
  verifyLedger: () => fetcher<{ valid: boolean; total_blocks: number; verified_blocks: number; first_invalid_block?: number; message: string }>("/api/ledger/verify", {
    method: "POST",
  }),
  getLedgerBlocks: (page = 1, pageSize = 20) =>
    fetcher<{ items: any[]; total: number; page: number; page_size: number }>(`/api/ledger/blocks?page=${page}&page_size=${pageSize}`),

  // Reports
  getReportSummary: (days = 30) => fetcher<ReportSummary>(`/api/reports/summary?days=${days}`),
  getExportUrl: (dataType: "threats" | "events" | "ledger") => `${API_BASE}/api/reports/export?data_type=${dataType}`,
  getPdfExportUrl: (days = 30) => `${API_BASE}/api/reports/pdf?days=${days}`,

  // Settings
  getSettings: () => fetcher<SystemSettings>("/api/settings"),
  updateSettings: (data: Partial<SystemSettings>) =>
    fetcher<{ status: string; updated_keys: string[] }>("/api/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  toggleRule: (ruleId: string, enabled: boolean) =>
    fetcher<any>(`/api/settings/rules/${ruleId}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    }),

  // Test Lab
  getTestScenarios: () => fetcher<Array<{ id: string; name: string; description: string; detection_rule: string }>>("/api/test-lab/scenarios"),
  runTestLab: (params: {
    attack_type: string;
    runs: number;
    attack_intensity?: number;
    replay_window?: number;
    measurement_perturbation?: number;
  }) =>
    fetcher<{ test_id: string; status: string; attack_type: string; runs: number; message: string }>(
      "/api/test-lab/run",
      {
        method: "POST",
        body: JSON.stringify(params),
      }
    ),
  getTestRun: (testId: string) => fetcher<any>(`/api/test-lab/${testId}`),
  getTestResults: (testId: string, page = 1, pageSize = 20) =>
    fetcher<{ test_id: string; items: any[]; total: number; page: number; page_size: number; total_pages: number }>(
      `/api/test-lab/${testId}/results?page=${page}&page_size=${pageSize}`
    ),
  getTestHistory: (page = 1, pageSize = 10, attackType?: string) => {
    const query = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (attackType) query.append("attack_type", attackType);
    return fetcher<{ items: any[]; total: number; page: number; page_size: number; total_pages: number }>(
      `/api/test-lab/history?${query.toString()}`
    );
  },
  getTestMetrics: (testId: string) => fetcher<any>(`/api/test-lab/${testId}/metrics`),

  // Physical Hardware & Optical Telemetry
  getHardwareStatus: () => fetcher<any>("/api/hardware/status"),
  syncEtsiTelemetry: (payload: any) =>
    fetcher<any>("/api/hardware/etsi/sync", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  configureHardware: (config: any) =>
    fetcher<any>("/api/hardware/configure", {
      method: "POST",
      body: JSON.stringify(config),
    }),
  pingHardwareNode: (nodeId: string) =>
    fetcher<any>("/api/hardware/ping", {
      method: "POST",
      body: JSON.stringify({ node_id: nodeId }),
    }),

  // Multi-Layer Security & DEFCON Center
  getSecurityStatus: () => fetcher<any>("/api/security/status"),
  blockIp: (ip: string, reason?: string) =>
    fetcher<any>("/api/security/ip/block", {
      method: "POST",
      body: JSON.stringify({ ip, reason }),
    }),
  unblockIp: (ip: string) =>
    fetcher<any>("/api/security/ip/unblock", {
      method: "POST",
      body: JSON.stringify({ ip }),
    }),
  whitelistIp: (ip: string) =>
    fetcher<any>("/api/security/ip/whitelist", {
      method: "POST",
      body: JSON.stringify({ ip }),
    }),
  toggleLockdown: (enabled: boolean) =>
    fetcher<any>("/api/security/lockdown", {
      method: "POST",
      body: JSON.stringify({ enabled }),
    }),
  resetCircuitBreaker: () =>
    fetcher<any>("/api/security/circuit-breaker/reset", {
      method: "POST",
    }),
  getThreatActors: () => fetcher<any>("/api/security/threat-actors"),
  getHoneypotStatus: () => fetcher<any>("/api/security/honeypot/status"),
  generateApiKey: (description?: string) =>
    fetcher<any>("/api/security/keys/generate", {
      method: "POST",
      body: JSON.stringify({ description }),
    }),
  revokeApiKey: (key_id: string) =>
    fetcher<any>("/api/security/keys/revoke", {
      method: "POST",
      body: JSON.stringify({ key_id }),
    }),
};

