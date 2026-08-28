"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  Activity,
  AlertTriangle,
  FileText,
  Settings as SettingsIcon,
  Atom,
  Lock,
  RefreshCw,
  Play,
  Cpu,
} from "lucide-react";
import { api } from "@/lib/api";

interface NavbarProps {
  wsConnected?: boolean;
  onRefresh?: () => void;
  onRunSimulator?: () => void;
}

export function Navbar({ wsConnected = false, onRefresh, onRunSimulator }: NavbarProps) {
  const pathname = usePathname();
  const [isVerifying, setIsVerifying] = useState(false);
  const [ledgerMessage, setLedgerMessage] = useState<string | null>(null);

  const navItems = [
    { label: "Dashboard", href: "/", icon: Activity },
    { label: "Logs & Events", href: "/logs", icon: FileText },
    { label: "Threats", href: "/threats", icon: AlertTriangle },
    { label: "Defense & IPS", href: "/security", icon: Shield },
    { label: "Test Lab", href: "/test-lab", icon: Atom },
    { label: "Hardware Link", href: "/hardware", icon: Cpu },
    { label: "Reports", href: "/reports", icon: FileText },
    { label: "Settings", href: "/settings", icon: SettingsIcon },
  ];


  const handleVerifyLedger = async () => {
    setIsVerifying(true);
    setLedgerMessage(null);
    try {
      const res = await api.verifyLedger();
      setLedgerMessage(res.valid ? "Ledger: VALID" : "Ledger: COMPROMISED");
      setTimeout(() => setLedgerMessage(null), 4000);
    } catch {
      setLedgerMessage("Ledger Error");
      setTimeout(() => setLedgerMessage(null), 4000);
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-[#09090b]/95 backdrop-blur-xl border-b border-[#23232a] shadow-premium">
      <div className="max-w-[1720px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center gap-3.5">
            <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-zinc-900 border border-zinc-700/60 text-zinc-100 shadow-inner">
              <Atom className="w-5 h-5 animate-spin-slow text-zinc-300" />
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-zinc-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm tracking-wider text-white">QDS·SIEM</span>
                <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 font-mono">
                  ENTERPRISE SOC
                </span>
              </div>
              <p className="text-[10px] text-zinc-500 font-mono tracking-tight">Quantum Threat Architecture</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 bg-zinc-950/60 p-1 rounded-lg border border-zinc-850">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium tracking-wide transition-all ${
                    isActive
                      ? "bg-zinc-800 text-white shadow-sm border border-zinc-700/80"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60 border border-transparent"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-white" : "text-zinc-500"}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Top Actions & Live Status */}
          <div className="flex items-center gap-2.5">
            {/* Ledger Verify Button */}
            <button
              onClick={handleVerifyLedger}
              disabled={isVerifying}
              title="Audit Hash-Chain Verification"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-zinc-900/80 hover:bg-zinc-850 border border-zinc-800 text-zinc-300 hover:text-white transition-all shadow-sm"
            >
              <Lock className={`w-3.5 h-3.5 ${isVerifying ? "animate-spin text-zinc-400" : "text-zinc-500"}`} />
              <span className="hidden sm:inline">
                {isVerifying ? "Verifying..." : ledgerMessage || "Verify Ledger"}
              </span>
            </button>

            {/* Run Simulation Button */}
            {onRunSimulator && (
              <button
                onClick={onRunSimulator}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-zinc-100 hover:bg-white text-zinc-950 font-semibold shadow-md transition-all hover:shadow-glow"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span className="hidden sm:inline">Simulate Threat</span>
              </button>
            )}

            {/* Refresh Button */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                title="Refresh All Telemetry"
                className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 border border-zinc-800 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            )}

            {/* Live Indicator */}
            <div className="flex items-center gap-2 pl-2 border-l border-zinc-800">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900/90 border border-zinc-800">
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    wsConnected ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" : "bg-zinc-600"
                  }`}
                />
                <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider hidden lg:inline">
                  {wsConnected ? "LIVE" : "OFFLINE"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
