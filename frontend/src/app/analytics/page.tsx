"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import PriceTrajectoryChart, { HistoryPoint } from "@/components/PriceTrajectoryChart";
import MetaAnalysisCard from "@/components/MetaAnalysisCard";
import SentimentTrajectoryTimeline from "@/components/SentimentTrajectoryTimeline";
import ValuationMetricsPanel from "@/components/ValuationMetricsPanel";
import ActionableInsightsLog from "@/components/ActionableInsightsLog";

function AnalyticsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialTicker = searchParams.get("ticker")?.toUpperCase() || "";

  const [tickers, setTickers] = useState<string[]>([]);
  const [selectedTicker, setSelectedTicker] = useState<string>(initialTicker);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [loadingTickers, setLoadingTickers] = useState<boolean>(true);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  // 1. Fetch available tickers
  useEffect(() => {
    fetch("http://localhost:8000/api/analytics/tickers")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch tracked tickers");
        return res.json();
      })
      .then((data: string[]) => {
        setTickers(data);
        if (data.length > 0) {
          if (initialTicker && data.includes(initialTicker)) {
            setSelectedTicker(initialTicker);
          } else {
            setSelectedTicker(data[0]);
          }
        }
        setLoadingTickers(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoadingTickers(false);
      });
  }, [initialTicker]);

  // 2. Fetch history for selected ticker
  useEffect(() => {
    if (!selectedTicker) return;
    setLoadingHistory(true);
    setError("");

    fetch(`http://localhost:8000/api/analytics/ticker/${selectedTicker}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load historical trajectory for ${selectedTicker}`);
        return res.json();
      })
      .then((data: HistoryPoint[]) => {
        setHistory(data);
        setLoadingHistory(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoadingHistory(false);
      });
  }, [selectedTicker]);

  const handleSelectTicker = (ticker: string) => {
    setSelectedTicker(ticker);
    router.push(`/analytics?ticker=${ticker}`);
  };

  const latestReport = history.length > 0 ? history[history.length - 1] : null;

  const getRecommendationBadge = (rec: "BUY" | "SELL" | "HOLD" | null) => {
    switch (rec) {
      case "BUY":
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            🟢 BUY
          </span>
        );
      case "SELL":
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            🔴 SELL
          </span>
        );
      case "HOLD":
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            🟡 HOLD
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold bg-slate-500/10 text-slate-400 border border-slate-500/20">
            ⚪ NO REPORT
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background Accent */}
      <div className="absolute top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-indigo-500/10 via-purple-500/5 to-transparent pointer-events-none blur-[120px]" />

      <Navbar />

      <main className="max-w-6xl mx-auto px-6 py-12 relative">
        {/* Header Bar */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8 pb-6 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Multi-Run Longitudinal Analysis
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight text-white mb-2">
              Ticker Analytical Report
            </h1>
            <p className="text-slate-400 text-sm max-w-xl">
              Track multi-run price trajectory vs. Wall Street target price, community sentiment evolution, and AI meta-analysis over time.
            </p>
          </div>

          {/* Ticker Selector */}
          <div className="flex items-center gap-3">
            <label htmlFor="ticker-select" className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Select Ticker:
            </label>
            <select
              id="ticker-select"
              value={selectedTicker}
              onChange={(e) => handleSelectTicker(e.target.value)}
              disabled={loadingTickers || tickers.length === 0}
              className="bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm font-black text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 cursor-pointer shadow-lg tracking-wide"
            >
              {tickers.map((t) => (
                <option key={t} value={t} className="bg-slate-900 text-white font-bold">
                  ${t}
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

        {loadingTickers ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 text-sm">Loading tracked tickers catalog...</p>
          </div>
        ) : tickers.length === 0 ? (
          <div className="text-center py-24 bg-slate-900/30 border border-slate-800/80 rounded-2xl p-12">
            <span className="text-4xl mb-4 block">📉</span>
            <h3 className="text-xl font-bold text-white mb-2">No Tracked Tickers Found</h3>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              No stock reports have been generated yet. Run the analysis pipeline to populate tickers and reports.
            </p>
          </div>
        ) : loadingHistory ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 text-sm">Assembling analytical trajectory for ${selectedTicker}...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-20 bg-slate-900/30 border border-slate-800/80 rounded-2xl p-8">
            <p className="text-slate-400 text-sm">No historical data found for ${selectedTicker}.</p>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Active Ticker Hero Banner */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xl text-white shadow-lg shadow-indigo-500/20 shrink-0">
                  📊
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-black text-white">${selectedTicker}</h2>
                    {latestReport && getRecommendationBadge(latestReport.recommendation)}
                  </div>
                  <span className="text-xs font-medium text-slate-400">
                    {latestReport?.raw_metrics?.sector || "Technology"} &bull;{" "}
                    {latestReport?.raw_metrics?.industry || "Equities"}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <span className="text-xs font-semibold text-slate-400">
                  {history.length} Run{history.length > 1 ? "s" : ""} Recorded
                </span>
                <Link
                  href={`/report/${selectedTicker}`}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition-all"
                >
                  View Latest Full Report &rarr;
                </Link>
              </div>
            </div>

            {/* 1. Price vs. Target Price Trajectory Chart */}
            <PriceTrajectoryChart data={history} ticker={selectedTicker} />

            {/* 2. AI Trajectory Meta-Analysis Card */}
            <MetaAnalysisCard ticker={selectedTicker} reportCount={history.length} />

            {/* 3. Sentiment & Recommendation Timeline */}
            <SentimentTrajectoryTimeline data={history} />

            {/* 4. Valuation Multiples & Trading Range */}
            <ValuationMetricsPanel data={history} />

            {/* 5. Chronological Actionable Insights Log */}
            <ActionableInsightsLog data={history} />
          </div>
        )}
      </main>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-950 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <AnalyticsContent />
    </Suspense>
  );
}

