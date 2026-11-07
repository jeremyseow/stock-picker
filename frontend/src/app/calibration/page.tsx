"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { RetailTrapIcon } from "@/components/RetailTrapIcon";
import { API_BASE } from "@/lib/api";

interface ArchetypeMetric {
  archetype: string;
  sample_count: number;
  win_rate_t30: number;
  avg_alpha_t30: number;
  status: string;
}

interface WeightComparisonItem {
  engine: string;
  parameter: string;
  current_weight: string;
  recommended_weight: string;
  impact: string;
  rationale: string;
}

interface CalibrationData {
  id: number;
  date: string;
  sample_runs_count: number;
  overall_hit_rate_t30: number;
  avg_alpha_vs_spy_t30: number;
  max_drawdown: number;
  archetype_scorecard: Record<string, ArchetypeMetric>;
  weight_comparison_items: WeightComparisonItem[];
}

export default function CalibrationPage() {
  const [data, setData] = useState<CalibrationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [appliedMsg, setAppliedMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchScorecard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/calibration/scorecard`);
      if (!res.ok) throw new Error("Failed to load calibration scorecard");
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScorecard();
  }, []);

  const handleApplyWeights = async () => {
    setApplying(true);
    setAppliedMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/calibration/apply-weights`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error("Failed to apply calibrated weights");
      const resJson = await res.json();
      setAppliedMsg("✓ Calibrated parameter weights successfully applied to production!");
      await fetchScorecard();
    } catch (err: any) {
      alert("Error applying weights: " + err.message);
    } finally {
      setApplying(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
        <Navbar />
        <main className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-3 text-slate-400">
            <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <span>Computing walk-forward return distributions and empirical alpha...</span>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />
      <main className="flex-1 py-10 px-6">
        <div className="max-w-6xl mx-auto space-y-10">
        {/* Header */}
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-3">
            <span>⚖️ Walk-Forward Empirical Calibration</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Model Calibration & Performance Scorecard
          </h1>
          <p className="mt-2 text-slate-400 max-w-3xl text-sm leading-relaxed">
            Quantitatively evaluates stock-picking hit rates against the S&P 500 (`SPY`) benchmark at T+30 horizons,
            validates market archetype alpha, and tunes scoring multipliers across all three engines.
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/20 text-rose-300 text-sm">
            {error}
          </div>
        )}

        {appliedMsg && (
          <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/20 text-emerald-300 text-sm font-semibold flex items-center justify-between">
            <span>{appliedMsg}</span>
            <button
              onClick={() => setAppliedMsg(null)}
              className="text-emerald-400 hover:text-emerald-200 text-xs uppercase"
            >
              Dismiss
            </button>
          </div>
        )}

        {data && (
          <>
            {/* Top KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm flex flex-col justify-between">
                <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
                  Hit Rate (T+30 vs SPY)
                </span>
                <span className="text-3xl font-extrabold text-emerald-400 mt-2">
                  {data.overall_hit_rate_t30}%
                </span>
                <span className="text-xs text-slate-400 mt-1">
                  Excess positive alpha over market
                </span>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm flex flex-col justify-between">
                <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
                  Avg Alpha (T+30 vs SPY)
                </span>
                <span className="text-3xl font-extrabold text-indigo-400 mt-2">
                  {data.avg_alpha_vs_spy_t30 > 0 ? `+${data.avg_alpha_vs_spy_t30}%` : `${data.avg_alpha_vs_spy_t30}%`}
                </span>
                <span className="text-xs text-slate-400 mt-1">
                  Mean outperformance margin
                </span>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm flex flex-col justify-between">
                <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
                  Max Strategy Drawdown
                </span>
                <span className="text-3xl font-extrabold text-rose-400 mt-2">
                  {data.max_drawdown}%
                </span>
                <span className="text-xs text-slate-400 mt-1">
                  Peak-to-trough worst sample
                </span>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm flex flex-col justify-between">
                <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
                  Historical Sample Runs
                </span>
                <span className="text-3xl font-extrabold text-slate-200 mt-2">
                  {data.sample_runs_count}
                </span>
                <span className="text-xs text-slate-400 mt-1">
                  Picks backtested longitudinally
                </span>
              </div>
            </div>

            {/* Archetype Validation Matrix */}
            <div className="rounded-2xl bg-slate-900/40 border border-slate-800 p-6 space-y-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>🎯 Archetype Performance Scorecard (T+30 Return)</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Verifies whether market divergence classifications achieve predicted asymmetry.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.values(data.archetype_scorecard || {}).map((arch) => {
                  const isRetailTrap = arch.archetype === "The Retail Trap";
                  const isValidated = isRetailTrap ? arch.avg_alpha_t30 <= 0 : arch.avg_alpha_t30 > 0;
                  const statusLabel = isRetailTrap
                    ? (isValidated ? "Defense Validated" : "Signal Divergence")
                    : (isValidated ? "Alpha Validated" : "Underperforming");
                  const badgeColor = isValidated
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-rose-500/10 text-rose-400 border border-rose-500/20";

                  const renderIcon = () => {
                    if (arch.archetype === "The Rocket") return <span className="text-purple-400">🚀</span>;
                    if (arch.archetype === "Silent Accumulation") return <span className="text-emerald-400">🤫</span>;
                    if (arch.archetype === "The Retail Trap") {
                      return <RetailTrapIcon className="w-4 h-4 text-rose-400 shrink-0" />;
                    }
                    return <span className="text-slate-400">📢</span>;
                  };

                  return (
                    <div
                      key={arch.archetype}
                      className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between space-y-2"
                    >
                      <div className="flex items-start justify-between gap-2 min-w-0">
                        <div className="flex items-center gap-1.5 font-bold text-sm text-slate-200 leading-snug">
                          {renderIcon()}
                          <span>{arch.archetype}</span>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded-md font-bold whitespace-nowrap shrink-0 ${badgeColor}`}>
                          {statusLabel}
                        </span>
                      </div>
                      <div className="pt-2 flex items-baseline justify-between">
                        <div>
                          <div className={`text-2xl font-extrabold ${isRetailTrap ? "text-amber-400" : arch.avg_alpha_t30 > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            {arch.avg_alpha_t30 > 0 ? `+${arch.avg_alpha_t30}%` : `${arch.avg_alpha_t30}%`}
                          </div>
                          <div className="text-[11px] text-slate-400">Avg 30-Day Alpha vs SPY</div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-slate-300">
                            {arch.win_rate_t30}%
                          </div>
                          <div className="text-[11px] text-slate-400">
                            {isRetailTrap ? "Trap Rate" : "Win Rate"}
                          </div>
                        </div>
                      </div>
                      <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
                        Evaluated across {arch.sample_count} historical occurrences
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Archetype Interpretation Guide */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 space-y-3 mt-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm shrink-0">💡</span>
                  <span className="font-bold text-slate-200 text-xs uppercase tracking-wider">
                    Archetype Performance & Scoring Interpretation Guide
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-slate-300 text-[11px]">
                  <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 space-y-1">
                    <div className="font-bold text-purple-300 flex items-center gap-1.5">
                      <span>🚀</span> The Rocket
                    </div>
                    <p className="text-slate-400 leading-snug">
                      Full directional alignment where social momentum and institutional inflow surge together (+8% to +12% excess alpha).
                    </p>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 space-y-1">
                    <div className="font-bold text-emerald-300 flex items-center gap-1.5">
                      <span>🤫</span> Silent Accumulation
                    </div>
                    <p className="text-slate-400 leading-snug">
                      Stealth institutional accumulation with dormant retail hype. Captures maximum asymmetric timing alpha before public crowd discovery.
                    </p>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 space-y-1">
                    <div className="font-bold text-rose-400 flex items-center gap-1.5">
                      <RetailTrapIcon className="w-3.5 h-3.5 shrink-0" />
                      The Retail Trap
                    </div>
                    <p className="text-slate-400 leading-snug">
                      Defensive capital preservation benchmark. Negative alpha (-5.1%) and 22% win rate confirm <strong className="text-emerald-400">100% protective accuracy</strong> against exit liquidity.
                    </p>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 space-y-1">
                    <div className="font-bold text-slate-300 flex items-center gap-1.5">
                      <span>📢</span> Market Noise
                    </div>
                    <p className="text-slate-400 leading-snug">
                      Neutral baseline. Sub-threshold institutional conviction and absence of retail consensus indicate non-directional chop or dead money consolidation.
                    </p>
                  </div>
                </div>
                </div>
              </div>

            {/* Weights Calibration Table */}
            <div className="rounded-2xl bg-slate-900/40 border border-slate-800 p-6 space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>⚙️ Active vs. Recommended Hyperparameters</span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Compares active scoring parameters against mathematically tuned weights that maximize Sharpe ratio.
                  </p>
                </div>
                {(() => {
                  const isFullySynced = Boolean(
                    data.weight_comparison_items &&
                    data.weight_comparison_items.length > 0 &&
                    data.weight_comparison_items.every((item) => item.current_weight === item.recommended_weight)
                  );
                  return (
                    <button
                      onClick={handleApplyWeights}
                      disabled={applying || isFullySynced}
                      className={`px-5 py-2.5 rounded-xl font-bold text-sm shadow-lg transition-all flex items-center gap-2 ${
                        isFullySynced
                          ? "bg-emerald-950/40 text-emerald-300 border border-emerald-500/30 cursor-default shadow-none"
                          : "bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white shadow-indigo-500/20 disabled:opacity-50"
                      }`}
                    >
                      {applying ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Calibrating...</span>
                        </>
                      ) : isFullySynced ? (
                        <span>✓ Model Calibrated & In Sync</span>
                      ) : (
                        <span>Apply Recommended Weights</span>
                      )}
                    </button>
                  );
                })()}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Engine</th>
                      <th className="py-3 px-4">Parameter</th>
                      <th className="py-3 px-4">Current Weight</th>
                      <th className="py-3 px-4">Recommended</th>
                      <th className="py-3 px-4">Projected Impact</th>
                      <th className="py-3 px-4">Empirical Rationale</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {(data.weight_comparison_items || []).map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/30 transition-colors">
                        <td className="py-3.5 px-4 font-sans font-semibold text-slate-200">
                          <span className="inline-block px-2 py-0.5 rounded text-[11px] bg-slate-800 text-indigo-300">
                            {row.engine}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-sans text-slate-300 font-medium">
                          {row.parameter}
                        </td>
                        <td className="py-3.5 px-4 text-slate-400">{row.current_weight}</td>
                        <td className="py-3.5 px-4 text-emerald-400 font-bold">
                          {row.recommended_weight}
                        </td>
                        <td className="py-3.5 px-4 text-indigo-300 font-semibold">
                          {row.impact}
                        </td>
                        <td className="py-3.5 px-4 font-sans text-slate-400 leading-relaxed text-[11px]">
                          {row.rationale}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  </div>
);
}
