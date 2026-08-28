"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { TestLabRunParams, TestRunMetrics, TestResultDetail, TestRunSummary } from "@/lib/types";

export type TestLabState = "idle" | "running" | "completed" | "error";

export interface UseTestLabReturn {
  state: TestLabState;
  currentTestId: string | null;
  progress: { completed: number; total: number; percentage: number };
  metrics: TestRunMetrics | null;
  results: TestResultDetail[];
  summary: TestRunSummary | null;
  errorMessage: string | null;
  runTest: (params: TestLabRunParams) => Promise<void>;
  resetTest: () => void;
  loadHistoricalTest: (testId: string) => Promise<void>;
}

const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000";

export function useTestLab(onTestFinished?: () => void): UseTestLabReturn {
  const [state, setState] = useState<TestLabState>("idle");
  const [currentTestId, setCurrentTestId] = useState<string | null>(null);
  const [progress, setProgress] = useState({ completed: 0, total: 0, percentage: 0 });
  const [metrics, setMetrics] = useState<TestRunMetrics | null>(null);
  const [results, setResults] = useState<TestResultDetail[]>([]);
  const [summary, setSummary] = useState<TestRunSummary | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  const cleanupWs = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const loadHistoricalTest = useCallback(async (testId: string) => {
    try {
      setState("running");
      setErrorMessage(null);
      const data = await api.getTestRun(testId);
      setCurrentTestId(testId);
      setSummary(data.summary);
      setMetrics(data.metrics || null);
      setResults(data.results || []);
      setProgress({
        completed: data.summary?.total_runs || 0,
        total: data.summary?.total_runs || 0,
        percentage: 100,
      });
      setState("completed");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load test session");
      setState("error");
    }
  }, []);

  const runTest = useCallback(
    async (params: TestLabRunParams) => {
      try {
        cleanupWs();
        setState("running");
        setErrorMessage(null);
        setMetrics(null);
        setResults([]);
        setSummary(null);
        setProgress({ completed: 0, total: params.runs, percentage: 0 });

        // 1. Trigger test run on real FastAPI backend
        const res = await api.runTestLab(params);
        const testId = res.test_id;
        setCurrentTestId(testId);

        // 2. Open WebSocket for live progress
        const wsUrl = `${WS_BASE}/ws/test-lab/${testId}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = async (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === "test_progress" && data.test_id === testId) {
              setProgress({
                completed: data.completed,
                total: data.total,
                percentage: data.percentage,
              });
            } else if (data.type === "test_completed" && data.test_id === testId) {
              setProgress({
                completed: data.metrics?.total_runs || params.runs,
                total: data.metrics?.total_runs || params.runs,
                percentage: 100,
              });
              setMetrics(data.metrics);
              setState("completed");
              cleanupWs();

              // Fetch detailed result rows from backend
              try {
                const fullData = await api.getTestRun(testId);
                setSummary(fullData.summary);
                setResults(fullData.results || []);
              } catch (e) {
                console.error("Failed to fetch full test details:", e);
              }

              if (onTestFinished) onTestFinished();
            }
          } catch (e) {
            console.error("WS parse error:", e);
          }
        };

        ws.onerror = (e) => {
          console.warn("Test Lab WS encountered issue, falling back to polling:", e);
        };

        // 3. Fallback poller in case WebSocket disconnects or drops
        const pollInterval = setInterval(async () => {
          try {
            const check = await api.getTestRun(testId);
            if (check.summary?.status === "completed") {
              clearInterval(pollInterval);
              setSummary(check.summary);
              setMetrics(check.metrics);
              setResults(check.results || []);
              setProgress({
                completed: check.summary.total_runs,
                total: check.summary.total_runs,
                percentage: 100,
              });
              setState("completed");
              cleanupWs();
              if (onTestFinished) onTestFinished();
            }
          } catch (err) {
            // Ignore polling errors while running
          }
        }, 1500);

        // Clean poller after 2 minutes max
        setTimeout(() => clearInterval(pollInterval), 120000);
      } catch (err: any) {
        setErrorMessage(err.message || "Failed to start attack test");
        setState("error");
        cleanupWs();
      }
    },
    [cleanupWs, onTestFinished]
  );

  const resetTest = useCallback(() => {
    cleanupWs();
    setState("idle");
    setCurrentTestId(null);
    setProgress({ completed: 0, total: 0, percentage: 0 });
    setMetrics(null);
    setResults([]);
    setSummary(null);
    setErrorMessage(null);
  }, [cleanupWs]);

  useEffect(() => {
    return () => {
      cleanupWs();
    };
  }, [cleanupWs]);

  return {
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
  };
}
