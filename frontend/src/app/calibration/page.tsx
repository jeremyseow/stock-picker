"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { RetailTrapIcon } from "@/components/RetailTrapIcon";
import { API_BASE } from "@/lib/api";

interface ArchetypeMetric {
  archetype: string;
  sample_count: number;
  tracked_count?: number;
  t5_matured_count?: number;
  t5_win_rate?: number | null;
  t5_avg_alpha?: number | null;
  t30_matured_count?: number;
  win_rate_t30?: number | null;
  avg_alpha_t30?: number | null;
  status: string;
  recent_picks?: Array<{
    ticker: string;
    action: string;
    date: string;
    alpha: number | null;
    matured: boolean;
  }>;
}

interface HorizonMetric {
  is_matured: boolean;
  hit_rate?: number | null;
  avg_alpha?: number | null;
  max_drawdown?: number | null;
  matured_count: number;
  progress_days?: number;
  target_days?: number;
  target_count?: number;
}

interface MaturationMeta {
  inception_date: string;
  latest_run_date: string;
  calendar_days_elapsed: number;
  trading_days_elapsed: number;
  total_tracked_picks: number;
  t5_metrics: HorizonMetric;
  t15_metrics: HorizonMetric;
  t30_metrics: HorizonMetric;
}

interface LiveCohortRecord {
  ticker: string;
  archetype: string;
  discovery_date: string;
  action: string;
  entry_price: number | null;
  current_price: number | null;
  stock_ret: number | null;
  alpha_vs_spy: number | null;
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
  is_maturing?: boolean;
  maturation_meta?: MaturationMeta;
  sample_runs_count: number;
  overall_hit_rate_t30?: number | null;
  avg_alpha_vs_spy_t30?: number | null;
  max_drawdown?: number | null;
  hit_rate_t5?: number | null;
  avg_alpha_t5?: number | null;
  archetype_scorecard: Record<string, ArchetypeMetric>;
  live_cohort_records?: LiveCohortRecord[];
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
      await res.json();
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
            <span>Tracking live cohort maturation and empirical market alpha...</span>
          </div>
        </main>
      </div>
    );
  }

  const meta = data?.maturation_meta;
  const t5 = meta?.t5_metrics;
  const t15 = meta?.t15_metrics;
  const t30 = meta?.t30_metrics;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />
      <main className="flex-1 py-10 px-6">
        <div className="max-w-6xl mx-auto space-y-10">
          {/* Header */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-3">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Live Walk-Forward Maturation Tracker</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Model Calibration & Walk-Forward Performance Tracker
            </h1>
            <p className="mt-2 text-slate-400 max-w-3xl text-sm leading-relaxed">
              Longitudinally tracks live stock recommendations across T+5, T+15, and T+30 trading day horizons against
              the S&P 500 (<code>SPY</code>). Synthetic placeholders have been removed: this dashboard reflects genuine
              market returns as live trading sessions mature.
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
              {/* Inception & Live Horizon Maturation Progress */}
              <div className="rounded-2xl bg-slate-900/40 border border-slate-800 p-6 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
                  <div>
                    <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      System Inception & Observation Status
                    </div>
                    <div className="text-lg font-bold text-white mt-0.5">
                      First Report: <span className="text-indigo-400 font-mono">{meta?.inception_date || "2026-11-01"}</span>
                      <span className="text-slate-500 mx-2">•</span>
                      <span className="text-slate-300">{meta?.trading_days_elapsed ?? 5} Trading Days Elapsed</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-semibold font-mono">
                      {data.sample_runs_count} Total Tracked Picks
                    </span>
                  </div>
                </div>

                {/* 3 Horizon Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  {/* T+5 Horizon */}
                  <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        T+5 Short-Term Horizon
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        🟢 Active ({t5?.matured_count || 0} Matured)
                      </span>
                    </div>

                    <div className="flex items-baseline justify-between pt-1">
                      <div>
                        <div className="text-2xl font-extrabold text-emerald-400 font-mono">
                          {t5?.hit_rate !== null && t5?.hit_rate !== undefined ? `${t5.hit_rate}%` : "—"}
                        </div>
                        <div className="text-[11px] text-slate-400">Hit Rate vs SPY</div>
                      </div>
                      <div className="text-right">
                        <div className={`text-xl font-bold font-mono ${Number(t5?.avg_alpha) >= 0 ? "text-indigo-400" : "text-amber-400"}`}>
                          {t5?.avg_alpha !== null && t5?.avg_alpha !== undefined
                            ? Number(t5.avg_alpha) >= 0
                              ? `+${t5.avg_alpha}%`
                              : `${t5.avg_alpha}%`
                            : "—"}
                        </div>
                        <div className="text-[11px] text-slate-400">Avg Excess Alpha</div>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                      Early reaction window. {t5?.matured_count || 0} picks completed 5 market sessions.
                    </div>
                  </div>

                  {/* T+15 Horizon */}
                  <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        T+15 Intermediate Swing
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        ⏳ Maturing ({meta?.trading_days_elapsed ?? 5}/15 Days)
                      </span>
                    </div>

                    <div className="space-y-1.5 pt-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-slate-300">Cohort Progress</span>
                        <span className="text-amber-400 font-mono">
                          {Math.round(((meta?.trading_days_elapsed ?? 5) / 15) * 100)}%
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-amber-400 rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(100, Math.round(((meta?.trading_days_elapsed ?? 5) / 15) * 100))}%`,
                          }}
                        />
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                      Unlocks after 10 more trading sessions (~Nov 21, 2026).
                    </div>
                  </div>

                  {/* T+30 Horizon */}
                  <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        T+30 Statistical Alpha
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        ⏳ Maturing ({meta?.trading_days_elapsed ?? 5}/30 Days)
                      </span>
                    </div>

                    <div className="space-y-1.5 pt-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-slate-300">Cohort Progress</span>
                        <span className="text-indigo-400 font-mono">
                          {Math.round(((meta?.trading_days_elapsed ?? 5) / 30) * 100)}%
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(100, Math.round(((meta?.trading_days_elapsed ?? 5) / 30) * 100))}%`,
                          }}
                        />
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                      Full multi-week alpha benchmark. Unlocks ~Dec 12, 2026.
                    </div>
                  </div>
                </div>
              </div>

              {/* Archetype Performance Pipeline */}
              <div className="rounded-2xl bg-slate-900/40 border border-slate-800 p-6 space-y-4">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>🎯 Archetype Cohort Observation Pipeline</span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Live breakdown of active recommendations grouped by market divergence classification.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {Object.values(data.archetype_scorecard || {}).map((arch) => {
                    const isRetailTrap = arch.archetype === "The Retail Trap";
                    const hasT5 = arch.t5_win_rate !== null && arch.t5_win_rate !== undefined;

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
                        className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between space-y-3"
                      >
                        <div className="flex items-start justify-between gap-2 min-w-0">
                          <div className="flex items-center gap-1.5 font-bold text-sm text-slate-200 leading-snug">
                            {renderIcon()}
                            <span>{arch.archetype}</span>
                          </div>
                          <span className={`text-[10px] px-2 py-0.5 rounded-md font-bold whitespace-nowrap shrink-0 ${
                            hasT5
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-slate-800 text-slate-400 border border-slate-700/50"
                          }`}>
                            {hasT5 ? "T+5 Matured" : "Observing"}
                          </span>
                        </div>

                        <div className="pt-1 flex items-baseline justify-between">
                          <div>
                            <div className="text-2xl font-extrabold text-white font-mono">
                              {arch.tracked_count ?? arch.sample_count}
                            </div>
                            <div className="text-[11px] text-slate-400">Tracked Picks</div>
                          </div>
                          <div className="text-right">
                            {hasT5 ? (
                              <>
                                <div className={`text-lg font-bold font-mono ${
                                  isRetailTrap
                                    ? "text-amber-400"
                                    : Number(arch.t5_avg_alpha) >= 0
                                    ? "text-emerald-400"
                                    : "text-rose-400"
                                }`}>
                                  {Number(arch.t5_avg_alpha) >= 0 ? `+${arch.t5_avg_alpha}%` : `${arch.t5_avg_alpha}%`}
                                </div>
                                <div className="text-[11px] text-slate-400">T+5 Avg Alpha</div>
                              </>
                            ) : (
                              <>
                                <div className="text-sm font-semibold text-slate-500">Maturing</div>
                                <div className="text-[11px] text-slate-500">T+5 Pending</div>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Recent observed picks in this archetype */}
                        <div className="pt-2 border-t border-slate-800/60 space-y-1">
                          <span className="text-[10px] uppercase font-bold text-slate-500">Sample Live Picks:</span>
                          <div className="flex flex-wrap gap-1.5 pt-0.5">
                            {(arch.recent_picks || []).map((pick, pIdx) => (
                              <span
                                key={pIdx}
                                className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 font-mono flex items-center gap-1"
                              >
                                <span className="font-bold text-slate-200">${pick.ticker}</span>
                                {pick.alpha !== null && pick.alpha !== undefined && (
                                  <span className={`text-[10px] ${pick.alpha >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                                    {pick.alpha >= 0 ? `+${pick.alpha}%` : `${pick.alpha}%`}
                                  </span>
                                )}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Archetype Guide */}
                <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 space-y-3 mt-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm shrink-0">💡</span>
                    <span className="font-bold text-slate-200 text-xs uppercase tracking-wider">
                      Archetype Scoring & Execution Reference
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-slate-300 text-[11px]">
                    <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 space-y-1">
                      <div className="font-bold text-purple-300 flex items-center gap-1.5">
                        <span>🚀</span> The Rocket
                      </div>
                      <p className="text-slate-400 leading-snug">
                        Full directional alignment: strong retail momentum validated by institutional Form 4 buying and call sweeps.
                      </p>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 space-y-1">
                      <div className="font-bold text-emerald-300 flex items-center gap-1.5">
                        <span>🤫</span> Silent Accumulation
                      </div>
                      <p className="text-slate-400 leading-snug">
                        Stealth institutional accumulation with dormant retail hype (&lt;10 mentions). Maximum asymmetric pre-discovery edge.
                      </p>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 space-y-1">
                      <div className="font-bold text-rose-400 flex items-center gap-1.5">
                        <RetailTrapIcon className="w-3.5 h-3.5 shrink-0" />
                        The Retail Trap
                      </div>
                      <p className="text-slate-400 leading-snug">
                        Defensive warning: retail euphoria while insiders are selling or options skew bearish. Avoid or trade contrarian.
                      </p>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 space-y-1">
                      <div className="font-bold text-slate-300 flex items-center gap-1.5">
                        <span>📢</span> Market Noise
                      </div>
                      <p className="text-slate-400 leading-snug">
                        Neutral baseline: sub-threshold conviction without institutional edge. Pass to avoid dead money consolidation.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Live Cohort Stream Table */}
              {data.live_cohort_records && data.live_cohort_records.length > 0 && (
                <div className="rounded-2xl bg-slate-900/40 border border-slate-800 p-6 space-y-4">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                    <div>
                      <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <span>📡 Live Cohort Maturation Stream</span>
                      </h2>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Real-time tracking of active recommendations against the S&P 500 (SPY) benchmark.
                      </p>
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                      Showing latest 15 tracked picks
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-slate-300">
                      <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                        <tr>
                          <th className="py-3 px-4">Ticker</th>
                          <th className="py-3 px-4">Archetype</th>
                          <th className="py-3 px-4">Discovery Date</th>
                          <th className="py-3 px-4">Action</th>
                          <th className="py-3 px-4 text-right">Entry Price</th>
                          <th className="py-3 px-4 text-right">Latest / T+5 Price</th>
                          <th className="py-3 px-4 text-right">Stock Return</th>
                          <th className="py-3 px-4 text-right">Alpha vs SPY</th>
                          <th className="py-3 px-4 text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                        {data.live_cohort_records.map((row, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/30 transition-colors">
                            <td className="py-3.5 px-4 font-bold text-white font-sans text-sm">
                              ${row.ticker}
                            </td>
                            <td className="py-3.5 px-4 font-sans text-xs">
                              <span className="inline-block px-2 py-0.5 rounded bg-slate-800 text-slate-200">
                                {row.archetype}
                              </span>
                            </td>
                            <td className="py-3.5 px-4 text-slate-400">{row.discovery_date}</td>
                            <td className="py-3.5 px-4 font-sans text-xs">
                              <span className={`inline-block px-2 py-0.5 rounded font-bold ${
                                row.action.includes("BUY")
                                  ? "bg-emerald-500/10 text-emerald-400"
                                  : row.action.includes("AVOID")
                                  ? "bg-rose-500/10 text-rose-400"
                                  : "bg-slate-800 text-slate-400"
                              }`}>
                                {row.action}
                              </span>
                            </td>
                            <td className="py-3.5 px-4 text-right text-slate-300">
                              {row.entry_price ? `$${row.entry_price.toFixed(2)}` : "—"}
                            </td>
                            <td className="py-3.5 px-4 text-right text-slate-300">
                              {row.current_price ? `$${row.current_price.toFixed(2)}` : "—"}
                            </td>
                            <td className={`py-3.5 px-4 text-right font-bold ${
                              row.stock_ret !== null && row.stock_ret !== undefined
                                ? row.stock_ret >= 0
                                  ? "text-emerald-400"
                                  : "text-rose-400"
                                : "text-slate-400"
                            }`}>
                              {row.stock_ret !== null && row.stock_ret !== undefined
                                ? `${row.stock_ret >= 0 ? "+" : ""}${row.stock_ret}%`
                                : "—"}
                            </td>
                            <td className={`py-3.5 px-4 text-right font-bold ${
                              row.alpha_vs_spy !== null && row.alpha_vs_spy !== undefined
                                ? row.alpha_vs_spy >= 0
                                  ? "text-indigo-400"
                                  : "text-amber-400"
                                : "text-slate-400"
                            }`}>
                              {row.alpha_vs_spy !== null && row.alpha_vs_spy !== undefined
                                ? `${row.alpha_vs_spy >= 0 ? "+" : ""}${row.alpha_vs_spy}%`
                                : "—"}
                            </td>
                            <td className="py-3.5 px-4 text-center font-sans">
                              <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold ${
                                row.status.includes("Matured")
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                  : "bg-slate-800 text-slate-400"
                              }`}>
                                {row.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

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
