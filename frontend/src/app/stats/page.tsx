"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { RetailTrapIcon } from "@/components/RetailTrapIcon";
import { API_BASE } from "@/lib/api";

interface RetailReportItem {
  id: number;
  ticker: string;
  date: string;
  current_price: number | null;
  target_price: number | null;
  recommendation: "BUY" | "SELL" | "HOLD" | null;
  recommendation_rationale: string;
  smart_money_verdict?: string | null;
  community_sentiment: string;
  community_hype: string;
  ground_truth_status: string;
  reconciliation_risk_score: string;
  reconciliation_actionable_insight: string;
  industry: string;
  sector: string;
}

interface SmartMoneyReportItem {
  id: number;
  ticker: string;
  date: string;
  rank: number | null;
  company_name: string;
  sector: string;
  industry: string;
  current_price: number | null;
  target_price: number | null;
  conviction_score: number;
  conviction_tier: string;
  cluster_count: number;
  total_buy_volume: number;
  top_buyer_summary: string | null;
  catalyst_horizon: string | null;
  actionable_thesis: string | null;
  ground_truth_status: string | null;
  risk_score: string | null;
}

interface SynthesisRecordItem {
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
}

export default function HistoricalReportsPage() {
  const [dates, setDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"retail" | "smart-money" | "synthesis">("retail");

  const [retailReports, setRetailReports] = useState<RetailReportItem[]>([]);
  const [smartMoneyReports, setSmartMoneyReports] = useState<SmartMoneyReportItem[]>([]);
  const [synthesisReports, setSynthesisReports] = useState<SynthesisRecordItem[]>([]);

  const [loadingDates, setLoadingDates] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [error, setError] = useState("");

  // Fetch available distinct report dates
  useEffect(() => {
    fetch(`${API_BASE}/api/dates`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load historical dates");
        return res.json();
      })
      .then((data: string[]) => {
        setDates(data);
        if (data.length > 0) {
          setSelectedDate(data[0]);
        }
        setLoadingDates(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoadingDates(false);
      });
  }, []);

  // Fetch data across engines when selectedDate changes
  useEffect(() => {
    if (!selectedDate) return;
    setLoadingData(true);

    Promise.all([
      fetch(`${API_BASE}/api/retail/reports?date=${selectedDate}`).then((r) => (r.ok ? r.json() : [])),
      fetch(`${API_BASE}/api/smart-money/reports?date=${selectedDate}`).then((r) => (r.ok ? r.json() : [])),
      fetch(`${API_BASE}/api/synthesis/reports?date=${selectedDate}`).then((r) => (r.ok ? r.json() : [])),
    ])
      .then(([retailData, smartMoneyData, synthesisData]) => {
        setRetailReports(retailData || []);
        setSmartMoneyReports(smartMoneyData || []);
        setSynthesisReports(synthesisData || []);
        setLoadingData(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoadingData(false);
      });
  }, [selectedDate]);

  const getRecommendationBadge = (rec: "BUY" | "SELL" | "HOLD" | null) => {
    switch (rec) {
      case "BUY":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            🟢 BUY
          </span>
        );
      case "SELL":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            🔴 SELL
          </span>
        );
      case "HOLD":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            🟡 HOLD
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
            ⚪ NO REPORT
          </span>
        );
    }
  };

  const getRiskBadge = (score: string | null) => {
    switch (score?.toLowerCase()) {
      case "low":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "high":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      default:
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    }
  };

  const getSmartMoneyBadge = (verdict?: string | null) => {
    if (!verdict || verdict === "Neutral" || verdict === "No Form 4 Activity") {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
          No Cluster Buy
        </span>
      );
    }
    const lower = verdict.toLowerCase();
    if (lower.includes("bearish") || lower.includes("selling") || lower.includes("divergence")) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-950/80 text-rose-300 border border-rose-800">
          ⚠️ {verdict}
        </span>
      );
    }
    if (lower.includes("bullish") || lower.includes("buying") || lower.includes("accumulation")) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
          🏛️ {verdict}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-950/80 text-indigo-300 border border-indigo-800">
        🏛️ {verdict}
      </span>
    );
  };

  const getArchetypeBadge = (archetype: string) => {
    switch (archetype) {
      case "The Rocket":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-black bg-purple-500/20 text-purple-300 border border-purple-500/40">
            🚀 The Rocket
          </span>
        );
      case "The Retail Trap":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-black bg-rose-500/20 text-rose-300 border border-rose-500/40">
            <RetailTrapIcon className="w-3.5 h-3.5 text-rose-400 shrink-0" /> The Retail Trap
          </span>
        );
      case "Silent Accumulation":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-black bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            🤫 Silent Accumulation
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-black bg-slate-500/20 text-slate-300 border border-slate-500/40">
            📢 Market Noise
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header & Date Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold tracking-wider uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Multi-Engine Archives
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Historical Intelligence Archives
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm mt-1">
              Inspect archived daily pipeline runs across Retail Momentum, Smart Money Scout, and Synthesis Matrix.
            </p>
          </div>

          {/* Date Picker Selector */}
          <div className="flex items-center gap-3">
            <label htmlFor="date-select" className="text-xs font-semibold text-slate-400 whitespace-nowrap">
              Run Date:
            </label>
            {loadingDates ? (
              <div className="h-9 w-36 bg-slate-900 rounded-lg animate-pulse" />
            ) : dates.length === 0 ? (
              <span className="text-xs text-slate-500 italic">No runs recorded</span>
            ) : (
              <select
                id="date-select"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 text-sm font-semibold text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 hover:border-slate-600 transition-colors cursor-pointer"
              >
                {dates.map((d) => (
                  <option key={d} value={d} className="bg-slate-900 text-white">
                    {d}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab("retail")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === "retail"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            📊 Retail Momentum
            <span
              className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                activeTab === "retail" ? "bg-indigo-800 text-white" : "bg-slate-800 text-slate-400"
              }`}
            >
              {retailReports.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("smart-money")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === "smart-money"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            🏛️ Smart Money & Gov
            <span
              className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                activeTab === "smart-money" ? "bg-indigo-800 text-white" : "bg-slate-800 text-slate-400"
              }`}
            >
              {smartMoneyReports.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("synthesis")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === "synthesis"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            ⚡ Synthesis Matrix
            <span
              className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                activeTab === "synthesis" ? "bg-indigo-800 text-white" : "bg-slate-800 text-slate-400"
              }`}
            >
              {synthesisReports.length}
            </span>
          </button>
        </div>

        {/* Content Area */}
        {error ? (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            {error}
          </div>
        ) : loadingData ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 text-sm">Loading intelligence records for {selectedDate}...</p>
          </div>
        ) : (
          <>
            {/* TAB 1: RETAIL MOMENTUM */}
            {activeTab === "retail" && (
              retailReports.length === 0 ? (
                <div className="text-center py-20 bg-slate-900/30 border border-slate-800/80 rounded-2xl p-8">
                  <span className="text-3xl block mb-2">📊</span>
                  <p className="text-slate-300 font-semibold text-sm">No Retail Momentum reports recorded for {selectedDate}.</p>
                  <p className="text-slate-500 text-xs mt-1">Engine 1 was not recorded on this run date.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {retailReports.map((rep) => {
                      const upside =
                        rep.current_price && rep.target_price
                          ? (((rep.target_price - rep.current_price) / rep.current_price) * 100).toFixed(1)
                          : null;

                      return (
                        <div
                          key={rep.id}
                          className="group bg-slate-900/40 border border-slate-800/80 hover:border-slate-700/80 rounded-2xl p-6 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/5 flex flex-col justify-between backdrop-blur-sm"
                        >
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getRiskBadge(
                                  rep.reconciliation_risk_score
                                )}`}
                              >
                                Risk: {rep.reconciliation_risk_score || "Medium"}
                              </span>
                              {getRecommendationBadge(rep.recommendation)}
                            </div>

                            <div className="flex items-start justify-between gap-3 mb-4 min-w-0">
                              <div>
                                <span className="text-2xl font-black tracking-tight text-white group-hover:text-indigo-400 transition-colors">
                                  ${rep.ticker}
                                </span>
                                <span className="text-xs font-medium text-slate-400 block mt-0.5">
                                  {rep.sector} &bull; {rep.industry}
                                </span>
                              </div>
                              {getSmartMoneyBadge(rep.smart_money_verdict)}
                            </div>

                            <div className="grid grid-cols-3 gap-2 p-3 rounded-xl bg-slate-950/50 border border-slate-800/50 mb-4">
                              <div>
                                <span className="text-[10px] text-slate-400 font-medium block">Price</span>
                                <span className="text-sm font-bold text-white">
                                  {rep.current_price ? `$${rep.current_price.toFixed(2)}` : "N/A"}
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 font-medium block">Target</span>
                                <span className="text-sm font-bold text-slate-200">
                                  {rep.target_price ? `$${rep.target_price.toFixed(2)}` : "N/A"}
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 font-medium block">Upside</span>
                                <span
                                  className={`text-sm font-bold ${
                                    upside && parseFloat(upside) >= 0 ? "text-emerald-400" : "text-rose-400"
                                  }`}
                                >
                                  {upside ? `${parseFloat(upside) >= 0 ? "+" : ""}${upside}%` : "N/A"}
                                </span>
                              </div>
                            </div>

                            <div className="space-y-3 mb-6">
                              <div>
                                <span className="text-[11px] font-bold text-indigo-300 block mb-1">
                                  Reddit Sentiment: {rep.community_sentiment}
                                </span>
                                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                                  {rep.community_hype}
                                </p>
                              </div>
                              <div>
                                <span className="text-[11px] font-bold text-slate-300 block mb-1">
                                  Actionable Insight:
                                </span>
                                <p className="text-xs text-slate-400 line-clamp-2 italic">
                                  &ldquo;{rep.reconciliation_actionable_insight}&rdquo;
                                </p>
                              </div>
                            </div>
                          </div>

                          <div className="pt-4 border-t border-slate-800/60 flex items-center justify-between">
                            <Link
                              href={`/analytics?ticker=${rep.ticker}`}
                              className="text-xs font-semibold text-slate-400 hover:text-indigo-300 transition-colors"
                            >
                              📊 View Trajectory & Analytics &rarr;
                            </Link>
                            <Link
                              href={`/retail/${rep.ticker}`}
                              className="inline-flex items-center gap-1 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
                            >
                              View Retail Momentum Report &rarr;
                            </Link>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )
            )}

            {/* TAB 2: SMART MONEY & GOV */}
            {activeTab === "smart-money" && (
              smartMoneyReports.length === 0 ? (
                <div className="text-center py-20 bg-slate-900/30 border border-slate-800/80 rounded-2xl p-8">
                  <span className="text-3xl block mb-2">🏛️</span>
                  <p className="text-slate-300 font-semibold text-sm">No Smart Money reports recorded for {selectedDate}.</p>
                  <p className="text-slate-500 text-xs mt-1">Engine 2 was not tracked on this run date.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {smartMoneyReports.map((rep) => (
                      <div
                        key={rep.id}
                        className="group bg-slate-900/40 border border-slate-800/80 hover:border-slate-700/80 rounded-2xl p-6 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/5 flex flex-col justify-between backdrop-blur-sm"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              Conviction Score: {rep.conviction_score.toFixed(1)}
                            </span>
                            <span className="text-[11px] font-semibold text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded">
                              {rep.conviction_tier}
                            </span>
                          </div>

                          <div className="flex items-start justify-between gap-3 mb-4 min-w-0">
                            <div>
                              <span className="text-2xl font-black tracking-tight text-white group-hover:text-indigo-400 transition-colors">
                                ${rep.ticker}
                              </span>
                              <span className="text-xs font-medium text-slate-400 block mt-0.5">
                                {rep.company_name || rep.ticker} &bull; {rep.sector}
                              </span>
                            </div>
                            <span className="text-xs font-bold text-emerald-400 bg-emerald-950/40 px-2.5 py-1 rounded-lg border border-emerald-800/60">
                              ${(rep.total_buy_volume / 1000).toFixed(0)}k Cluster
                            </span>
                          </div>

                          <div className="space-y-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60 mb-4">
                            <div>
                              <span className="text-[10px] text-slate-500 uppercase font-black block">Buyers</span>
                              <span className="text-xs font-semibold text-slate-200">
                                {rep.top_buyer_summary || "Multiple executive filings"}
                              </span>
                            </div>
                            {rep.catalyst_horizon && (
                              <div>
                                <span className="text-[10px] text-slate-500 uppercase font-black block">Horizon</span>
                                <span className="text-xs font-bold text-amber-300">
                                  ⏳ {rep.catalyst_horizon}
                                </span>
                              </div>
                            )}
                          </div>

                          {rep.actionable_thesis && (
                            <p className="text-xs text-slate-300 line-clamp-3 mb-6 leading-relaxed">
                              &ldquo;{rep.actionable_thesis}&rdquo;
                            </p>
                          )}
                        </div>

                        <div className="pt-4 border-t border-slate-800/60 flex items-center justify-between">
                          <Link
                            href={`/analytics?ticker=${rep.ticker}`}
                            className="text-xs font-semibold text-slate-400 hover:text-indigo-300 transition-colors"
                          >
                            📊 View Trajectory & Analytics &rarr;
                          </Link>
                          <Link
                            href={`/smart-money/${rep.ticker}`}
                            className="inline-flex items-center gap-1 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
                          >
                            View Smart Money Catalyst Report &rarr;
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            )}

            {/* TAB 3: SYNTHESIS MATRIX */}
            {activeTab === "synthesis" && (
              synthesisReports.length === 0 ? (
                <div className="text-center py-20 bg-slate-900/30 border border-slate-800/80 rounded-2xl p-8">
                  <span className="text-3xl block mb-2">⚡</span>
                  <p className="text-slate-300 font-semibold text-sm">No Synthesis Matrix records recorded for {selectedDate}.</p>
                  <p className="text-slate-500 text-xs mt-1">Cross-engine synthesis was not recorded on this run date.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {synthesisReports.map((rec) => (
                      <div
                        key={rec.id}
                        className="group bg-slate-900/40 border border-slate-800/80 hover:border-slate-700/80 rounded-2xl p-6 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/5 flex flex-col justify-between backdrop-blur-sm"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-3">
                            {getArchetypeBadge(rec.archetype)}
                            <span className="text-xs font-bold text-indigo-300 bg-indigo-950/60 border border-indigo-800/60 px-2 py-0.5 rounded">
                              Edge: {rec.timing_edge_score.toFixed(0)}/100
                            </span>
                          </div>

                          <div className="flex items-start justify-between gap-3 mb-4 min-w-0">
                            <div>
                              <span className="text-2xl font-black tracking-tight text-white group-hover:text-indigo-400 transition-colors">
                                ${rec.ticker}
                              </span>
                              <span className="text-xs font-medium text-slate-400 block mt-0.5">
                                Retail: {rec.retail_mentions} mentions &bull; {rec.retail_awareness_level}
                              </span>
                            </div>
                            <span
                              className={`text-xs font-bold px-2 py-1 rounded ${
                                rec.recommended_action === "STRONG BUY" || rec.recommended_action === "EARLY SWING BUY"
                                  ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                                  : rec.recommended_action === "AVOID/SHORT"
                                  ? "bg-rose-950 text-rose-400 border border-rose-800"
                                  : "bg-slate-900 text-slate-400 border border-slate-700"
                              }`}
                            >
                              {rec.recommended_action}
                            </span>
                          </div>

                          <p className="text-xs text-slate-300 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/60 mb-6 leading-relaxed">
                            {rec.synthesis_diagnosis}
                          </p>
                        </div>

                        <div className="pt-4 border-t border-slate-800/60 flex items-center justify-between">
                          <Link
                            href={`/analytics?ticker=${rec.ticker}`}
                            className="text-xs font-semibold text-slate-400 hover:text-indigo-300 transition-colors"
                          >
                            📊 View Trajectory & Analytics &rarr;
                          </Link>
                          <Link
                            href={`/report/${rec.ticker}`}
                            className="inline-flex items-center gap-1 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
                          >
                            View Unified Master Report &rarr;
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            )}
          </>
        )}
      </main>
    </div>
  );
}
