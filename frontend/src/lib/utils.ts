import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateTime(isoString?: string | null): string {
  if (!isoString) return "--";
  try {
    // If string has no timezone indicator (Z or +offset or -offset), treat as UTC from backend
    let formatted = isoString;
    if (!formatted.endsWith("Z") && !/[+-]\d{2}(:\d{2})?$/.test(formatted)) {
      formatted += "Z";
    }
    const d = new Date(formatted);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString("en-US", {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return isoString;
  }
}

export function formatPercent(val?: number | null, decimals = 1): string {
  if (val === null || val === undefined) return "--";
  return `${val.toFixed(decimals)}%`;
}

export function formatHash(hash?: string | null, length = 12): string {
  if (!hash) return "--";
  if (hash.length <= length) return hash;
  return `${hash.slice(0, length / 2)}...${hash.slice(-length / 2)}`;
}
