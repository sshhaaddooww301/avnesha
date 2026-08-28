"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { EmptyState } from "@/components/common/EmptyState";
import { api } from "@/lib/api";
import { SecurityEvent } from "@/lib/types";
import { formatDateTime, formatPercent, formatHash } from "@/lib/utils";
import {
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  Eye,
  X,
  Lock,
  Atom,
} from "lucide-react";

export default function LogsPage() {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [eventType, setEventType] = useState("");
  const [sourceNode, setSourceNode] = useState("");
  const [verificationResult, setVerificationResult] = useState<string>("");

  // Selected event for detail drawer
  const [selectedEvent, setSelectedEvent] = useState<any | null>(null);

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      const params: Record<string, any> = {
        page,
        page_size: 15,
        sort_by: "timestamp",
        sort_order: "desc",
      };
      if (search) params.search = search;
      if (eventType) params.event_type = eventType;
      if (sourceNode) params.source_node = sourceNode;
      if (verificationResult !== "") params.verification_result = verificationResult === "true";

      const res = await api.getEvents(params);
      setEvents(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error("Failed to fetch events:", err);
    } finally {
      setLoading(false);
    }
  }, [page, search, eventType, sourceNode, verificationResult]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handleViewDetail = async (eventId: string) => {
    try {
      const detail = await api.getEventDetail(eventId);
      setSelectedEvent(detail);
    } catch (err) {
      console.error("Failed to fetch event detail:", err);
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
              Logs & Telemetry Explorer
            </h1>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Query, filter, and inspect raw Quantum Digital Signature verification streams
            </p>
          </div>
          <button
            onClick={fetchEvents}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card hover:bg-card-hover border border-border text-xs font-mono text-zinc-300"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-zinc-400" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="p-4 rounded-xl bg-card border border-border shadow-card grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search Event ID, Session, Node..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-200 placeholder-zinc-500 font-mono focus:border-zinc-500 focus:outline-none"
            />
          </div>

          <div>
            <select
              value={eventType}
              onChange={(e) => {
                setEventType(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-300 font-mono focus:border-zinc-500 focus:outline-none"
            >
              <option value="">All Event Types</option>
              <option value="QDS_VERIFICATION">QDS_VERIFICATION</option>
              <option value="QDS_MEASUREMENT">QDS_MEASUREMENT</option>
              <option value="BELL_STATE_EXCHANGE">BELL_STATE_EXCHANGE</option>
            </select>
          </div>

          <div>
            <select
              value={sourceNode}
              onChange={(e) => {
                setSourceNode(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-300 font-mono focus:border-zinc-500 focus:outline-none"
            >
              <option value="">All Source Nodes</option>
              <option value="QNode-Alpha-01">QNode-Alpha-01</option>
              <option value="QNode-Beta-02">QNode-Beta-02</option>
              <option value="QNode-Gamma-03">QNode-Gamma-03</option>
              <option value="QNode-Delta-04">QNode-Delta-04</option>
              <option value="QNode-Epsilon-05">QNode-Epsilon-05</option>
            </select>
          </div>

          <div>
            <select
              value={verificationResult}
              onChange={(e) => {
                setVerificationResult(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-300 font-mono focus:border-zinc-500 focus:outline-none"
            >
              <option value="">All Verification States</option>
              <option value="true">Verification Passed (True)</option>
              <option value="false">Verification Failed (False)</option>
            </select>
          </div>

          <div>
            <button
              onClick={() => {
                setSearch("");
                setEventType("");
                setSourceNode("");
                setVerificationResult("");
                setPage(1);
              }}
              className="w-full py-2 bg-zinc-950 hover:bg-zinc-900 rounded-lg border border-border text-xs text-zinc-400 hover:text-zinc-200 font-mono transition-colors"
            >
              Reset Filters
            </button>
          </div>
        </div>

        {/* Events Data Table */}
        <div className="bg-card rounded-xl border border-border p-5 shadow-card overflow-hidden flex flex-col">
          <div className="overflow-x-auto">
            {loading ? (
              <div className="py-16 text-center text-xs font-mono text-zinc-500">
                Fetching event telemetry from PostgreSQL...
              </div>
            ) : events.length === 0 ? (
              <EmptyState
                icon="database"
                title="No Security Events Found"
                message="No events matching the current search criteria exist in the database."
              />
            ) : (
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-border text-zinc-500 uppercase text-[10px]">
                    <th className="pb-3 font-medium">Timestamp</th>
                    <th className="pb-3 font-medium">Event ID</th>
                    <th className="pb-3 font-medium">Type</th>
                    <th className="pb-3 font-medium">Source Node</th>
                    <th className="pb-3 font-medium">Session ID</th>
                    <th className="pb-3 font-medium">Expected</th>
                    <th className="pb-3 font-medium">Observed</th>
                    <th className="pb-3 font-medium">Deviation</th>
                    <th className="pb-3 font-medium">Verification</th>
                    <th className="pb-3 font-medium">Threat</th>
                    <th className="pb-3 text-right font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {events.map((ev) => (
                    <tr key={ev.event_id} className="hover:bg-card-hover/90 transition-colors">
                      <td className="py-3 text-zinc-400 whitespace-nowrap text-[11px]">
                        {formatDateTime(ev.timestamp)}
                      </td>
                      <td className="py-3 text-zinc-300 whitespace-nowrap">{formatHash(ev.event_id, 10)}</td>
                      <td className="py-3 font-sans font-medium text-white whitespace-nowrap">{ev.event_type}</td>
                      <td className="py-3 text-zinc-300 whitespace-nowrap">{ev.source_node}</td>
                      <td className="py-3 text-zinc-400 whitespace-nowrap">{ev.session_id}</td>
                      <td className="py-3 text-zinc-400 whitespace-nowrap">
                        {ev.expected_measurement !== null && ev.expected_measurement !== undefined
                          ? ev.expected_measurement.toFixed(4)
                          : "--"}
                      </td>
                      <td className="py-3 text-zinc-400 whitespace-nowrap">
                        {ev.observed_measurement !== null && ev.observed_measurement !== undefined
                          ? ev.observed_measurement.toFixed(4)
                          : "--"}
                      </td>
                      <td className="py-3 whitespace-nowrap">
                        {ev.measurement_deviation !== null && ev.measurement_deviation !== undefined ? (
                          <span
                            className={`font-semibold ${
                              ev.measurement_deviation > 0.3 ? "text-red-400" : "text-emerald-400"
                            }`}
                          >
                            {formatPercent(ev.measurement_deviation * 100)}
                          </span>
                        ) : (
                          "--"
                        )}
                      </td>
                      <td className="py-3 whitespace-nowrap">
                        {ev.verification_result === true ? (
                          <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px]">
                            <CheckCircle className="w-3.5 h-3.5" /> Pass
                          </span>
                        ) : ev.verification_result === false ? (
                          <span className="inline-flex items-center gap-1 text-red-400 text-[11px]">
                            <XCircle className="w-3.5 h-3.5" /> Fail
                          </span>
                        ) : (
                          <span className="text-zinc-500">N/A</span>
                        )}
                      </td>
                      <td className="py-3 whitespace-nowrap">
                        {ev.has_threats ? (
                          <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-red-950/60 text-red-400 border border-red-800/80">
                            Flagged
                          </span>
                        ) : (
                          <span className="text-zinc-600 text-[11px]">None</span>
                        )}
                      </td>
                      <td className="py-3 text-right whitespace-nowrap">
                        <button
                          onClick={() => handleViewDetail(ev.event_id)}
                          className="p-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 hover:text-white transition-colors"
                          title="Inspect Event"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination Footer */}
          {total > 0 && (
            <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-xs font-mono text-zinc-400">
              <span>
                Page <strong className="text-white">{page}</strong> of{" "}
                <strong className="text-white">{totalPages}</strong> ({total} events)
              </span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-2.5 py-1 rounded bg-zinc-900 border border-border disabled:opacity-40 hover:bg-zinc-850 text-zinc-200"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="px-2.5 py-1 rounded bg-zinc-900 border border-border disabled:opacity-40 hover:bg-zinc-850 text-zinc-200"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Event Detail Drawer / Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="relative w-full max-w-2xl bg-[#101014] border border-zinc-750 rounded-2xl shadow-2xl p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-zinc-800">
              <div className="flex items-center gap-2.5">
                <Atom className="w-5 h-5 text-zinc-300" />
                <h3 className="text-sm font-bold text-white uppercase font-mono">Event Telemetry Details</h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 border border-zinc-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4 font-mono text-xs">
              <div className="grid grid-cols-2 gap-3 p-3.5 bg-zinc-950/80 rounded-lg border border-zinc-850">
                <div>
                  <span className="text-zinc-500 block text-[10px] uppercase">EVENT ID</span>
                  <span className="text-zinc-200 break-all">{selectedEvent.event_id}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block text-[10px] uppercase">TIMESTAMP</span>
                  <span className="text-white">{formatDateTime(selectedEvent.timestamp)}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block text-[10px] uppercase">SESSION ID</span>
                  <span className="text-white">{selectedEvent.session_id}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block text-[10px] uppercase">SOURCE NODE</span>
                  <span className="text-white">{selectedEvent.source_node}</span>
                </div>
              </div>

              {/* Quantum Measurement Section */}
              <div className="p-3.5 bg-zinc-950/80 rounded-lg border border-zinc-850 space-y-2.5">
                <span className="text-zinc-300 font-semibold uppercase text-[11px] block tracking-wider">
                  Quantum State Analysis
                </span>
                <div className="grid grid-cols-3 gap-2.5 text-center">
                  <div className="p-2.5 bg-zinc-900 rounded border border-zinc-800">
                    <span className="text-zinc-500 block text-[10px]">EXPECTED</span>
                    <span className="text-white font-bold">{selectedEvent.expected_measurement?.toFixed(4) ?? "--"}</span>
                  </div>
                  <div className="p-2.5 bg-zinc-900 rounded border border-zinc-800">
                    <span className="text-zinc-500 block text-[10px]">OBSERVED</span>
                    <span className="text-white font-bold">{selectedEvent.observed_measurement?.toFixed(4) ?? "--"}</span>
                  </div>
                  <div className="p-2.5 bg-zinc-900 rounded border border-zinc-800">
                    <span className="text-zinc-500 block text-[10px]">DEVIATION</span>
                    <span
                      className={`font-bold ${
                        (selectedEvent.measurement_deviation ?? 0) > 0.3 ? "text-red-400" : "text-emerald-400"
                      }`}
                    >
                      {selectedEvent.measurement_deviation !== null
                        ? formatPercent(selectedEvent.measurement_deviation * 100)
                        : "--"}
                    </span>
                  </div>
                </div>
                {selectedEvent.quantum_state && (
                  <div className="pt-2 text-zinc-400 text-[11px]">
                    State Description: <span className="text-zinc-300">{selectedEvent.quantum_state}</span>
                  </div>
                )}
              </div>

              {/* Blockchain Block Hash Section */}
              {selectedEvent.audit_block && (
                <div className="p-3.5 bg-zinc-950/80 rounded-lg border border-zinc-850 space-y-2">
                  <div className="flex items-center gap-1.5 text-emerald-400 text-[11px] font-semibold uppercase">
                    <Lock className="w-3.5 h-3.5" />
                    <span>Audit Hash Block #{selectedEvent.audit_block.block_index}</span>
                  </div>
                  <div className="space-y-1 text-[11px] text-zinc-400 break-all">
                    <div>
                      <span className="text-zinc-500">Block Hash:</span>{" "}
                      <span className="text-emerald-400 font-mono">{selectedEvent.audit_block.block_hash}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500">Prev Hash:</span>{" "}
                      <span className="text-zinc-500 font-mono">{selectedEvent.audit_block.previous_hash}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500">Payload Hash:</span>{" "}
                      <span className="text-zinc-500 font-mono">{selectedEvent.audit_block.payload_hash}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 pt-3 border-t border-zinc-800 flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-1.5 rounded-lg text-xs bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
