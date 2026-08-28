"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Lock,
  Unlock,
  AlertTriangle,
  Flame,
  Zap,
  Globe,
  Radio,
  RefreshCw,
  Ban,
  CheckCircle,
  Eye,
  Key,
  Server,
  Layers,
  Terminal,
  Clock,
  ArrowUpRight,
} from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { api } from "@/lib/api";

export default function SecurityCenterPage() {
  const [loading, setLoading] = useState(true);
  const [secData, setSecData] = useState<any>(null);
  const [threatActors, setThreatActors] = useState<any[]>([]);
  const [honeypotData, setHoneypotData] = useState<any>(null);
  const [blockIpInput, setBlockIpInput] = useState("");
  const [blockReasonInput, setBlockReasonInput] = useState("");
  const [whitelistInput, setWhitelistInput] = useState("");
  const [actionMsg, setActionMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const fetchSecurityData = useCallback(async () => {
    try {
      const [statusRes, actorsRes, hpRes] = await Promise.all([
        api.getSecurityStatus(),
        api.getThreatActors().catch(() => ({ actors: [] })),
        api.getHoneypotStatus().catch(() => ({ total_trapped: 0, recent_hits: [] })),
      ]);
      setSecData(statusRes);
      setThreatActors(actorsRes.actors || []);
      setHoneypotData(hpRes);
    } catch (err) {
      console.error("Failed to load security telemetry:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSecurityData();
    const interval = setInterval(fetchSecurityData, 4000);
    return () => clearInterval(interval);
  }, [fetchSecurityData]);

  const showNotification = (text: string, type: "success" | "error" = "success") => {
    setActionMsg({ text, type });
    setTimeout(() => setActionMsg(null), 4000);
  };

  const handleManualBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!blockIpInput.trim()) return;
    setIsProcessing(true);
    try {
      await api.blockIp(blockIpInput.trim(), blockReasonInput.trim() || "Manual SOC Quarantine");
      showNotification(`IP [${blockIpInput.trim()}] permanently blacklisted & blocked!`);
      setBlockIpInput("");
      setBlockReasonInput("");
      await fetchSecurityData();
    } catch (err: any) {
      showNotification(err.message || "Failed to block IP", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUnblock = async (ip: string) => {
    setIsProcessing(true);
    try {
      await api.unblockIp(ip);
      showNotification(`IP [${ip}] unblocked successfully.`);
      await fetchSecurityData();
    } catch (err: any) {
      showNotification(err.message || "Failed to unblock IP", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleWhitelist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!whitelistInput.trim()) return;
    setIsProcessing(true);
    try {
      await api.whitelistIp(whitelistInput.trim());
      showNotification(`IP [${whitelistInput.trim()}] added to trusted whitelist.`);
      setWhitelistInput("");
      await fetchSecurityData();
    } catch (err: any) {
      showNotification(err.message || "Failed to whitelist IP", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleToggleLockdown = async () => {
    if (!secData) return;
    const currentMode = secData.layers?.layer_1_ip_firewall?.lockdown_mode;
    setIsProcessing(true);
    try {
      await api.toggleLockdown(!currentMode);
      showNotification(
        !currentMode
          ? "🚨 EMERGENCY LOCKDOWN ACTIVATED: All external untrusted traffic blocked!"
          : "Emergency Lockdown Deactivated. Resumed normal filtering."
      );
      await fetchSecurityData();
    } catch (err: any) {
      showNotification(err.message || "Failed to toggle lockdown", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleResetCircuitBreaker = async () => {
    setIsProcessing(true);
    try {
      await api.resetCircuitBreaker();
      showNotification("Circuit Breaker reset. Normal detection tolerance restored.");
      await fetchSecurityData();
    } catch (err: any) {
      showNotification(err.message || "Failed to reset circuit breaker", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const isLockdown = secData?.layers?.layer_1_ip_firewall?.lockdown_mode;
  const isCircuitBreaker = secData?.layers?.layer_6_autonomous_prevention?.circuit_breaker_active;
  const blacklistedList = secData?.layers?.layer_1_ip_firewall?.blacklisted_ips || [];
  const suspectList = secData?.layers?.layer_1_ip_firewall?.suspect_ips || [];
  const rateLimitBans = secData?.layers?.layer_2_rate_limiter?.active_bans || [];

  return (
    <div className="min-h-screen bg-[#070709] text-zinc-100 flex flex-col font-sans">
      <Navbar wsConnected={true} onRefresh={fetchSecurityData} />

      <main className="flex-1 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Banner Alert if in Lockdown / Circuit Breaker */}
        {isLockdown && (
          <div className="p-4 rounded-xl bg-red-950/80 border border-red-600/80 flex items-center justify-between animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.3)]">
            <div className="flex items-center gap-3">
              <ShieldAlert className="w-6 h-6 text-red-400" />
              <div>
                <h3 className="text-sm font-bold text-red-200 tracking-wide">
                  🚨 EMERGENCY SOC LOCKDOWN IS ACTIVE
                </h3>
                <p className="text-xs text-red-300">
                  All non-whitelisted ingress traffic is actively rejected at Layer 1 firewall.
                </p>
              </div>
            </div>
            <button
              onClick={handleToggleLockdown}
              disabled={isProcessing}
              className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold tracking-wider transition-all"
            >
              DISENGAGE LOCKDOWN
            </button>
          </div>
        )}

        {/* Action Notification Toast */}
        {actionMsg && (
          <div
            className={`p-3 rounded-lg border text-xs font-mono flex items-center gap-2 transition-all ${
              actionMsg.type === "success"
                ? "bg-emerald-950/80 border-emerald-600/60 text-emerald-300"
                : "bg-red-950/80 border-red-600/60 text-red-300"
            }`}
          >
            {actionMsg.type === "success" ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            <span>{actionMsg.text}</span>
          </div>
        )}

        {/* TOP ROW: DEFCON Threat Level Bar & Master Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* DEFCON Threat Level Card */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-zinc-900/70 border border-zinc-800/80 relative overflow-hidden backdrop-blur-xl flex flex-col justify-between">
            <div className="absolute top-0 right-0 w-72 h-72 bg-gradient-to-bl from-zinc-800/20 to-transparent rounded-full blur-3xl pointer-events-none" />

            <div>
              <div className="flex items-center justify-between pb-3 border-b border-zinc-800/80">
                <div className="flex items-center gap-2">
                  <Flame className="w-5 h-5 text-amber-400" />
                  <span className="text-xs font-bold uppercase tracking-widest text-zinc-400 font-mono">
                    SOC DEFCON POSTURE
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  <span>REAL-TIME HEURISTICS</span>
                </div>
              </div>

              <div className="mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
                    {secData?.threat_level || "DEFCON 5: NORMAL SECURE"}
                  </h1>
                  <p className="text-xs text-zinc-400 mt-1 max-w-xl">
                    Multi-layer active defense enforcing strict deterministic policy across 14 quantum detection rules, IP firewall, rate limiting, and autonomous countermeasures.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold tracking-wider uppercase border ${
                      secData?.threat_score === 1
                        ? "bg-red-950/80 border-red-500 text-red-300 shadow-[0_0_15px_rgba(239,68,68,0.4)] animate-pulse"
                        : secData?.threat_score === 2
                        ? "bg-orange-950/80 border-orange-500 text-orange-300"
                        : secData?.threat_score === 3
                        ? "bg-amber-950/80 border-amber-500 text-amber-300"
                        : "bg-emerald-950/80 border-emerald-500/60 text-emerald-300"
                    }`}
                  >
                    STATUS: {secData?.threat_color?.toUpperCase() || "GREEN"}
                  </span>
                </div>
              </div>
            </div>

            {/* Defense Health Indicators */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-4 border-t border-zinc-800/80">
              <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800">
                <div className="text-[10px] text-zinc-500 font-mono uppercase">L1 Firewall</div>
                <div className="text-sm font-semibold text-emerald-400 flex items-center gap-1 mt-0.5">
                  <ShieldCheck className="w-3.5 h-3.5" /> Enforcing
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800">
                <div className="text-[10px] text-zinc-500 font-mono uppercase">L2 Rate Limiter</div>
                <div className="text-sm font-semibold text-emerald-400 flex items-center gap-1 mt-0.5">
                  <Zap className="w-3.5 h-3.5" /> 30 req/min
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800">
                <div className="text-[10px] text-zinc-500 font-mono uppercase">L4 Validator</div>
                <div className="text-sm font-semibold text-emerald-400 flex items-center gap-1 mt-0.5">
                  <Terminal className="w-3.5 h-3.5" /> Entropy & SQLi
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800">
                <div className="text-[10px] text-zinc-500 font-mono uppercase">L5 Quantum IPS</div>
                <div className="text-sm font-semibold text-emerald-400 flex items-center gap-1 mt-0.5">
                  <Radio className="w-3.5 h-3.5" /> Drop & Quarantine
                </div>
              </div>
            </div>
          </div>

          {/* Master Emergency Controls */}
          <div className="p-6 rounded-2xl bg-zinc-900/70 border border-zinc-800/80 backdrop-blur-xl flex flex-col justify-between space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800/80">
              <span className="text-xs font-bold uppercase tracking-widest text-zinc-400 font-mono flex items-center gap-2">
                <Lock className="w-4 h-4 text-zinc-300" />
                SOAR EMERGENCY ACTIONS
              </span>
            </div>

            <div className="space-y-3">
              {/* Emergency Lockdown Toggle */}
              <button
                onClick={handleToggleLockdown}
                disabled={isProcessing}
                className={`w-full py-3 px-4 rounded-xl text-xs font-bold tracking-wider uppercase transition-all flex items-center justify-center gap-2 border ${
                  isLockdown
                    ? "bg-zinc-800 hover:bg-zinc-700 border-zinc-600 text-white"
                    : "bg-red-600 hover:bg-red-500 border-red-500 text-white shadow-[0_0_15px_rgba(239,68,68,0.3)]"
                }`}
              >
                {isLockdown ? (
                  <>
                    <Unlock className="w-4 h-4" /> DISENGAGE EMERGENCY LOCKDOWN
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4" /> ENGAGE EMERGENCY LOCKDOWN
                  </>
                )}
              </button>

              {/* Circuit Breaker Reset */}
              {isCircuitBreaker && (
                <button
                  onClick={handleResetCircuitBreaker}
                  disabled={isProcessing}
                  className="w-full py-2.5 px-4 rounded-xl bg-amber-600 hover:bg-amber-500 border border-amber-500 text-zinc-950 font-bold text-xs tracking-wider uppercase transition-all flex items-center justify-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" /> RESET TRIPPED CIRCUIT BREAKER
                </button>
              )}

              <p className="text-[11px] text-zinc-500 font-mono text-center">
                Lockdown immediately drops all incoming network traffic outside the trusted whitelist.
              </p>
            </div>

            {/* Quick Metrics */}
            <div className="pt-3 border-t border-zinc-800/80 grid grid-cols-2 gap-2 text-center">
              <div className="p-2 rounded bg-zinc-950/60 border border-zinc-850">
                <span className="text-[10px] text-zinc-500 font-mono block">BLOCKED ATTACKS</span>
                <span className="text-base font-bold text-red-400">
                  {(secData?.layers?.layer_1_ip_firewall?.total_blocked || 0) +
                    (secData?.layers?.layer_2_rate_limiter?.total_rate_limited || 0)}
                </span>
              </div>
              <div className="p-2 rounded bg-zinc-950/60 border border-zinc-850">
                <span className="text-[10px] text-zinc-500 font-mono block">QUARANTINED</span>
                <span className="text-base font-bold text-amber-400">
                  {blacklistedList.length + (secData?.layers?.layer_5_quantum_ips?.total_quarantined_nodes || 0)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 6-LAYER SECURITY MATRIX CARDS */}
        <div>
          <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
            <Layers className="w-4 h-4 text-zinc-400" />
            6-LAYER ACTIVE DEFENSE ARCHITECTURE
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Layer 1: IP Firewall */}
            <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-zinc-700 transition-all">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <span className="text-xs font-mono text-zinc-400 font-bold">LAYER 1: IP FIREWALL</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono">
                  ACTIVE
                </span>
              </div>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Checked Packets:</span>
                  <span className="font-mono text-white">{secData?.layers?.layer_1_ip_firewall?.total_checked || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Firewall Dropped:</span>
                  <span className="font-mono text-red-400 font-semibold">{secData?.layers?.layer_1_ip_firewall?.total_blocked || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Blacklisted IPs:</span>
                  <span className="font-mono text-amber-400">{blacklistedList.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Lockdown Status:</span>
                  <span className={`font-mono font-bold ${isLockdown ? "text-red-400" : "text-emerald-400"}`}>
                    {isLockdown ? "ENGAGED" : "STANDBY"}
                  </span>
                </div>
              </div>
            </div>

            {/* Layer 2: Rate Limiter */}
            <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-zinc-700 transition-all">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <span className="text-xs font-mono text-zinc-400 font-bold">LAYER 2: RATE LIMITER</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono">
                  ACTIVE
                </span>
              </div>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Rate Limit Policy:</span>
                  <span className="font-mono text-zinc-300">30 req / min / IP</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Throttled Requests:</span>
                  <span className="font-mono text-red-400 font-semibold">{secData?.layers?.layer_2_rate_limiter?.total_rate_limited || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Active Auto-Bans:</span>
                  <span className="font-mono text-amber-400">{rateLimitBans.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Backoff Algorithm:</span>
                  <span className="font-mono text-zinc-300">Exponential (15m-24h)</span>
                </div>
              </div>
            </div>

            {/* Layer 3: API Key Auth */}
            <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-zinc-700 transition-all">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <span className="text-xs font-mono text-zinc-400 font-bold">LAYER 3: API AUTH</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono">
                  HMAC-SHA256
                </span>
              </div>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Active API Keys:</span>
                  <span className="font-mono text-white">{secData?.layers?.layer_3_api_auth?.active_keys || 1}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Auth Failures:</span>
                  <span className="font-mono text-red-400">{secData?.layers?.layer_3_api_auth?.total_auth_failures || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Localhost Bypass:</span>
                  <span className="font-mono text-emerald-400">ENABLED (Dev)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Key Rotation:</span>
                  <span className="font-mono text-zinc-300">Supported</span>
                </div>
              </div>
            </div>

            {/* Layer 4: Deep Payload Validator */}
            <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-zinc-700 transition-all">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <span className="text-xs font-mono text-zinc-400 font-bold">LAYER 4: SANITIZER & ENTROPY</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono">
                  INSPECTION
                </span>
              </div>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Validated Ingress:</span>
                  <span className="font-mono text-white">{secData?.layers?.layer_4_payload_validator?.total_validated || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Exploit/Fuzz Rejected:</span>
                  <span className="font-mono text-red-400 font-semibold">{secData?.layers?.layer_4_payload_validator?.total_rejected || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Entropy Analysis:</span>
                  <span className="font-mono text-emerald-400">Shannon Threshold 5.8</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Injection Filters:</span>
                  <span className="font-mono text-zinc-300">SQLi, XSS, Cmd, Travers</span>
                </div>
              </div>
            </div>

            {/* Layer 5: Quantum IPS */}
            <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-zinc-700 transition-all">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <span className="text-xs font-mono text-zinc-400 font-bold">LAYER 5: QUANTUM IPS</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono">
                  ENFORCING
                </span>
              </div>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Quarantined Nodes:</span>
                  <span className="font-mono text-amber-400 font-semibold">{secData?.layers?.layer_5_quantum_ips?.total_quarantined_nodes || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Revoked Sessions:</span>
                  <span className="font-mono text-red-400">{secData?.layers?.layer_5_quantum_ips?.total_revoked_sessions || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Tainted Hashes:</span>
                  <span className="font-mono text-zinc-300">{secData?.layers?.layer_5_quantum_ips?.total_blacklisted_hashes || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Decoherence Reset:</span>
                  <span className="font-mono text-emerald-400">Automated</span>
                </div>
              </div>
            </div>

            {/* Layer 6: Autonomous Prevention */}
            <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-zinc-700 transition-all">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <span className="text-xs font-mono text-zinc-400 font-bold">LAYER 6: 14-RULE ENGINE</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono">
                  HEURISTIC & AI
                </span>
              </div>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Active Rule Count:</span>
                  <span className="font-mono text-emerald-400 font-bold">14 RULES LOADED</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Adaptive Thresholds:</span>
                  <span className={`font-mono ${secData?.layers?.layer_6_autonomous_prevention?.adaptive_mode_active ? "text-amber-400 font-bold" : "text-zinc-300"}`}>
                    {secData?.layers?.layer_6_autonomous_prevention?.adaptive_mode_active ? "TIGHTENED (Under Attack)" : "Standard Baseline"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Circuit Breaker:</span>
                  <span className={`font-mono font-semibold ${isCircuitBreaker ? "text-red-400" : "text-emerald-400"}`}>
                    {isCircuitBreaker ? "TRIPPED" : "NOMINAL"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Correlation Engine:</span>
                  <span className="font-mono text-zinc-300">Multi-Vector Linked</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* MIDDLE SECTION: IP Management & Live Honeypot Telemetry */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* IP Quarantine & Blacklist Manager */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-zinc-900/70 border border-zinc-800/80 backdrop-blur-xl">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <div className="flex items-center gap-2">
                <Ban className="w-5 h-5 text-red-400" />
                <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-white">
                  IP FIREWALL BLACKLIST & QUARANTINE ({blacklistedList.length})
                </h3>
              </div>
            </div>

            {/* Quick Actions Form: Manual Block & Whitelist */}
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 pb-4 border-b border-zinc-800/60">
              <form onSubmit={handleManualBlock} className="space-y-2">
                <span className="text-[11px] font-mono text-zinc-400 uppercase font-bold">Manual IP Quarantine</span>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="e.g. 192.168.1.100"
                    value={blockIpInput}
                    onChange={(e) => setBlockIpInput(e.target.value)}
                    className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-red-500 font-mono"
                  />
                  <button
                    type="submit"
                    disabled={isProcessing}
                    className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-semibold tracking-wider font-mono transition-all"
                  >
                    BLOCK
                  </button>
                </div>
              </form>

              <form onSubmit={handleWhitelist} className="space-y-2">
                <span className="text-[11px] font-mono text-zinc-400 uppercase font-bold">Add Whitelist Operator IP</span>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="e.g. 10.0.0.5"
                    value={whitelistInput}
                    onChange={(e) => setWhitelistInput(e.target.value)}
                    className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500 font-mono"
                  />
                  <button
                    type="submit"
                    disabled={isProcessing}
                    className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg text-xs font-semibold tracking-wider font-mono transition-all"
                  >
                    TRUST
                  </button>
                </div>
              </form>
            </div>

            {/* Blacklist Table */}
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-500">
                    <th className="pb-2">IP ADDRESS</th>
                    <th className="pb-2">BAN REASON</th>
                    <th className="pb-2">REPUTATION</th>
                    <th className="pb-2">ATTACK PROFILE</th>
                    <th className="pb-2 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-850">
                  {blacklistedList.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-zinc-600">
                        No actively blacklisted IPs. Ingress perimeter is clean.
                      </td>
                    </tr>
                  ) : (
                    blacklistedList.map((bl: any, i: number) => (
                      <tr key={i} className="hover:bg-zinc-800/40 transition-colors">
                        <td className="py-2.5 font-bold text-red-400">{bl.ip}</td>
                        <td className="py-2.5 text-zinc-300 max-w-[200px] truncate">{bl.reason}</td>
                        <td className="py-2.5">
                          <span className="px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-800/60">
                            {bl.reputation_at_ban || 0.0} / 100
                          </span>
                        </td>
                        <td className="py-2.5 text-zinc-400">
                          {Object.keys(bl.attack_types || {}).join(", ") || "Active Breach Attempt"}
                        </td>
                        <td className="py-2.5 text-right">
                          <button
                            onClick={() => handleUnblock(bl.ip)}
                            disabled={isProcessing}
                            className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 hover:text-white border border-zinc-700 text-[11px] transition-all"
                          >
                            Unblock
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Decoy Honeypot Trap Telemetry */}
          <div className="p-6 rounded-2xl bg-zinc-900/70 border border-zinc-800/80 backdrop-blur-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
                <div className="flex items-center gap-2">
                  <Eye className="w-5 h-5 text-amber-400" />
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-white">
                    DECEPTION HONEYPOT TRAPS
                  </h3>
                </div>
                <span className="text-xs font-mono text-amber-400 font-bold">
                  {honeypotData?.total_trapped || 0} TRAPPED
                </span>
              </div>

              <div className="mt-4 space-y-3">
                <p className="text-xs text-zinc-400">
                  Active decoys simulate vulnerable legacy endpoints. Attackers probing these endpoints are immediately blacklisted and tarpitted.
                </p>

                <div className="p-3 rounded-lg bg-zinc-950/70 border border-zinc-800 space-y-1 text-xs font-mono">
                  <div className="text-zinc-500 font-bold uppercase text-[10px]">Active Decoy Routes:</div>
                  <div className="text-zinc-300">/api/security/v1/legacy/events</div>
                  <div className="text-zinc-300">/api/security/qkd/admin/key-export</div>
                </div>

                {/* Recent Trapped Probes */}
                <div className="mt-3 space-y-2">
                  <span className="text-[10px] font-mono uppercase text-zinc-500 block">Recent Trapped Probes:</span>
                  {(honeypotData?.recent_hits || []).length === 0 ? (
                    <div className="text-xs font-mono text-zinc-600 py-3 text-center">
                      No attackers trapped recently.
                    </div>
                  ) : (
                    (honeypotData?.recent_hits || []).slice(-3).map((hit: any, idx: number) => (
                      <div key={idx} className="p-2.5 rounded bg-zinc-950/80 border border-zinc-850 text-xs font-mono space-y-1">
                        <div className="flex justify-between items-center text-red-400 font-bold">
                          <span>{hit.client_ip}</span>
                          <span className="text-[10px] text-zinc-500">{new Date(hit.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <div className="text-zinc-400 text-[11px] truncate">{hit.trap_name}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-zinc-800/80 text-[11px] text-zinc-500 font-mono flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Zero-Tolerance Auto-Blacklist Enforced</span>
            </div>
          </div>
        </div>

        {/* BOTTOM ROW: Threat Actor Intelligence Profile Correlation */}
        <div className="p-6 rounded-2xl bg-zinc-900/70 border border-zinc-800/80 backdrop-blur-xl">
          <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
            <div className="flex items-center gap-2">
              <Server className="w-5 h-5 text-indigo-400" />
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-white">
                CORRELATED THREAT ACTOR INTELLIGENCE ({threatActors.length} TRACKED)
              </h3>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {threatActors.length === 0 ? (
              <div className="col-span-full py-8 text-center text-zinc-600 font-mono text-xs">
                No active threat actor profiles recorded. Perimeter secure.
              </div>
            ) : (
              threatActors.map((actor, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 space-y-2 text-xs font-mono">
                  <div className="flex justify-between items-center pb-1.5 border-b border-zinc-850">
                    <span className="font-bold text-indigo-300">{actor.actor_id}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                        actor.highest_severity === "critical"
                          ? "bg-red-950 text-red-400 border border-red-800"
                          : actor.highest_severity === "high"
                          ? "bg-orange-950 text-orange-400 border border-orange-800"
                          : "bg-amber-950 text-amber-400 border border-amber-800"
                      }`}
                    >
                      {actor.highest_severity}
                    </span>
                  </div>
                  <div className="space-y-1 text-zinc-400 text-[11px]">
                    <div className="flex justify-between">
                      <span>Total Attack Count:</span>
                      <span className="font-bold text-white">{actor.total_attacks}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Highest Risk Score:</span>
                      <span className="font-bold text-red-400">{actor.highest_risk_score} / 100</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Associated IPs:</span>
                      <span className="text-zinc-300 truncate max-w-[140px]">
                        {actor.associated_ips?.join(", ") || "None"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Contained Status:</span>
                      <span className={actor.is_contained ? "text-emerald-400 font-semibold" : "text-amber-400"}>
                        {actor.is_contained ? "ISOLATED & BLOCKED" : "MONITORING"}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
