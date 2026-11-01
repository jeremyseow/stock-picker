"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";

export interface ArchetypeHistoryPoint {
  id: number;
  date: string;
  archetype: string;
  timing_edge_score: number;
  retail_awareness_level: string;
  retail_mentions: number;
  smart_money_conviction: string;
  synthesis_diagnosis?: string;
  recommended_action: string;
}

interface ArchetypeLifecycleTimelineProps {
  ticker: string;
}

export default function ArchetypeLifecycleTimeline({ ticker }: ArchetypeLifecycleTimelineProps) {
  const [history, setHistory] = useState<ArchetypeHistoryPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError("");

    fetch(`${API_BASE}/api/analytics/ticker/${ticker}/archetypes`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load archetype lifecycle for ${ticker}`);
        return res.json();
      })
      .then((data: ArchetypeHistoryPoint[]) => {
        setHistory(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [ticker]);

  const getArchetypeConfig = (archetype: string) => {
    const arch = archetype.toLowerCase();
    if (arch.includes("rocket") || arch.includes("front-running")) {
      return {
        badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
        dot: "bg-emerald-500 ring-emerald-500/30",
        icon: "🚀",
        label: "The Rocket",
        desc: "Front-Running Institutional Flow",
      };
    }
    if (arch.includes("silent") || arch.includes("accumulation") || arch.includes("stealth")) {
      return {
        badge: "bg-blue-500/10 text-blue-400 border-blue-500/30",
        dot: "bg-blue-500 ring-blue-500/30",
        icon: "🤫",
        label: "Silent Accumulation",
        desc: "Early Inflow / Stealth",
      };
    }
    if (arch.includes("trap") || arch.includes("exit") || arch.includes("bagholder")) {
      return {
        badge: "bg-rose-500/10 text-rose-400 border-rose-500/30",
        dot: "bg-rose-500 ring-rose-500/30",
        icon: "🪤",
        label: "The Retail Trap",
        desc: "Smart Money Exit / Bagholder Risk",
      };
    }
    return {
      badge: "bg-slate-500/10 text-slate-400 border-slate-500/30",
      dot: "bg-slate-500 ring-slate-500/30",
      icon: "💤",
      label: "Market Noise",
      desc: "Low Conviction / Indifferent Flow",
    };
  };

  const getActionBadge = (action: string) => {
    const act = (action || "").toUpperCase();
    if (act.includes("BUY")) {
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    }
    if (act.includes("SELL") || act.includes("EXIT")) {
      return "bg-rose-500/10 text-rose-400 border-rose-500/20";
    }
    if (act.includes("ACCUMULATE")) {
      return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    }
    return "bg-slate-500/10 text-slate-400 border-slate-500/20";
  };

  return (
    <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">🧬</span>
            <h3 className="text-lg font-black text-white">Archetype Lifecycle Progression</h3>
          </div>
          <p className="text-xs text-slate-400">
            Multi-run tracking of how ${ticker} migrates between Institutional Stealth, Retail Frenzy, and Exit Traps
          </p>
        </div>
        {history.length > 0 && (
          <span className="self-start sm:self-auto text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700/80 font-mono">
            {history.length} Lifecycle State{history.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {loading ? (
        <div className="py-12 flex flex-col items-center justify-center gap-3">
          <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-500">Querying archetype divergence trajectory...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
          {error}
        </div>
      ) : history.length === 0 ? (
        <div className="py-10 text-center rounded-xl bg-slate-900/20 border border-slate-800/60 p-6">
          <span className="text-2xl mb-2 block">📡</span>
          <p className="text-sm font-semibold text-slate-300 mb-1">No Archetype Transitions Logged</p>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Cross-engine synthesis has not yet evaluated ${ticker} across multiple pipeline runs.
            Once synthesis executes on upcoming cycles, its market divergence path will appear here.
          </p>
        </div>
      ) : (
        <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-[11px] sm:before:left-[15px] before:top-3 before:bottom-3 before:w-[2px] before:bg-gradient-to-b before:from-indigo-500 before:via-purple-500 before:to-slate-800">
          {history.map((item, idx) => {
            const config = getArchetypeConfig(item.archetype);
            const dateStr = new Date(item.date).toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
            });
            const isLatest = idx === history.length - 1;

            return (
              <div key={item.id} className="relative group">
                {/* Node indicator */}
                <div
                  className={`absolute -left-[30px] sm:-left-[35px] top-1.5 w-4 h-4 rounded-full ring-4 ${
                    isLatest ? `${config.dot} ring-indigo-500/40 animate-pulse` : `${config.dot} ring-slate-900`
                  }`}
                />

                <div className="bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 rounded-xl p-4 transition-all">
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="text-base">{config.icon}</span>
                      <span className="text-xs font-mono font-bold text-slate-300">{dateStr}</span>
                      {isLatest && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
                          Current
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${config.badge}`}>
                        {config.label}
                      </span>
                      <span
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${getActionBadge(
                          item.recommended_action
                        )}`}
                      >
                        {item.recommended_action}
                      </span>
                    </div>
                  </div>

                  {/* Metrics Row */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-2 px-3 rounded-lg bg-slate-950/40 border border-slate-800/60 mb-3 text-xs">
                    <div>
                      <span className="text-[10px] uppercase text-slate-500 font-semibold block">Timing Edge</span>
                      <span className="font-mono font-bold text-amber-400">
                        {item.timing_edge_score ? item.timing_edge_score.toFixed(1) : "0.0"}/10
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase text-slate-500 font-semibold block">Retail Phase</span>
                      <span className="font-medium text-slate-300 truncate block">
                        {item.retail_awareness_level || "Stealth"}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase text-slate-500 font-semibold block">Retail Mentions</span>
                      <span className="font-mono text-slate-300">{item.retail_mentions ?? 0}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase text-slate-500 font-semibold block">Smart Conviction</span>
                      <span className="font-medium text-indigo-400">{item.smart_money_conviction || "N/A"}</span>
                    </div>
                  </div>

                  {/* Diagnosis */}
                  {item.synthesis_diagnosis && (
                    <p className="text-xs text-slate-300 leading-relaxed italic border-l-2 border-slate-700 pl-3 py-0.5">
                      &ldquo;{item.synthesis_diagnosis}&rdquo;
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

