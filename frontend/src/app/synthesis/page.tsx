"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { API_BASE } from "@/lib/api";

interface SynthesisRecord {
  id: number;
  ticker: string;
  date: string;
  archetype: string;
  retail_rank: number | null;
  retail_mentions: number;
  retail_sentiment: string | null;
  smart_money_rank: number | null;
  smart_money_conviction: number;
  smart_money_flow: string | null;
  retail_awareness_level: string;
  timing_edge_score: number;
  synthesis_diagnosis: string;
  recommended_action: string;
  whale_options_flow?: string | null;
  whale_options_score?: number;
  put_call_ratio?: number | null;
}

export default function SynthesisPage() {
  const [records, setRecords] = useState<SynthesisRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/api/synthesis/today`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load Synthesis Matrix data");
        return res.json();
      })
      .then((data) => {
        setRecords(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const getArchetypeBadge = (archetype: string) => {
    switch (archetype) {
      case "The Rocket":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            🚀 The Rocket
          </span>
        );
      case "The Retail Trap":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            🪤 The Retail Trap
          </span>
        );
      case "Silent Accumulation":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
            🕵️‍♂️ Silent Accumulation
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">
            😴 Market Noise
          </span>
        );
    }
  };

  const getActionBadge = (action: string) => {
    if (action.includes("BUY")) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-black bg-emerald-500 text-slate-950 uppercase tracking-wider">
          {action}
        </span>
      );
    }
    if (action.includes("AVOID") || action.includes("SHORT")) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-black bg-rose-500 text-white uppercase tracking-wider">
          {action}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 uppercase tracking-wider">
        {action}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background Glow */}
      <div className="absolute top-0 left-0 right-0 h-[450px] bg-gradient-to-b from-purple-500/10 via-indigo-500/5 to-transparent pointer-events-none blur-[120px]" />

      <Navbar />

      <main className="max-w-6xl mx-auto px-6 py-12 relative">
        {/* Header */}
        <div className="mb-10 pb-6 border-b border-slate-800/80">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20 mb-3">
            <span>⚡</span> Cross-Engine Synthesis Hub
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
            Market Divergence & Archetype Matrix
          </h1>
          <p className="text-slate-400 text-sm mt-2 max-w-2xl leading-relaxed">
            Reconciles retail momentum from Reddit with institutional positioning from SEC Form 4 and Congressional filings.
          </p>
        </div>

        {/* 4 Archetype Guide Legend */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
            <span className="text-base mb-1 block">🚀</span>
            <h3 className="text-xs font-bold text-emerald-400">The Rocket</h3>
            <p className="text-[11px] text-slate-400 mt-0.5">High retail hype + heavy insider cluster buying. Full alignment breakout.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
            <span className="text-base mb-1 block">🪤</span>
            <h3 className="text-xs font-bold text-rose-400">The Retail Trap</h3>
            <p className="text-[11px] text-slate-400 mt-0.5">High retail hype + insider dumping. Retail acting as exit liquidity.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
            <span className="text-base mb-1 block">🕵️‍♂️</span>
            <h3 className="text-xs font-bold text-purple-400">Silent Accumulation</h3>
            <p className="text-[11px] text-slate-400 mt-0.5">Zero retail attention + heavy insider/political buying. Maximum timing edge.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60">
            <span className="text-base mb-1 block">😴</span>
            <h3 className="text-xs font-bold text-slate-400">Market Noise</h3>
            <p className="text-[11px] text-slate-400 mt-0.5">Routine activity without institutional edge or sentiment convergence.</p>
          </div>
        </div>

        {/* Loading / Error States */}
        {loading && (
          <div className="py-20 text-center flex flex-col items-center justify-center gap-3">
            <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 text-sm">Computing cross-engine correlations and timing edges...</p>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm mb-6">
            Failed to load synthesis matrix: {error}
          </div>
        )}

        {!loading && !error && records.length === 0 && (
          <div className="max-w-md mx-auto bg-slate-900/50 border border-slate-800 rounded-2xl p-8 text-center">
            <span className="text-3xl mb-3 block">⚖️</span>
            <h3 className="text-lg font-bold text-slate-300">No Synthesis records yet</h3>
            <p className="text-slate-500 text-sm mt-1">
              Run both Engine 1 (Retail) and Engine 2 (Smart Money) to generate today&apos;s synthesis matrix.
            </p>
          </div>
        )}

        {/* Synthesis Records Cards */}
        <div className="space-y-6">
          {records.map((r) => (
            <div
              key={r.id}
              className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm hover:border-purple-500/30 transition-all shadow-xl"
            >
              {/* Header Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/60">
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-black text-white">${r.ticker}</h2>
                  {getArchetypeBadge(r.archetype)}
                  {getActionBadge(r.recommended_action)}
                </div>

                <div className="flex items-center gap-4 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider">Timing Edge</span>
                    <span className="font-black text-purple-400 text-sm">{r.timing_edge_score.toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider">Retail Awareness</span>
                    <span className="font-bold text-slate-300">{r.retail_awareness_level}</span>
                  </div>
                </div>
              </div>

              {/* Diagnosis Callout */}
              <div className="my-4 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60 text-xs leading-relaxed text-slate-200">
                <span className="text-slate-400 font-bold block mb-1">Diagnosis:</span>
                {r.synthesis_diagnosis}
              </div>

              {/* Multi-Engine Signal Comparison */}
              <div className={`grid grid-cols-1 ${r.whale_options_flow ? "md:grid-cols-3" : "md:grid-cols-2"} gap-4 text-xs`}>
                {/* Engine 1: Retail View */}
                <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/40">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-indigo-400 flex items-center gap-1.5">
                      <span>📱</span> Engine 1: Retail Momentum
                    </span>
                    {r.retail_rank && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold">
                        Rank #{r.retail_rank}
                      </span>
                    )}
                  </div>
                  <div className="space-y-1 text-slate-300">
                    <p><span className="text-slate-500">Reddit Mentions:</span> <span className="font-bold">{r.retail_mentions}</span></p>
                    <p><span className="text-slate-500">Community Sentiment:</span> {r.retail_sentiment || "None"}</p>
                  </div>
                </div>

                {/* Engine 2: Smart Money View */}
                <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/40">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-purple-400 flex items-center gap-1.5">
                      <span>🏛️</span> Engine 2: Smart Money Scout
                    </span>
                    {r.smart_money_rank && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold">
                        Rank #{r.smart_money_rank}
                      </span>
                    )}
                  </div>
                  <div className="space-y-1 text-slate-300">
                    <p><span className="text-slate-500">Conviction Score:</span> <span className="font-bold text-purple-400">{r.smart_money_conviction.toFixed(1)}</span></p>
                    <p className="truncate"><span className="text-slate-500">Flow:</span> {r.smart_money_flow || "Neutral"}</p>
                  </div>
                </div>

                {/* Engine 3: Whale Options View */}
                {r.whale_options_flow && (
                  <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/40">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-cyan-400 flex items-center gap-1.5">
                        <span>🐳</span> Engine 3: Whale Options
                      </span>
                      {r.whale_options_score !== undefined && r.whale_options_score > 0 && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-cyan-400 font-semibold">
                          Score: {r.whale_options_score.toFixed(0)}
                        </span>
                      )}
                    </div>
                    <div className="space-y-1 text-slate-300">
                      <p className="truncate">
                        <span className="text-slate-500">Flow:</span> <span className="font-semibold text-cyan-300">{r.whale_options_flow}</span>
                      </p>
                      {r.put_call_ratio !== undefined && r.put_call_ratio !== null && (
                        <p>
                          <span className="text-slate-500">P/C Ratio:</span> <span className="font-bold text-slate-200">{r.put_call_ratio.toFixed(2)}</span>
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Links */}
              <div className="mt-4 pt-3 border-t border-slate-800/40 flex flex-wrap items-center justify-between gap-2 text-xs font-bold">
                <Link href={`/report/${r.ticker}`} className="text-indigo-400 hover:text-indigo-300 transition-colors">
                  View Unified Master Report &rarr;
                </Link>
                <div className="flex items-center gap-3">
                  <Link href={`/retail/${r.ticker}`} className="text-amber-400 hover:text-amber-300 transition-colors font-medium">
                    Retail Report &rarr;
                  </Link>
                  <Link href={`/smart-money/${r.ticker}`} className="text-purple-400 hover:text-purple-300 transition-colors font-medium">
                    Smart Money &rarr;
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

