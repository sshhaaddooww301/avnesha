"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { api } from "@/lib/api";
import { Threat } from "@/lib/types";
import { formatDateTime, formatPercent } from "@/lib/utils";
import {
  ShieldAlert,
  ShieldCheck,
  Ban,
  ArrowLeft,
  Atom,
  Lock,
  Activity,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";

export default function ThreatDetailPage() {
  const params = useParams();
  const threatId = params.id as string;

  const [threat, setThreat] = useState<Threat | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [ipActionMsg, setIpActionMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [isIpProcessing, setIsIpProcessing] = useState(false);

  const fetchThreat = useCallback(async () => {
    if (!threatId) return;
    try {
      setLoading(true);
      const data = await api.getThreatDetail(threatId);
      setThreat(data);
    } catch (err) {
      console.error("Failed to load threat detail:", err);
    } finally {
      setLoading(false);
    }
  }, [threatId]);

  useEffect(() => {
    fetchThreat();
  }, [fetchThreat]);

  const handleUpdateStatus = async (newStatus: string) => {
    try {
      setStatusUpdating(true);
      await api.updateThreatStatus(threatId, newStatus);
      setStatusMsg(`Status updated: ${newStatus}`);
      setTimeout(() => setStatusMsg(null), 3000);
      fetchThreat();
    } catch (err) {
      console.error("Status update error:", err);
    } finally {
      setStatusUpdating(false);
    }
  };

  const handleBlockIp = async (ip: string) => {
    if (!ip) return;
    setIsIpProcessing(true);
    try {
      await api.blockIp(ip, `Quarantined from Threat #${threatId.slice(0, 8)}`);
      setIpActionMsg({ text: `IP [${ip}] permanently blacklisted & quarantined in firewall!`, type: "success" });
      setTimeout(() => setIpActionMsg(null), 4000);
    } catch (err: any) {
      setIpActionMsg({ text: err.message || "Failed to block IP", type: "error" });
      setTimeout(() => setIpActionMsg(null), 4000);
    } finally {
      setIsIpProcessing(false);
    }
  };

  const handleTrustIp = async (ip: string) => {
    if (!ip) return;
    setIsIpProcessing(true);
    try {
      await api.whitelistIp(ip);
      setIpActionMsg({ text: `IP [${ip}] added to trusted whitelist.`, type: "success" });
      setTimeout(() => setIpActionMsg(null), 4000);
    } catch (err: any) {
      setIpActionMsg({ text: err.message || "Failed to trust IP", type: "error" });
      setTimeout(() => setIpActionMsg(null), 4000);
    } finally {
      setIsIpProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-zinc-200 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center font-mono text-xs text-zinc-500">
          Loading threat mathematical forensics from PostgreSQL...
        </div>
      </div>
    );
  }

  if (!threat) {
    return (
      <div className="min-h-screen bg-background text-zinc-200 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <ShieldAlert className="w-12 h-12 text-red-500 mb-4" />
          <h2 className="text-lg font-bold">Threat Incident Not Found</h2>
          <p className="text-xs text-zinc-400 mt-1 font-mono">Threat ID {threatId} does not exist in database.</p>
          <Link
            href="/threats"
            className="mt-4 px-4 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-200 text-xs font-mono"
          >
            Back to Threats
          </Link>
        </div>
      </div>
    );
  }

  const breakdown = threat.evidence?.risk_breakdown || {
    formula: "Risk = 0.30·Deviation + 0.25·VerificationFail + 0.20·Anomaly + 0.15·Frequency + 0.10·HashMismatch",
    factors: {
      deviation: { score: 85, weight: 0.3, weighted: 25.5 },
      verification: { score: 100, weight: 0.25, weighted: 25.0 },
      anomaly: { score: 70, weight: 0.2, weighted: 14.0 },
      frequency: { score: 50, weight: 0.15, weighted: 7.5 },
      hash_mismatch: { score: 80, weight: 0.1, weighted: 8.0 },
    },
  };
  const factors = breakdown?.factors || {};

  const sourceIp = threat.evidence?.source_ip || (threat.evidence?.primary_evidence as any)?.source_ip || "10.0.1.10";

  return (
    <div className="min-h-screen flex flex-col bg-background text-zinc-200">
      <Navbar />

      <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* IP Action Notification Banner */}
        {ipActionMsg && (
          <div
            className={`p-3.5 rounded-xl border text-xs font-mono flex items-center gap-2 transition-all ${
              ipActionMsg.type === "success"
                ? "bg-emerald-950/80 border-emerald-600 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
                : "bg-red-950/80 border-red-600 text-red-300 shadow-[0_0_15px_rgba(239,68,68,0.2)]"
            }`}
          >
            {ipActionMsg.type === "success" ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-red-400" />}
            <span>{ipActionMsg.text}</span>
          </div>
        )}

        {/* Top Breadcrumb & Actions */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/threats"
              className="p-2 rounded-lg bg-card hover:bg-card-hover border border-border text-zinc-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-lg font-bold text-white tracking-wide uppercase font-mono">{threat.threat_type}</h1>
                <SeverityBadge severity={threat.severity} />
                <StatusBadge status={threat.status} />
              </div>
              <p className="text-xs text-zinc-400 font-mono mt-0.5">Threat Incident ID: {threat.threat_id}</p>
            </div>
          </div>

          {/* IPS Defense Actions & Status Controls */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Quick IPS Defense Buttons */}
            <button
              onClick={() => handleBlockIp(sourceIp)}
              disabled={isIpProcessing}
              title={`Permanently block IP ${sourceIp} in Firewall`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950/70 hover:bg-red-900 border border-red-800 text-red-300 text-xs font-mono font-bold transition-all disabled:opacity-50"
            >
              <Ban className="w-3.5 h-3.5" />
              <span>Block IP ({sourceIp})</span>
            </button>
            <button
              onClick={() => handleTrustIp(sourceIp)}
              disabled={isIpProcessing}
              title={`Add IP ${sourceIp} to trusted Whitelist`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/70 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 text-xs font-mono font-bold transition-all disabled:opacity-50"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Trust / Whitelist IP</span>
            </button>

            {statusMsg && <span className="text-xs font-mono text-emerald-400 mr-1">{statusMsg}</span>}
            <select
              value={threat.status}
              disabled={statusUpdating}
              onChange={(e) => handleUpdateStatus(e.target.value)}
              className="px-3 py-1.5 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-200 font-mono focus:border-zinc-500 focus:outline-none"
            >
              <option value="open">Open</option>
              <option value="investigating">Under Investigation</option>
              <option value="resolved">Resolved</option>
              <option value="false_positive">False Positive</option>
            </select>
          </div>
        </div>

        {/* Core Metadata Card */}
        <div className="p-5 rounded-xl bg-card border border-border shadow-card grid grid-cols-2 sm:grid-cols-5 gap-4 font-mono text-xs">
          <div>
            <span className="text-zinc-500 block text-[10px] uppercase">Detection Rule</span>
            <span className="text-zinc-200 font-semibold">{threat.detection_rule}</span>
          </div>
          <div>
            <span className="text-zinc-500 block text-[10px] uppercase">Confidence</span>
            <span className="text-white font-bold">{(threat.confidence * 100).toFixed(1)}%</span>
          </div>
          <div>
            <span className="text-zinc-500 block text-[10px] uppercase">Detected Timestamp</span>
            <span className="text-white">{formatDateTime(threat.detected_at)}</span>
          </div>
          <div>
            <span className="text-zinc-500 block text-[10px] uppercase">Source Node</span>
            <span className="text-zinc-300 truncate block">
              {threat.source_node || threat.session_id || "--"}
            </span>
          </div>
          <div>
            <span className="text-zinc-500 block text-[10px] uppercase">Source IP Address</span>
            <span className="text-amber-300 font-bold block">
              {sourceIp}
            </span>
          </div>
        </div>

        {/* Mathematical Risk Score Breakdown Section */}
        <div className="p-6 rounded-xl bg-card border border-border shadow-card space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-zinc-400" />
              <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
                Explainable Mathematical Risk Score: <span className="text-white text-sm font-bold">{threat.risk_score} / 100</span>
              </h3>
            </div>
            <span className="text-xs font-mono text-zinc-400">
              Severity: <strong className="uppercase text-white">{threat.severity}</strong>
            </span>
          </div>

          {breakdown && (
            <div className="space-y-4">
              <div className="p-3 bg-zinc-950/80 rounded-lg border border-border font-mono text-xs text-zinc-300">
                <span className="text-zinc-500 block text-[10px] uppercase mb-1">Mathematical Formula:</span>
                <code className="text-zinc-200">{breakdown.formula}</code>
              </div>

              {/* Factors Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 font-mono text-xs">
                {Object.entries(factors).map(([k, v]: [string, any]) => (
                  <div key={k} className="p-3.5 bg-zinc-950/80 rounded-lg border border-border space-y-1">
                    <span className="text-zinc-400 block text-[10px] uppercase font-bold truncate">
                      {k.replace("_", " ")}
                    </span>
                    <div className="flex items-baseline justify-between pt-1">
                      <span className="text-xs text-zinc-500">Weight: {(v.weight * 100).toFixed(0)}%</span>
                      <span className="text-sm font-bold text-white">{v.weighted} pts</span>
                    </div>
                    <div className="text-[10px] text-zinc-400">Raw Score: {v.score}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Two Columns: Quantum Measurement Analysis (Left) & Blockchain Audit Ledger (Right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Quantum & Statistical Telemetry */}
          <div className="lg:col-span-6 space-y-6">
            <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-border">
                <Atom className="w-5 h-5 text-zinc-400" />
                <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
                  Quantum Analysis & Telemetry
                </h3>
              </div>

              {threat.quantum_analysis ? (
                <div className="space-y-4 font-mono text-xs">
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                      <span className="text-zinc-500 block text-[10px]">EXPECTED</span>
                      <span className="text-sm font-bold text-white">
                        {threat.quantum_analysis.expected_measurement?.toFixed(4) ?? "--"}
                      </span>
                    </div>
                    <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                      <span className="text-zinc-500 block text-[10px]">OBSERVED</span>
                      <span className="text-sm font-bold text-white">
                        {threat.quantum_analysis.observed_measurement?.toFixed(4) ?? "--"}
                      </span>
                    </div>
                    <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                      <span className="text-zinc-500 block text-[10px]">DEVIATION</span>
                      <span
                        className={`text-sm font-bold ${
                          (threat.quantum_analysis.deviation_ratio ?? 0) > 0.3
                            ? "text-red-400"
                            : "text-emerald-400"
                        }`}
                      >
                        {formatPercent(threat.quantum_analysis.deviation_percentage)}
                      </span>
                    </div>
                  </div>

                  {threat.quantum_analysis.quantum_state && (
                    <div className="p-3 bg-zinc-950/80 rounded-lg border border-border text-[11px] text-zinc-300">
                      <span className="text-zinc-500 block text-[10px] mb-1">STATE DESCRIPTION:</span>
                      {threat.quantum_analysis.quantum_state}
                    </div>
                  )}

                  {threat.quantum_analysis.signature_hash && (
                    <div className="p-3 bg-zinc-950/80 rounded-lg border border-border text-[11px] text-zinc-300 break-all">
                      <span className="text-zinc-500 block text-[10px] mb-1">SIGNATURE SHA-256 HASH:</span>
                      <code className="text-zinc-200">{threat.quantum_analysis.signature_hash}</code>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-xs font-mono text-zinc-500 py-4 text-center">
                  No quantum telemetry associated with this event.
                </div>
              )}
            </div>

            {/* Statistical Z-Score Card */}
            {threat.statistical_analysis && (
              <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
                <div className="flex items-center gap-2 pb-3 border-b border-border">
                  <Activity className="w-5 h-5 text-zinc-400" />
                  <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
                    Statistical Baseline Analysis
                  </h3>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs text-center">
                  <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                    <span className="text-zinc-500 block text-[10px]">SAMPLES</span>
                    <span className="text-sm font-bold text-white">
                      {threat.statistical_analysis.sample_size}
                    </span>
                  </div>
                  <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                    <span className="text-zinc-500 block text-[10px]">MEAN DEV</span>
                    <span className="text-sm font-bold text-white">
                      {threat.statistical_analysis.mean_deviation.toFixed(4)}
                    </span>
                  </div>
                  <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                    <span className="text-zinc-500 block text-[10px]">STD DEV (σ)</span>
                    <span className="text-sm font-bold text-white">
                      {threat.statistical_analysis.std_deviation.toFixed(4)}
                    </span>
                  </div>
                  <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                    <span className="text-zinc-500 block text-[10px]">Z-SCORE</span>
                    <span
                      className={`text-sm font-bold ${
                        Math.abs(threat.statistical_analysis.z_score) > 2.5
                          ? "text-red-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {threat.statistical_analysis.z_score.toFixed(2)}σ
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right: Tamper-Evident Blockchain Audit Ledger Block */}
          <div className="lg:col-span-6 space-y-6">
            <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <Lock className="w-5 h-5 text-emerald-400" />
                  <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
                    Audit Ledger Evidence Block
                  </h3>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-900 text-emerald-400 border border-zinc-800">
                  CRYPTOGRAPHIC BLOCK
                </span>
              </div>

              {threat.audit_block ? (
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 bg-zinc-950/80 rounded-lg border border-border flex items-center justify-between">
                    <span className="text-zinc-400">Block Index:</span>
                    <span className="font-bold text-white">#{threat.audit_block.block_index}</span>
                  </div>

                  <div className="p-3 bg-zinc-950/80 rounded-lg border border-border space-y-1 break-all">
                    <span className="text-zinc-500 block text-[10px]">BLOCK HASH (SHA-256):</span>
                    <code className="text-emerald-400 text-[11px]">{threat.audit_block.block_hash}</code>
                  </div>

                  <div className="p-3 bg-zinc-950/80 rounded-lg border border-border space-y-1 break-all">
                    <span className="text-zinc-500 block text-[10px]">PREVIOUS BLOCK HASH:</span>
                    <code className="text-zinc-400 text-[11px]">{threat.audit_block.previous_hash}</code>
                  </div>

                  <div className="p-3 bg-zinc-950/80 rounded-lg border border-border space-y-1 break-all">
                    <span className="text-zinc-500 block text-[10px]">EVENT PAYLOAD HASH:</span>
                    <code className="text-zinc-400 text-[11px]">{threat.audit_block.payload_hash}</code>
                  </div>

                  <div className="p-3 bg-zinc-950/80 rounded-lg border border-border flex items-center justify-between text-zinc-400 text-[11px]">
                    <span>Block Timestamp:</span>
                    <span>{formatDateTime(threat.audit_block.timestamp)}</span>
                  </div>
                </div>
              ) : (
                <div className="text-xs font-mono text-zinc-500 py-6 text-center">
                  No blockchain audit block recorded for this threat event.
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
