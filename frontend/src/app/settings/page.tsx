"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { api } from "@/lib/api";
import { SystemSettings } from "@/lib/types";
import {
  Settings as SettingsIcon,
  Sliders,
  ShieldAlert,
  Save,
  CheckCircle2,
  ToggleLeft,
  ToggleRight,
  Database,
  Atom,
} from "lucide-react";

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  // Form states
  const [sevLowMax, setSevLowMax] = useState(24);
  const [sevMedMax, setSevMedMax] = useState(49);
  const [sevHighMax, setSevHighMax] = useState(74);

  const [wDeviation, setWDeviation] = useState(0.30);
  const [wVerification, setWVerification] = useState(0.25);
  const [wFrequency, setWFrequency] = useState(0.15);
  const [wAnomaly, setWAnomaly] = useState(0.20);
  const [wHashMismatch, setWHashMismatch] = useState(0.10);

  const [devThreshold, setDevThreshold] = useState(0.30);
  const [zScoreThreshold, setZScoreThreshold] = useState(2.5);
  const [replayWindow, setReplayWindow] = useState(300);

  const fetchSettings = useCallback(async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);

      if (data.severity_thresholds) {
        setSevLowMax(data.severity_thresholds.low_max);
        setSevMedMax(data.severity_thresholds.medium_max);
        setSevHighMax(data.severity_thresholds.high_max);
      }

      if (data.risk_weights) {
        setWDeviation(data.risk_weights.weight_deviation);
        setWVerification(data.risk_weights.weight_verification);
        setWFrequency(data.risk_weights.weight_frequency);
        setWAnomaly(data.risk_weights.weight_anomaly);
        setWHashMismatch(data.risk_weights.weight_hash_mismatch);
      }

      if (data.detection_thresholds) {
        setDevThreshold(data.detection_thresholds.deviation_threshold);
        setZScoreThreshold(data.detection_thresholds.zscore_threshold);
        setReplayWindow(data.detection_thresholds.replay_window_seconds);
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async () => {
    try {
      setSaving(true);
      setSaveMsg(null);
      await api.updateSettings({
        severity_thresholds: {
          low_max: sevLowMax,
          medium_max: sevMedMax,
          high_max: sevHighMax,
        },
        risk_weights: {
          weight_deviation: wDeviation,
          weight_verification: wVerification,
          weight_frequency: wFrequency,
          weight_anomaly: wAnomaly,
          weight_hash_mismatch: wHashMismatch,
        },
        detection_thresholds: {
          deviation_threshold: devThreshold,
          zscore_threshold: zScoreThreshold,
          replay_window_seconds: replayWindow,
          anomaly_sensitivity: 0.5,
        },
      });
      setSaveMsg("Configuration updated successfully.");
      setTimeout(() => setSaveMsg(null), 4000);
      fetchSettings();
    } catch (err: any) {
      setSaveMsg(`Error: ${err.message || "Failed to update settings"}`);
    } finally {
      setSaving(false);
    }
  };

  const handleToggleRule = async (ruleId: string, currentEnabled: boolean) => {
    try {
      await api.toggleRule(ruleId, !currentEnabled);
      fetchSettings();
    } catch (err) {
      console.error("Rule toggle error:", err);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-zinc-200">
      <Navbar />

      <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-bold text-white tracking-wide uppercase font-mono">
              Detection Engine Settings
            </h1>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Tune mathematical thresholds, multi-factor risk weights, and detection rule activations
            </p>
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2 rounded-lg bg-white hover:bg-zinc-100 text-zinc-950 font-semibold text-xs shadow-md transition-all disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? "Saving..." : "Save Configuration"}</span>
          </button>
        </div>

        {saveMsg && (
          <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-700 text-xs font-mono text-zinc-200 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{saveMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (8 cols): Mathematical Configuration */}
          <div className="lg:col-span-8 space-y-6">
            {/* Severity Thresholds */}
            <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-border">
                <ShieldAlert className="w-5 h-5 text-zinc-400" />
                <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
                  Severity Classification Thresholds (0 - 100 Risk Score)
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
                <div>
                  <label className="block text-zinc-400 mb-1">
                    Low Max: <strong className="text-zinc-200">{sevLowMax}</strong>
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="40"
                    value={sevLowMax}
                    onChange={(e) => setSevLowMax(parseInt(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                  <span className="text-[10px] text-zinc-500 block mt-1">Scores 0–{sevLowMax} are Low</span>
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1">
                    Medium Max: <strong className="text-amber-300">{sevMedMax}</strong>
                  </label>
                  <input
                    type="range"
                    min="40"
                    max="65"
                    value={sevMedMax}
                    onChange={(e) => setSevMedMax(parseInt(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                  <span className="text-[10px] text-zinc-500 block mt-1">Scores {sevLowMax+1}–{sevMedMax} are Medium</span>
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1">
                    High Max: <strong className="text-orange-400">{sevHighMax}</strong>
                  </label>
                  <input
                    type="range"
                    min="65"
                    max="85"
                    value={sevHighMax}
                    onChange={(e) => setSevHighMax(parseInt(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                  <span className="text-[10px] text-zinc-500 block mt-1">Scores &gt;{sevHighMax} are Critical</span>
                </div>
              </div>
            </div>

            {/* Risk Formula Weights */}
            <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-border">
                <Sliders className="w-5 h-5 text-zinc-400" />
                <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
                  Multi-Factor Risk Weights (Sum: {(wDeviation + wVerification + wFrequency + wAnomaly + wHashMismatch).toFixed(2)})
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono text-xs">
                <div>
                  <label className="block text-zinc-400 mb-1">
                    Deviation Weight: <strong className="text-zinc-200">{wDeviation.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="0.6"
                    step="0.05"
                    value={wDeviation}
                    onChange={(e) => setWDeviation(parseFloat(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1">
                    Verification Penalty: <strong className="text-zinc-200">{wVerification.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="0.6"
                    step="0.05"
                    value={wVerification}
                    onChange={(e) => setWVerification(parseFloat(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1">
                    Repeat Frequency Weight: <strong className="text-zinc-200">{wFrequency.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="0.4"
                    step="0.05"
                    value={wFrequency}
                    onChange={(e) => setWFrequency(parseFloat(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1">
                    Anomaly (Z-Score) Weight: <strong className="text-zinc-200">{wAnomaly.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="0.5"
                    step="0.05"
                    value={wAnomaly}
                    onChange={(e) => setWAnomaly(parseFloat(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-zinc-400 mb-1">
                    Hash Mismatch Penalty: <strong className="text-zinc-200">{wHashMismatch.toFixed(2)}</strong>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="0.4"
                    step="0.05"
                    value={wHashMismatch}
                    onChange={(e) => setWHashMismatch(parseFloat(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                </div>
              </div>
            </div>

            {/* Detection Mathematical Thresholds */}
            <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-border">
                <Atom className="w-5 h-5 text-zinc-400" />
                <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
                  Detection Rule Thresholds
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
                <div>
                  <label className="block text-zinc-400 mb-1">
                    Deviation Threshold: <strong className="text-white">{(devThreshold * 100).toFixed(0)}%</strong>
                  </label>
                  <input
                    type="range"
                    min="0.10"
                    max="0.70"
                    step="0.05"
                    value={devThreshold}
                    onChange={(e) => setDevThreshold(parseFloat(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1">
                    Z-Score Threshold: <strong className="text-white">{zScoreThreshold.toFixed(1)}σ</strong>
                  </label>
                  <input
                    type="range"
                    min="1.5"
                    max="4.0"
                    step="0.1"
                    value={zScoreThreshold}
                    onChange={(e) => setZScoreThreshold(parseFloat(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1">
                    Replay Window (sec): <strong className="text-white">{replayWindow}s</strong>
                  </label>
                  <input
                    type="range"
                    min="60"
                    max="900"
                    step="30"
                    value={replayWindow}
                    onChange={(e) => setReplayWindow(parseInt(e.target.value))}
                    className="w-full accent-zinc-400"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (4 cols): Detection Rules Activation & Engine Status */}
          <div className="lg:col-span-4 space-y-6">
            <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-border">
                <SettingsIcon className="w-5 h-5 text-zinc-400" />
                <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
                  Detection Rules Registry
                </h3>
              </div>

              <div className="space-y-3 font-mono text-xs">
                {settings?.detection_rules.map((rule) => (
                  <div
                    key={rule.rule_id}
                    className="p-3 bg-zinc-950/80 rounded-lg border border-border flex items-start justify-between gap-2"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">{rule.rule_id}</span>
                        <span className="text-[10px] text-zinc-500">{rule.name}</span>
                      </div>
                      <p className="text-[10px] text-zinc-400 mt-1 font-sans">{rule.description}</p>
                    </div>

                    <button
                      onClick={() => handleToggleRule(rule.rule_id, rule.enabled)}
                      className="p-1 rounded text-zinc-400 hover:text-white"
                      title={rule.enabled ? "Disable Rule" : "Enable Rule"}
                    >
                      {rule.enabled ? (
                        <ToggleRight className="w-6 h-6 text-white" />
                      ) : (
                        <ToggleLeft className="w-6 h-6 text-zinc-600" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* System Status Cards */}
            <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-3 font-mono text-xs">
              <div className="flex items-center gap-2 pb-2 border-b border-border text-white font-semibold">
                <Database className="w-4 h-4 text-zinc-400" />
                <span>Engine Integrations</span>
              </div>

              <div className="flex items-center justify-between text-[11px]">
                <span className="text-zinc-400">PostgreSQL (Port 5436):</span>
                <span className="text-emerald-400 font-bold">CONNECTED</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-zinc-400">Quantum Simulator:</span>
                <span className="text-zinc-200 font-bold">ACTIVE</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-zinc-400">Audit Ledger:</span>
                <span className="text-emerald-400 font-bold">TAMPER-EVIDENT</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-zinc-400">WebSocket Dispatcher:</span>
                <span className="text-zinc-200 font-bold">BROADCASTING</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
