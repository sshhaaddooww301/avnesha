"use client";

import React, { useState } from "react";
import { Atom, Play, CheckCircle2, X } from "lucide-react";
import { api } from "@/lib/api";

interface SimulatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRunSuccess?: () => void;
}

export function SimulatorModal({ isOpen, onClose, onRunSuccess }: SimulatorModalProps) {
  const [mode, setMode] = useState<string>("attack_mix");
  const [count, setCount] = useState<number>(10);
  const [intervalMs, setIntervalMs] = useState<number>(300);
  const [isRunning, setIsRunning] = useState(false);
  const [resultMsg, setResultMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const modes = [
    { id: "normal", name: "Normal Quantum Signature Traffic", desc: "Legitimate QDS signature verification with natural noise" },
    { id: "attack_mix", name: "Mixed Attack Scenario", desc: "Blend of MITM, Replay, Forgery, Impersonation & Quantum Anomalies" },
    { id: "replay", name: "Signature Replay Inundation", desc: "Signatures reused across rapid sliding window (QDS-RPL-001)" },
    { id: "mitm", name: "Channel Decoherence & MITM", desc: "State tampering and high measurement deviation (QDS-MITM-001)" },
    { id: "forgery", name: "Cryptographic Hash Forgery", desc: "Tampered signature hash blocks (QDS-FRG-001)" },
    { id: "impersonation", name: "Node Origin Impersonation", desc: "Unauthorized origin node credential hijacking (QDS-IMP-001)" },
    { id: "anomaly", name: "Quantum Measurement Anomaly", desc: "Statistical Bell-state correlation outliers (QDS-ANM-001)" },
  ];

  const handleRun = async () => {
    setIsRunning(true);
    setResultMsg(null);
    try {
      const res = await api.runSimulator(mode, count, intervalMs);
      setResultMsg(res.message);
      if (onRunSuccess) onRunSuccess();
    } catch (err: any) {
      setResultMsg(`Error: ${err.message || "Failed to trigger simulation"}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="relative w-full max-w-xl bg-[#101014] border border-zinc-700/80 rounded-2xl shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-700 text-white">
              <Atom className="w-5 h-5 animate-spin-slow" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-wide uppercase font-mono">
                Teleportation-Based QDS Threat Simulator
              </h3>
              <p className="text-[11px] text-zinc-400">Simulate Bell-state teleportation QDS events & projective measurements</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 border border-zinc-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="mt-4 space-y-4">
          <div>
            <label className="block text-[11px] font-mono font-medium text-zinc-400 mb-2 uppercase">
              Simulation Scenario
            </label>
            <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto pr-1">
              {modes.map((m) => (
                <div
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    mode === m.id
                      ? "bg-zinc-850 border-zinc-500 text-white shadow-sm"
                      : "bg-zinc-950/60 border-zinc-800/80 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold">{m.name}</span>
                    {mode === m.id && <span className="text-[9px] text-zinc-300 uppercase px-1.5 py-0.5 rounded bg-zinc-750 font-mono border border-zinc-600">SELECTED</span>}
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-0.5">{m.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-1">
            <div className="p-3 bg-zinc-950/80 rounded-lg border border-zinc-850">
              <label className="block text-[10px] font-mono uppercase text-zinc-400 mb-1">
                Event Batch: <strong className="text-white">{count}</strong>
              </label>
              <input
                type="range"
                min="1"
                max="50"
                value={count}
                onChange={(e) => setCount(parseInt(e.target.value))}
                className="w-full accent-zinc-400"
              />
              <div className="flex justify-between text-[9px] font-mono text-zinc-600 mt-1">
                <span>1</span>
                <span>25</span>
                <span>50</span>
              </div>
            </div>

            <div className="p-3 bg-zinc-950/80 rounded-lg border border-zinc-850">
              <label className="block text-[10px] font-mono uppercase text-zinc-400 mb-1">
                Interval: <strong className="text-white">{intervalMs}ms</strong>
              </label>
              <input
                type="range"
                min="100"
                max="2000"
                step="100"
                value={intervalMs}
                onChange={(e) => setIntervalMs(parseInt(e.target.value))}
                className="w-full accent-zinc-400"
              />
              <div className="flex justify-between text-[9px] font-mono text-zinc-600 mt-1">
                <span>100ms</span>
                <span>1000ms</span>
                <span>2000ms</span>
              </div>
            </div>
          </div>

          {resultMsg && (
            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-700 text-xs font-mono text-zinc-200 flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
              <span>{resultMsg}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-zinc-800 flex items-center justify-end gap-2.5">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-850 border border-zinc-800 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-semibold bg-white hover:bg-zinc-100 text-zinc-950 shadow-md transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isRunning ? "Simulating QDS States..." : `Inject ${count} Events`}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
