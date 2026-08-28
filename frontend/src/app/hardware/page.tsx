"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { api } from "@/lib/api";
import {
  Cpu,
  Radio,
  Activity,
  Shield,
  Zap,
  CheckCircle2,
  RefreshCw,
  Send,
  Sliders,
  Cable,
  Server,
  Layers,
  ArrowUpRight,
  Terminal,
  AlertCircle,
  PowerOff,
} from "lucide-react";

export default function HardwarePage() {
  const [telemetry, setTelemetry] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [pingingNode, setPingingNode] = useState<string | null>(null);
  const [pingResult, setPingResult] = useState<any>(null);
  const [ingestingPulse, setIngestingPulse] = useState<boolean>(false);
  const [pulseLog, setPulseLog] = useState<string | null>(null);

  // Serial config form state
  const [port, setPort] = useState<string>("COM3");
  const [baudrate, setBaudrate] = useState<number>(115200);
  const [mode, setMode] = useState<string>("STANDBY");
  const [configSuccess, setConfigSuccess] = useState<boolean>(false);

  const fetchHardwareData = useCallback(async () => {
    try {
      const data = await api.getHardwareStatus();
      setTelemetry(data);
      if (data?.serial_interface) {
        setPort(data.serial_interface.port || "COM3");
        setBaudrate(data.serial_interface.baudrate || 115200);
      }
    } catch (e) {
      console.error("Failed to load hardware telemetry:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHardwareData();
    const interval = setInterval(fetchHardwareData, 3000);
    return () => clearInterval(interval);
  }, [fetchHardwareData]);

  const handlePing = async (nodeId: string) => {
    setPingingNode(nodeId);
    setPingResult(null);
    try {
      const res = await api.pingHardwareNode(nodeId);
      setPingResult(res);
    } catch (e) {
      console.error("Ping error:", e);
    } finally {
      setPingingNode(null);
    }
  };

  const handleSendLivePulse = async () => {
    setIngestingPulse(true);
    setPulseLog(null);
    try {
      const payload = {
        node_id: "QNODE-ALPHA-HQ",
        session_id: `QDS-PHYS-TX-${Date.now()}`,
        target_node_id: "QNODE-BETA-BRANCH",
        key_stream_id: `KEY-STR-${Math.random().toString(36).substring(2, 9).toUpperCase()}`,
        sifted_key_bits: 2048,
        quantum_bit_error_rate: 0.022,
        optical_power_uW: 14.7,
        dark_count_rate_hz: 118.0,
        deadtime_variance_ns: 8.44,
        decoy_gain_ratio: 1.01,
        fiber_attenuation_db_km: 0.2,
      };
      const res = await api.syncEtsiTelemetry(payload);
      setPulseLog(
        `[ETSI 014 SYNC OK] Ingested Event ${res.event_id.slice(0, 8)}... | QBER: ${(res.qber * 100).toFixed(2)}% | Threat: ${res.threat_detected ? res.threat_type : "CLEAN"}`
      );
      fetchHardwareData();
    } catch (e: any) {
      setPulseLog(`[ERROR] Sync failed: ${e.message}`);
    } finally {
      setIngestingPulse(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      await api.configureHardware({ port, baudrate, mode });
      setConfigSuccess(true);
      setTimeout(() => setConfigSuccess(false), 3000);
      fetchHardwareData();
    } catch (e) {
      console.error("Config failed:", e);
    }
  };

  const isLive = telemetry?.is_hardware_live;

  return (
    <div className="min-h-screen flex flex-col bg-background text-zinc-200">
      <Navbar />

      <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Header Ribbon */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-xl bg-card border border-border shadow-card">
          <div className="flex items-center gap-3.5">
            <div className={`p-2.5 rounded-lg border text-white ${isLive ? "bg-emerald-950/80 border-emerald-700/80" : "bg-zinc-900 border-zinc-800"}`}>
              <Cpu className={`w-5 h-5 ${isLive ? "text-emerald-400 animate-pulse" : "text-zinc-400"}`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-white font-mono tracking-wide">
                  PHYSICAL HARDWARE & OPTICAL LAYER INTERFACE
                </h1>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase border ${
                  isLive
                    ? "bg-emerald-950/80 border-emerald-700/60 text-emerald-400"
                    : "bg-amber-950/80 border-amber-800/60 text-amber-400"
                }`}>
                  {isLive ? "LIVE HARDWARE STREAMING" : "STANDBY (NO HARDWARE DETECTED)"}
                </span>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                Physical SPAD Single-Photon Detectors, 1550nm Laser Power Telemetry, and ETSI GS QKD 014 Ingress
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSendLivePulse}
              disabled={ingestingPulse}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-zinc-950 transition-all shadow-md"
            >
              <Send className={`w-3.5 h-3.5 ${ingestingPulse ? "animate-spin" : ""}`} />
              <span>{ingestingPulse ? "Transmitting..." : "Send ETSI 014 Hardware Pulse"}</span>
            </button>

            <button
              onClick={fetchHardwareData}
              title="Refresh Hardware Telemetry"
              className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Live / Standby Status Banner */}
        {!isLive ? (
          <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/50 text-amber-200 text-xs font-mono flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-white text-sm">NO PHYSICAL HARDWARE LINK CURRENTLY STREAMING</strong>
                <p className="text-amber-300/80 text-xs mt-1 leading-relaxed">
                  Nodes are in <strong>STANDBY</strong>. To establish a live optical link, start the edge agent:{" "}
                  <code className="px-1.5 py-0.5 bg-zinc-950 border border-amber-900/60 rounded text-emerald-400">
                    python backend/hardware_agent.py
                  </code>{" "}
                  or click the <strong>&quot;Send ETSI 014 Hardware Pulse&quot;</strong> button above to inject a test hardware frame.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/50 text-emerald-200 text-xs font-mono flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 animate-pulse" />
              <div>
                <strong className="text-white">LIVE PHYSICAL OPTICAL LINK ACTIVE</strong>
                <p className="text-emerald-300/80 text-[11px] mt-0.5">
                  Receiving continuous SPAD telemetry &amp; ETSI 014 key sync packets from physical transceivers.
                </p>
              </div>
            </div>
          </div>
        )}

        {pulseLog && (
          <div className="p-3 rounded-lg bg-zinc-900 border border-emerald-800/80 text-emerald-300 text-xs font-mono flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{pulseLog}</span>
            </div>
            <button onClick={() => setPulseLog(null)} className="text-zinc-500 hover:text-zinc-300 text-xs">
              Dismiss
            </button>
          </div>
        )}

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="p-4 rounded-xl bg-card border border-border">
            <span className="text-[10px] font-mono text-zinc-400 uppercase">Live Optical Links</span>
            <div className="text-lg font-bold text-white font-mono mt-1 flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${isLive ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"}`} />
              <span>{telemetry?.healthy_links || 0} / {telemetry?.nodes_count || 3} Active</span>
            </div>
            <span className="text-[10px] text-zinc-500 font-mono mt-1 block">
              {isLive ? "Telemetry Streaming" : "Awaiting Packets"}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border">
            <span className="text-[10px] font-mono text-zinc-400 uppercase">Live Channel QBER</span>
            <div className="text-xl font-bold font-mono mt-1">
              {isLive ? (
                <span className="text-emerald-400">{((telemetry?.average_qber || 0) * 100).toFixed(2)}%</span>
              ) : (
                <span className="text-zinc-600">-- (Offline)</span>
              )}
            </div>
            <span className="text-[10px] text-zinc-500 font-mono mt-1 block">Threshold: &lt; 11.0%</span>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border">
            <span className="text-[10px] font-mono text-zinc-400 uppercase">Live Optical Power</span>
            <div className="text-xl font-bold font-mono mt-1">
              {isLive ? (
                <span className="text-white">{(telemetry?.average_optical_power_uW || 0).toFixed(2)} <span className="text-xs text-zinc-400">μW</span></span>
              ) : (
                <span className="text-zinc-600">-- μW</span>
              )}
            </div>
            <span className="text-[10px] text-zinc-500 font-mono mt-1 block">Nominal: 10 - 25 μW</span>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border">
            <span className="text-[10px] font-mono text-zinc-400 uppercase">Total Sifted Keys</span>
            <div className="text-xl font-bold text-white font-mono mt-1">
              {(telemetry?.total_sifted_bits || 0).toLocaleString()} <span className="text-xs text-zinc-400">bits</span>
            </div>
            <span className="text-[10px] text-zinc-500 font-mono mt-1 block">Physical Entropy Ingested</span>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border">
            <span className="text-[10px] font-mono text-zinc-400 uppercase">Standard Compliance</span>
            <div className="text-xs font-bold text-zinc-200 font-mono mt-1.5 space-y-0.5">
              <div>✓ ETSI GS QKD 014</div>
              <div>✓ ITU-T Y.3800 QIT</div>
            </div>
          </div>
        </div>

        {/* Optical Transceiver Node Cards */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cable className="w-4 h-4 text-zinc-400" />
              <h2 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
                Physical Optical Transceivers (Live Telemetry Heartbeat)
              </h2>
            </div>
            <span className="text-[10px] font-mono text-zinc-500">Auto-refresh 3s | 15s Heartbeat Window</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {(telemetry?.nodes || []).map((node: any) => {
              const nodeLive = node.is_live;
              return (
                <div
                  key={node.node_id}
                  className={`p-5 rounded-xl border shadow-card space-y-4 transition-all ${
                    nodeLive ? "bg-card border-emerald-850 ring-1 ring-emerald-900/40" : "bg-card/70 border-border opacity-85"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                        {node.node_id}
                      </span>
                      <h3 className="text-sm font-bold text-white mt-1.5">{node.label}</h3>
                    </div>
                    {nodeLive ? (
                      <span className="flex items-center gap-1.5 text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-700/60 px-2 py-0.5 rounded-full">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" /> CONNECTED
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-[10px] font-mono font-bold text-zinc-400 bg-zinc-900 border border-zinc-750 px-2 py-0.5 rounded-full">
                        <PowerOff className="w-3 h-3 text-zinc-500" /> STANDBY
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-border">
                    <div className="p-2.5 rounded-lg bg-zinc-950/70 border border-border">
                      <span className="text-[9px] text-zinc-500 uppercase block">Wavelength</span>
                      <strong className="text-white text-xs">{node.wavelength_nm} nm</strong>
                    </div>
                    <div className="p-2.5 rounded-lg bg-zinc-950/70 border border-border">
                      <span className="text-[9px] text-zinc-500 uppercase block">Current QBER</span>
                      {nodeLive ? (
                        <strong className="text-emerald-400 text-xs">{(node.current_qber * 100).toFixed(2)}%</strong>
                      ) : (
                        <span className="text-zinc-600">-- (Offline)</span>
                      )}
                    </div>
                    <div className="p-2.5 rounded-lg bg-zinc-950/70 border border-border">
                      <span className="text-[9px] text-zinc-500 uppercase block">Optical Power</span>
                      {nodeLive ? (
                        <strong className="text-white text-xs">{node.optical_power_uW} μW</strong>
                      ) : (
                        <span className="text-zinc-600">-- μW</span>
                      )}
                    </div>
                    <div className="p-2.5 rounded-lg bg-zinc-950/70 border border-border">
                      <span className="text-[9px] text-zinc-500 uppercase block">SPAD Dark Count</span>
                      {nodeLive ? (
                        <strong className="text-white text-xs">{node.dark_count_rate_hz} Hz</strong>
                      ) : (
                        <span className="text-zinc-600">-- Hz</span>
                      )}
                    </div>
                    <div className="p-2.5 rounded-lg bg-zinc-950/70 border border-border">
                      <span className="text-[9px] text-zinc-500 uppercase block">Dead-Time</span>
                      {nodeLive ? (
                        <strong className="text-white text-xs">{node.deadtime_ns} ns</strong>
                      ) : (
                        <span className="text-zinc-600">-- ns</span>
                      )}
                    </div>
                    <div className="p-2.5 rounded-lg bg-zinc-950/70 border border-border">
                      <span className="text-[9px] text-zinc-500 uppercase block">Fiber Length</span>
                      <strong className="text-white text-xs">{node.fiber_length_km} km</strong>
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-between border-t border-border">
                    <span className="text-[10px] font-mono text-zinc-500">
                      Keys: {node.total_keys_sifted.toLocaleString()} bits
                    </span>
                    <button
                      onClick={() => handlePing(node.node_id)}
                      disabled={pingingNode === node.node_id}
                      className="flex items-center gap-1 px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-850 border border-zinc-750 text-zinc-300 hover:text-white text-[11px] font-mono transition-all"
                    >
                      <Radio className="w-3 h-3 text-zinc-400" />
                      <span>{pingingNode === node.node_id ? "Pinging..." : "Test Ping"}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Ping Result Banner */}
        {pingResult && (
          <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-750 shadow-lg text-xs font-mono flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Radio className="w-5 h-5 text-emerald-400 animate-pulse" />
              <div>
                <span className="text-white font-bold">Optical Link Ping to [{pingResult.node_id}]: {pingResult.status}</span>
                <p className="text-zinc-400 text-[11px] mt-0.5">
                  Round-trip Optical Latency: <strong className="text-emerald-400">{pingResult.optical_roundtrip_latency_ms} ms</strong> | 
                  Wavelength: {pingResult.wavelength_nm} nm | Protocol: {pingResult.interface}
                </p>
              </div>
            </div>
            <button onClick={() => setPingResult(null)} className="text-zinc-500 hover:text-white text-xs px-2 py-1">
              Close
            </button>
          </div>
        )}

        {/* Edge Daemon & Configuration */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-6 p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-border">
              <Terminal className="w-4 h-4 text-zinc-400" />
              <h2 className="text-xs font-bold text-white uppercase font-mono tracking-wider">
                How to Connect Real Hardware Sensors
              </h2>
            </div>

            <p className="text-xs text-zinc-400 leading-relaxed font-sans">
              To connect real optical transceivers, SPADs, or a Raspberry Pi edge board, launch the edge agent:
            </p>

            <div className="p-3.5 rounded-lg bg-zinc-950 border border-border font-mono text-xs text-zinc-300 space-y-2">
              <div className="text-zinc-500"># 1. Open a terminal in backend</div>
              <div className="text-emerald-400">cd backend</div>
              <div className="text-zinc-500"># 2. Launch physical edge daemon (stream live packets)</div>
              <div className="text-emerald-400">python hardware_agent.py --siem-url http://127.0.0.1:8000 --interval 2.0</div>
            </div>

            <div className="text-[11px] text-zinc-500 space-y-1 font-mono">
              <div>• Status automatically turns GREEN (CONNECTED) when packets arrive.</div>
              <div>• If no packets arrive within 15 seconds, link automatically drops to STANDBY.</div>
            </div>
          </div>

          <div className="lg:col-span-6 p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-border">
              <Sliders className="w-4 h-4 text-zinc-400" />
              <h2 className="text-xs font-bold text-white uppercase font-mono tracking-wider">
                Serial COM / Ingress Port Settings
              </h2>
            </div>

            <div className="space-y-3.5 text-xs font-mono">
              <div>
                <label className="block text-zinc-400 mb-1 text-[11px]">SERIAL COM / TTY DEVICE PORT</label>
                <input
                  type="text"
                  value={port}
                  onChange={(e) => setPort(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-zinc-950 border border-border text-white focus:outline-none focus:border-zinc-500"
                  placeholder="e.g. COM3 or /dev/ttyUSB0"
                />
              </div>

              <div>
                <label className="block text-zinc-400 mb-1 text-[11px]">BAUDRATE (BPS)</label>
                <select
                  value={baudrate}
                  onChange={(e) => setBaudrate(parseInt(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-zinc-950 border border-border text-white focus:outline-none focus:border-zinc-500"
                >
                  <option value={9600}>9600</option>
                  <option value={57600}>57600</option>
                  <option value={115200}>115200 (Default SPAD)</option>
                  <option value={921600}>921600 (High-Speed FPGA)</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-[10px] text-zinc-500">Device: SPAD_FPGA_TimeTagger_v2</span>
                <button
                  onClick={handleSaveConfig}
                  className="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 font-bold transition-all"
                >
                  Save Hardware Config
                </button>
              </div>

              {configSuccess && (
                <div className="p-2 rounded bg-emerald-950/80 border border-emerald-800 text-emerald-400 text-xs">
                  ✓ Hardware configuration successfully saved & applied.
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
