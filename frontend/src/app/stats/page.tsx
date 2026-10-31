"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

interface ReportItem {
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

export default function HistoricalReportsPage() {
  const [dates, setDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loadingDates, setLoadingDates] = useState(true);
  const [loadingReports, setLoadingReports] = useState(false);
  const [error, setError] = useState("");

  // Fetch available report dates
  useEffect(() => {
    fetch("http://localhost:8000/api/reports/dates")
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

  // Fetch reports when selectedDate changes
  useEffect(() => {
    if (!selectedDate) return;
    setLoadingReports(true);
    fetch(`http://localhost:8000/api/reports?date=${selectedDate}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load reports for ${selectedDate}`);
        return res.json();
      })
      .then((data: ReportItem[]) => {
        setReports(data);
        setLoadingReports(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoadingReports(false);
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

  const getRiskBadge = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case "HIGH":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      case "MEDIUM":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "LOW":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/20";
    }
  };

  const getSmartMoneyBadge = (verdict?: string | null) => {
    if (!verdict) return null;
    const text = verdict.toLowerCase();
    let color = "bg-slate-800 text-slate-300 border-slate-700";
    let icon = "⚖️";
    if (text.includes("no form 4") || text.includes("no data")) {
      color = "bg-slate-800 text-slate-400 border-slate-700";
      icon = "📋";
    } else if (text.includes("bearish") || text.includes("selling") || text.includes("divergence")) {
      color = "bg-rose-500/10 text-rose-400 border-rose-500/20";
      icon = "🔴";
    } else if (text.includes("bullish") || text.includes("accumulation") || text.includes("buying")) {
      color = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      icon = "🟢";
    }
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold border text-right leading-tight max-w-[65%] shrink-0 ${color}`}>
        <span className="shrink-0">{icon}</span>
        <span className="truncate">{verdict}</span>
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background Glow */}
      <div className="absolute top-0 left-0 right-0 h-[450px] bg-gradient-to-b from-indigo-500/10 via-purple-500/5 to-transparent pointer-events-none blur-[120px]" />

      <Navbar />

      <main className="max-w-6xl mx-auto px-6 py-12 relative">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 pb-6 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Historical Archive
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight text-white mb-2">
              Historical Intelligence Reports
            </h1>
            <p className="text-slate-400 text-sm max-w-xl">
              Browse market research reports, retail sentiment snapshots, and AI recommendations by pipeline execution date.
            </p>
          </div>

          {/* Date Selector Dropdown */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <label htmlFor="date-select" className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Select Run Date:
            </label>
            <select
              id="date-select"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              disabled={loadingDates || dates.length === 0}
              className="bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm font-semibold text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 transition-all cursor-pointer shadow-lg"
            >
              {dates.map((d) => (
                <option key={d} value={d} className="bg-slate-900 text-white">
                  📅 {d} {d === dates[0] ? "(Latest)" : ""}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="mb-8 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            {error}
          </div>
        )}

        {/* Content States */}
        {loadingDates ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 text-sm">Loading archive calendar...</p>
          </div>
        ) : dates.length === 0 ? (
          <div className="text-center py-24 bg-slate-900/30 border border-slate-800/80 rounded-2xl p-12">
            <span className="text-4xl mb-4 block">📭</span>
            <h3 className="text-xl font-bold text-white mb-2">No Historical Reports Yet</h3>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              Once the daily pipeline executes, past reports will be archived and accessible here by calendar date.
            </p>
          </div>
        ) : loadingReports ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 text-sm">Fetching reports for {selectedDate}...</p>
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-20 bg-slate-900/30 border border-slate-800/80 rounded-2xl p-8">
            <p className="text-slate-400 text-sm">No reports recorded for {selectedDate}.</p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 px-1">
              <span>Showing {reports.length} report{reports.length > 1 ? "s" : ""} analyzed on {selectedDate}</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {reports.map((rep) => {
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
                      {/* Top Bar: Risk Level & Recommendation */}
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

                      {/* Main Bar: Ticker & Smart Money Verdict */}
                      <div className="flex items-start justify-between gap-4 mb-4">
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

                      {/* Pricing Snapshot */}
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

                      {/* Sentiment & Insight */}
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

                    {/* Action Links */}
                    <div className="pt-4 border-t border-slate-800/60 flex items-center justify-between">
                      <Link
                        href={`/analytics?ticker=${rep.ticker}`}
                        className="text-xs font-semibold text-slate-400 hover:text-indigo-300 transition-colors"
                      >
                        📊 View Trajectory &rarr;
                      </Link>
                      <Link
                        href={`/report/${rep.ticker}`}
                        className="inline-flex items-center gap-1 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
                      >
                        Full Intel Report &rarr;
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
