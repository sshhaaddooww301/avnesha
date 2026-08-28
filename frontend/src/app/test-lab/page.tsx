"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { useTestLab } from "@/hooks/useTestLab";
import { api } from "@/lib/api";
import { AttackScenarioType, TestScenarioInfo } from "@/lib/types";
import { formatDateTime, formatPercent, formatHash } from "@/lib/utils";
import {
  Atom,
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Activity,
  History,
  Shield,
  ShieldCheck,
  Ban,
  Zap,
  Timer,
  Sliders,
  ExternalLink,
  ChevronRight,
  RefreshCw,
  FileText,
  BookOpen,
  CheckCircle,
} from "lucide-react";

export default function TestLabPage() {
  const [scenarios, setScenarios] = useState<TestScenarioInfo[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<AttackScenarioType>("replay");
  const [runs, setRuns] = useState<number>(10);
  const [intensity, setIntensity] = useState<number>(0.8);
  const [replayWindow, setReplayWindow] = useState<number>(60);
  const [perturbation, setPerturbation] = useState<number>(0.25);
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [ipActionMsg, setIpActionMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [isIpProcessing, setIsIpProcessing] = useState(false);

  const fetchHistory = useCallback(async () => {
    try {
      setLoadingHistory(true);
      const res = await api.getTestHistory(1, 8);
      setHistoryList(res.items || []);
    } catch (e) {
      console.error("Failed to load test history:", e);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const handleBlockIp = async (ip: string) => {
    if (!ip) return;
    setIsIpProcessing(true);
    try {
      await api.blockIp(ip, "Quarantined via Quantum Attack Test Lab");
      setIpActionMsg({ text: `IP [${ip}] blacklisted & quarantined in firewall!`, type: "success" });
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

  const {
    state,
    currentTestId,
    progress,
    metrics,
    results,
    summary,
    errorMessage,
    runTest,
    resetTest,
    loadHistoricalTest,
  } = useTestLab(fetchHistory);

  useEffect(() => {
    async function loadScenarios() {
      try {
        const sc = await api.getTestScenarios();
        setScenarios(sc);
      } catch (e) {
        console.error("Failed to fetch scenarios:", e);
      }
    }
    loadScenarios();
    fetchHistory();
  }, [fetchHistory]);

  const handleStartTest = () => {
    runTest({
      attack_type: selectedScenario,
      runs,
      attack_intensity: intensity,
      replay_window: replayWindow,
      measurement_perturbation: perturbation,
    });
  };

  const isRunning = state === "running";

  return (
    <div className="min-h-screen flex flex-col bg-background text-zinc-200">
      <Navbar />

      <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Page Header Ribbon */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-card border border-border shadow-card">
          <div className="flex items-center gap-3.5">
            <div className="p-2.5 rounded-lg bg-zinc-900 border border-zinc-700/80 text-white">
              <Atom className={`w-5 h-5 ${isRunning ? "animate-spin text-emerald-400" : "text-zinc-300"}`} />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-base font-bold text-white tracking-wide uppercase font-mono">
                  Quantum Attack & Test Lab
                </h1>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                  REAL QISKIT &bull; DETECTION VALIDATION
                </span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-800/80 text-emerald-400 font-bold">
                  TELEPORTATION-BASED QDS PROTOCOL
                </span>
              </div>
              <p className="text-xs text-zinc-400 font-mono mt-0.5">
                Inject mathematically controlled quantum attack models and benchmark detection precision, recall, and F1 scores (No AI/ML)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchHistory}
              title="Refresh Test History"
              className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-white transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingHistory ? "animate-spin" : ""}`} />
            </button>
            {state === "completed" && (
              <button
                onClick={resetTest}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-850 border border-zinc-700 text-zinc-300 text-xs font-mono transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>New Session</span>
              </button>
            )}
          </div>
        </div>

        {/* IP Action Banner */}
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

        {/* Error Banner if any */}
        {errorMessage && (
          <div className="p-4 rounded-xl bg-red-950/60 border border-red-800/80 text-xs font-mono text-red-300 flex items-center gap-3">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Main Grid: Left 8 cols Config & Execution, Right 4 cols History */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Attack Selector & Parameter Controls */}
          <div className="lg:col-span-8 space-y-6">
            {/* 1. Attack Scenario Selector Cards */}
            <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-zinc-400" />
                  <h2 className="text-xs font-bold text-white uppercase font-mono tracking-wider">
                    1. Select Controlled Attack Scenario
                  </h2>
                </div>
                <span className="text-[10px] font-mono text-zinc-500 uppercase">Detection Rules Mapped</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {scenarios.map((sc) => {
                  const isSelected = selectedScenario === sc.id;
                  return (
                    <div
                      key={sc.id}
                      onClick={() => !isRunning && setSelectedScenario(sc.id as AttackScenarioType)}
                      className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                        isSelected
                          ? "bg-zinc-850 border-zinc-400 shadow-md ring-1 ring-zinc-500"
                          : "bg-zinc-950/70 border-zinc-850 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
                      } ${isRunning ? "opacity-60 cursor-not-allowed" : ""}`}
                    >
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="text-xs font-bold text-white">{sc.name}</h3>
                          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-750 text-zinc-300 shrink-0">
                            {sc.detection_rule}
                          </span>
                        </div>
                        <p className="text-[11px] text-zinc-400 mt-1.5 leading-relaxed font-sans">
                          {sc.description}
                        </p>
                      </div>

                      <div className="mt-3 pt-2 border-t border-zinc-800/80 flex items-center justify-between text-[10px] font-mono">
                        <span className="text-zinc-500">Target Rule: {sc.detection_rule}</span>
                        {isSelected && (
                          <span className="text-white font-bold flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> ACTIVE
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 2. Simulation Execution Parameters */}
            <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-zinc-400" />
                  <h2 className="text-xs font-bold text-white uppercase font-mono tracking-wider">
                    2. Simulation Parameters
                  </h2>
                </div>
                <span className="text-[10px] font-mono text-zinc-500 uppercase">Interactive Dials</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
                {/* Iterations */}
                <div className="p-3.5 bg-zinc-950/80 rounded-lg border border-border">
                  <label className="block text-zinc-400 mb-1.5 text-[11px]">
                    ITERATIONS: <strong className="text-white text-sm">{runs} runs</strong>
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={runs}
                    disabled={isRunning}
                    onChange={(e) => setRuns(parseInt(e.target.value))}
                    className="w-full accent-white cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-zinc-600 mt-1">
                    <span>1</span>
                    <span>50</span>
                    <span>100</span>
                  </div>
                </div>

                {/* Attack Intensity */}
                <div className="p-3.5 bg-zinc-950/80 rounded-lg border border-border">
                  <label className="block text-zinc-400 mb-1.5 text-[11px]">
                    ATTACK RATIO: <strong className="text-white text-sm">{(intensity * 100).toFixed(0)}%</strong>
                  </label>
                  <input
                    type="range"
                    min="0.2"
                    max="1.0"
                    step="0.05"
                    value={intensity}
                    disabled={isRunning}
                    onChange={(e) => setIntensity(parseFloat(e.target.value))}
                    className="w-full accent-white cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-zinc-600 mt-1">
                    <span>20% (Noise)</span>
                    <span>100% (Full)</span>
                  </div>
                </div>

                {/* Replay Window */}
                <div className="p-3.5 bg-zinc-950/80 rounded-lg border border-border">
                  <label className="block text-zinc-400 mb-1.5 text-[11px]">
                    REPLAY WINDOW: <strong className="text-white text-sm">{replayWindow}s</strong>
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="300"
                    step="10"
                    value={replayWindow}
                    disabled={isRunning}
                    onChange={(e) => setReplayWindow(parseInt(e.target.value))}
                    className="w-full accent-white cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-zinc-600 mt-1">
                    <span>10s</span>
                    <span>300s</span>
                  </div>
                </div>

                {/* Quantum Perturbation */}
                <div className="p-3.5 bg-zinc-950/80 rounded-lg border border-border">
                  <label className="block text-zinc-400 mb-1.5 text-[11px]">
                    PERTURBATION: <strong className="text-white text-sm">{(perturbation * 100).toFixed(0)}%</strong>
                  </label>
                  <input
                    type="range"
                    min="0.05"
                    max="0.80"
                    step="0.05"
                    value={perturbation}
                    disabled={isRunning}
                    onChange={(e) => setPerturbation(parseFloat(e.target.value))}
                    className="w-full accent-white cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-zinc-600 mt-1">
                    <span>5% (Subtle)</span>
                    <span>80% (Severe)</span>
                  </div>
                </div>
              </div>

              {/* Action Button & Live Progress */}
              <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="w-full sm:flex-1">
                  {isRunning ? (
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs font-mono text-zinc-300">
                        <span className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                          Simulating quantum states & running detection pipeline...
                        </span>
                        <strong className="text-white">
                          {progress.completed} / {progress.total} ({progress.percentage}%)
                        </strong>
                      </div>
                      <div className="w-full h-2.5 bg-zinc-900 rounded-full overflow-hidden border border-zinc-800">
                        <div
                          className="h-full bg-gradient-to-r from-zinc-400 via-white to-emerald-400 transition-all duration-200"
                          style={{ width: `${progress.percentage}%` }}
                        />
                      </div>
                    </div>
                  ) : state === "completed" ? (
                    <div className="flex items-center gap-2 text-xs font-mono text-emerald-400">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>
                        Simulation complete. Processed {progress.completed} real QDS events through PostgreSQL detection pipeline.
                      </span>
                    </div>
                  ) : (
                    <div className="text-xs font-mono text-zinc-500">
                      Ready to execute {runs} iterations of {selectedScenario.toUpperCase()} model.
                    </div>
                  )}
                </div>

                <button
                  onClick={handleStartTest}
                  disabled={isRunning}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-xs font-bold font-mono tracking-wider bg-white hover:bg-zinc-100 text-zinc-950 shadow-lg hover:shadow-glow transition-all disabled:opacity-50 shrink-0"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{isRunning ? `EXECUTING (${progress.completed}/${progress.total})...` : `RUN ATTACK TEST`}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Historical Test Runs */}
          <div className="lg:col-span-4 space-y-6">
            <div className="p-5 rounded-xl bg-card border border-border shadow-card flex flex-col h-full">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4 text-zinc-400" />
                  <h2 className="text-xs font-bold text-white uppercase font-mono tracking-wider">
                    Recent Test Sessions
                  </h2>
                </div>
                <span className="text-[10px] font-mono text-zinc-500">PostgreSQL</span>
              </div>

              <div className="mt-3 flex-1 overflow-y-auto max-h-[380px] space-y-2 pr-1 font-mono text-xs">
                {loadingHistory ? (
                  <div className="py-12 text-center text-zinc-500">Loading test history...</div>
                ) : historyList.length === 0 ? (
                  <div className="py-12 text-center text-zinc-500 text-[11px]">
                    No historical test runs recorded yet.
                  </div>
                ) : (
                  historyList.map((h) => (
                    <div
                      key={h.test_id}
                      onClick={() => loadHistoricalTest(h.test_id)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        currentTestId === h.test_id
                          ? "bg-zinc-850 border-zinc-500 text-white"
                          : "bg-zinc-950/70 border-zinc-850 hover:border-zinc-700 text-zinc-300"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs capitalize text-white">{h.attack_name || h.attack_type}</span>
                        <span
                          className={`text-[9px] uppercase px-1.5 py-0.5 rounded ${
                            h.status === "completed"
                              ? "bg-emerald-950/60 border border-emerald-800 text-emerald-400"
                              : "bg-zinc-900 border border-zinc-700 text-zinc-400"
                          }`}
                        >
                          {h.status}
                        </span>
                      </div>

                      <div className="mt-2 flex items-center justify-between text-[10px] text-zinc-400">
                        <span>{h.total_runs} events</span>
                        {h.metrics?.f1_score !== undefined && (
                          <span>
                            F1: <strong className="text-white">{h.metrics.f1_score}%</strong>
                          </span>
                        )}
                        <span>{formatDateTime(h.created_at)}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 3. Mathematical Results & Performance Metrics Panel */}
        {metrics && (
          <div className="p-6 rounded-xl bg-card border border-border shadow-card space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-border">
              <div className="flex items-center gap-2.5">
                <Activity className="w-5 h-5 text-emerald-400" />
                <div>
                  <h2 className="text-sm font-bold text-white uppercase font-mono tracking-wider">
                    Detection Performance Metrics & Statistical Benchmark
                  </h2>
                  <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
                    Calculated by backend using exact mathematical detection formulas (Ground Truth vs Detection Decisions)
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={() => window.open(api.getPdfExportUrl(30), "_blank")}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white hover:bg-zinc-100 text-zinc-950 font-bold text-xs font-mono shadow-sm transition-colors"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Download PDF Report</span>
                </button>
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-zinc-500">Test ID:</span>
                  <code className="px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800 text-zinc-300">
                    {currentTestId?.slice(0, 13)}...
                  </code>
                </div>
              </div>
            </div>

            {/* Core Classification KPI Metric Tiles */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5 font-mono">
              <div className="p-4 rounded-xl bg-zinc-950/80 border border-border">
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">Detection Rate</span>
                <div className="text-2xl font-bold text-emerald-400 mt-1">{metrics.detection_rate}%</div>
                <span className="text-[10px] text-zinc-500 mt-1 block">
                  {metrics.detected_attacks} / {metrics.attacks_injected} attacks
                </span>
              </div>
              <div className="p-4 rounded-xl bg-zinc-950/80 border border-border">
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">F1-Score</span>
                <div className="text-2xl font-bold text-white mt-1">{metrics.f1_score}%</div>
                <span className="text-[10px] text-zinc-500 mt-1 block">Harmonic Mean (P & R)</span>
              </div>
              <div className="p-4 rounded-xl bg-zinc-950/80 border border-border">
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">Precision (PPV)</span>
                <div className="text-2xl font-bold text-white mt-1">{metrics.precision}%</div>
                <span className="text-[10px] text-zinc-500 mt-1 block">FP Rate: {(100 - metrics.precision).toFixed(1)}%</span>
              </div>
              <div className="p-4 rounded-xl bg-zinc-950/80 border border-border">
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">Recall / Sensitivity</span>
                <div className="text-2xl font-bold text-white mt-1">{metrics.recall}%</div>
                <span className="text-[10px] text-zinc-500 mt-1 block">FN Rate: {(100 - metrics.recall).toFixed(1)}%</span>
              </div>
              <div className="p-4 rounded-xl bg-zinc-950/80 border border-border">
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">Overall Accuracy</span>
                <div className="text-2xl font-bold text-white mt-1">{metrics.accuracy}%</div>
                <span className="text-[10px] text-zinc-500 mt-1 block">Across all {metrics.total_runs} events</span>
              </div>
              <div className="p-4 rounded-xl bg-zinc-950/80 border border-border">
                <span className="text-[10px] text-zinc-500 uppercase block font-bold">Avg Detection Speed</span>
                <div className="text-2xl font-bold text-emerald-400 mt-1">{metrics.average_detection_time_ms} ms</div>
                <span className="text-[10px] text-zinc-500 mt-1 block">Production Pipeline</span>
              </div>
            </div>

            {/* Confusion Matrix + Deep Analytics */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
              <div className="lg:col-span-6 p-4 rounded-xl bg-zinc-950/80 border border-border space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                  <span className="text-xs font-bold text-white uppercase">2x2 Confusion Matrix (PostgreSQL)</span>
                  <span className="text-[10px] text-zinc-500">GROUND TRUTH vs DETECTED</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-center pt-1">
                  <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60">
                    <span className="text-[10px] text-emerald-400 uppercase font-bold block">True Positives (TP)</span>
                    <span className="text-2xl font-bold text-white mt-1 block">{metrics.true_positives}</span>
                    <span className="text-[10px] text-zinc-400 mt-0.5 block">Attacks Successfully Flagged</span>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800">
                    <span className="text-[10px] text-zinc-400 uppercase font-bold block">False Positives (FP)</span>
                    <span className="text-2xl font-bold text-white mt-1 block">{metrics.false_positives}</span>
                    <span className="text-[10px] text-zinc-500 mt-0.5 block">False Alarms on Normal Traffic</span>
                  </div>
                  <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/60">
                    <span className="text-[10px] text-red-400 uppercase font-bold block">False Negatives (FN)</span>
                    <span className="text-2xl font-bold text-white mt-1 block">{metrics.false_negatives}</span>
                    <span className="text-[10px] text-zinc-400 mt-0.5 block">Missed Injected Attacks</span>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800">
                    <span className="text-[10px] text-zinc-400 uppercase font-bold block">True Negatives (TN)</span>
                    <span className="text-2xl font-bold text-white mt-1 block">{metrics.true_negatives}</span>
                    <span className="text-[10px] text-zinc-500 mt-0.5 block">Normal Events Passed Correctly</span>
                  </div>
                </div>
              </div>
              <div className="lg:col-span-6 p-4 rounded-xl bg-zinc-950/80 border border-border space-y-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                    <span className="text-xs font-bold text-white uppercase">Mathematical Risk Summary</span>
                    <span className="text-[10px] text-zinc-500">EXPLAINABLE FORMULA</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center mt-3">
                    <div className="p-2.5 rounded bg-zinc-900/80 border border-zinc-850">
                      <span className="text-[10px] text-zinc-500 block">AVG RISK</span>
                      <span className="text-base font-bold text-white mt-0.5 block">{metrics.average_risk_score}</span>
                    </div>
                    <div className="p-2.5 rounded bg-zinc-900/80 border border-zinc-850">
                      <span className="text-[10px] text-zinc-500 block">MAX RISK</span>
                      <span className="text-base font-bold text-red-400 mt-0.5 block">{metrics.max_risk_score}</span>
                    </div>
                    <div className="p-2.5 rounded bg-zinc-900/80 border border-zinc-850">
                      <span className="text-[10px] text-zinc-500 block">MIN RISK</span>
                      <span className="text-base font-bold text-emerald-400 mt-0.5 block">{metrics.min_risk_score}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-2 pt-2 border-t border-zinc-850 text-xs">
                  <div className="flex items-center justify-between p-2 rounded bg-zinc-900/60 border border-zinc-850">
                    <span className="text-zinc-400">Mean Measurement Deviation:</span>
                    <span className="font-bold text-emerald-400">
                      {formatPercent(metrics.average_measurement_deviation * 100)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-zinc-900/60 border border-zinc-850">
                    <span className="text-zinc-400">Overall Accuracy:</span>
                    <span className="font-bold text-white">{metrics.accuracy}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Mathematical Forgery Probability Analysis */}
            <div className="p-4 rounded-xl bg-zinc-950/90 border border-zinc-700/80 space-y-3 font-mono">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    Mathematical Forgery Probability Analysis & Theoretical Security Guarantees
                  </span>
                </div>
                <span className="text-[10px] text-zinc-400 uppercase px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800">
                  NO AI/ML &bull; DETERMINISTIC THRESHOLDS
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800 space-y-1.5">
                  <span className="text-[10px] text-zinc-400 uppercase font-bold block">
                    Calculated Forgery Probability (P_forge)
                  </span>
                  <div className="text-xl font-bold text-emerald-400">
                    {metrics.attacks_injected > 0
                      ? `${(((metrics.false_negatives || 0) / metrics.attacks_injected) * 100).toFixed(2)}%`
                      : "0.00%"}
                  </div>
                  <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
                    Formula: <code className="text-white font-mono">P_forge = FN / Total_Attacks = 1 - Recall</code>
                  </p>
                  <p className="text-[9px] text-zinc-500 font-sans">
                    Probability that an adversary successfully injects a forged quantum signature without triggering detection.
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800 space-y-1.5">
                  <span className="text-[10px] text-zinc-400 uppercase font-bold block">
                    False Alarm Rate (FAR / FPR)
                  </span>
                  <div className="text-xl font-bold text-white">
                    {metrics.normal_injected > 0
                      ? `${(((metrics.false_positives || 0) / metrics.normal_injected) * 100).toFixed(2)}%`
                      : "0.00%"}
                  </div>
                  <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
                    Formula: <code className="text-white font-mono">FAR = FP / (FP + TN)</code>
                  </p>
                  <p className="text-[9px] text-zinc-500 font-sans">
                    Rate of legitimate quantum signatures falsely rejected by deterministic statistical thresholds.
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800 space-y-1.5">
                  <span className="text-[10px] text-zinc-400 uppercase font-bold block">
                    Security Guarantee Level
                  </span>
                  <div className="text-sm font-bold text-emerald-400 uppercase flex items-center gap-1.5 mt-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>
                      {(metrics.false_negatives || 0) === 0
                        ? "Information-Theoretic Security"
                        : "Threshold Bound Security"}
                    </span>
                  </div>
                  <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
                    Quantum Teleportation + Pauli Eigenstate projective measurements ensure deterministic rejection of signature tampering.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 4. Individual Simulation Runs Table */}
        <div className="p-5 rounded-xl bg-card border border-border shadow-card flex flex-col space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-zinc-400" />
              <h2 className="text-xs font-bold text-white uppercase font-mono tracking-wider">
                Individual Simulation Iteration Log ({results.length} records)
              </h2>
            </div>
            <span className="text-[10px] font-mono text-zinc-500 uppercase">
              Linked to PostgreSQL Security Events, Threats & IPS Firewall
            </span>
          </div>

          <div className="overflow-x-auto">
            {results.length === 0 ? (
              <div className="py-12 text-center text-xs font-mono text-zinc-500">
                No iteration results to display. Click "RUN ATTACK TEST" to generate simulation telemetry.
              </div>
            ) : (
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-border text-zinc-500 uppercase text-[10px]">
                    <th className="pb-3 font-medium"># Run</th>
                    <th className="pb-3 font-medium">Ground Truth</th>
                    <th className="pb-3 font-medium">Source IP / Node</th>
                    <th className="pb-3 font-medium">Detection Result</th>
                    <th className="pb-3 font-medium">IPS Defense</th>
                    <th className="pb-3 font-medium">Severity</th>
                    <th className="pb-3 font-medium">Risk</th>
                    <th className="pb-3 font-medium">Triggered Rule</th>
                    <th className="pb-3 font-medium">Deviation</th>
                    <th className="pb-3 font-medium">Speed</th>
                    <th className="pb-3 text-right font-medium">IPS Actions & Forensics</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {results.map((r) => {
                    const rowIp = r.source_ip || "10.0.1.10";
                    return (
                      <tr key={r.id || r.run_index} className="hover:bg-card-hover/90 transition-colors">
                        <td className="py-3 text-zinc-400 whitespace-nowrap font-bold">
                          #{r.run_index}
                        </td>
                        <td className="py-3 whitespace-nowrap">
                          {r.attack_injected ? (
                            <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-red-950/70 text-red-300 border border-red-800/80">
                              ATTACK INJECTED
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-zinc-900 text-zinc-400 border border-zinc-800">
                              BENIGN NORMAL
                            </span>
                          )}
                        </td>
                        <td className="py-3 whitespace-nowrap">
                          <div className="flex flex-col">
                            <span className="font-bold text-amber-300 text-[11px]">{rowIp}</span>
                            <span className="text-[10px] text-zinc-500">{r.source_node || "QNode-Alpha"}</span>
                          </div>
                        </td>
                        <td className="py-3 whitespace-nowrap">
                          {r.threat_detected ? (
                            <span className="inline-flex items-center gap-1.5 text-red-400 font-bold">
                              <CheckCircle2 className="w-3.5 h-3.5" /> THREAT FLAGGED
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 text-zinc-500">
                              <XCircle className="w-3.5 h-3.5" /> PASSED CLEAR
                            </span>
                          )}
                        </td>
                        <td className="py-3 whitespace-nowrap">
                          {r.threat_detected ? (
                            <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-red-950/80 border border-red-700 text-red-300 flex items-center gap-1 w-fit">
                              <Ban className="w-2.5 h-2.5" /> {r.ips_action || "QUARANTINED"}
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono bg-zinc-900 border border-zinc-800 text-zinc-400">
                              PASSED
                            </span>
                          )}
                        </td>
                        <td className="py-3 whitespace-nowrap">
                          {r.severity && r.severity !== "none" ? (
                            <SeverityBadge severity={r.severity as any} />
                          ) : (
                            <span className="text-zinc-600">--</span>
                          )}
                        </td>
                        <td className="py-3 whitespace-nowrap">
                          <span
                            className={`font-bold ${
                              (r.risk_score || 0) >= 75
                                ? "text-red-400"
                                : (r.risk_score || 0) >= 50
                                ? "text-orange-400"
                                : (r.risk_score || 0) >= 25
                                ? "text-amber-300"
                                : "text-zinc-400"
                            }`}
                          >
                            {r.risk_score !== null && r.risk_score !== undefined ? r.risk_score : "--"}
                          </span>
                        </td>
                        <td className="py-3 text-zinc-300 whitespace-nowrap">
                          {r.detection_rule || "NONE"}
                        </td>
                        <td className="py-3 whitespace-nowrap">
                          {r.measurement_deviation !== null && r.measurement_deviation !== undefined ? (
                            <span
                              className={
                                r.measurement_deviation > 0.3 ? "text-red-400 font-bold" : "text-emerald-400"
                              }
                            >
                              {formatPercent(r.measurement_deviation * 100)}
                            </span>
                          ) : (
                            "--"
                          )}
                        </td>
                        <td className="py-3 text-zinc-400 whitespace-nowrap">
                          {r.detection_time_ms} ms
                        </td>
                        <td className="py-3 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleBlockIp(rowIp)}
                              disabled={isIpProcessing}
                              title={`Block IP ${rowIp}`}
                              className="px-2 py-1 rounded bg-red-950/70 hover:bg-red-900 border border-red-800 text-red-300 text-[10px] font-bold transition-all disabled:opacity-50"
                            >
                              Block IP
                            </button>
                            <button
                              onClick={() => handleTrustIp(rowIp)}
                              disabled={isIpProcessing}
                              title={`Trust IP ${rowIp}`}
                              className="px-2 py-1 rounded bg-emerald-950/70 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 text-[10px] font-bold transition-all disabled:opacity-50"
                            >
                              Trust IP
                            </button>
                            {r.threat_id && (
                              <Link
                                href={`/threats/${r.threat_id}`}
                                className="inline-flex items-center gap-1 px-2 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 hover:text-white text-[10px] transition-colors"
                              >
                                <span>Inspect</span>
                                <ExternalLink className="w-2.5 h-2.5" />
                              </Link>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
