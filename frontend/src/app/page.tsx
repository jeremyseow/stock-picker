"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

interface Ticker {
  id: number;
  ticker: string;
  rank: number;
  mention_count: number;
  engagement_score: number;
  date: string;
  recommendation: "BUY" | "SELL" | "HOLD" | null;
  smart_money_verdict?: string | null;
  current_price: number | null;
  target_price: number | null;
  industry: string;
  sector: string;
}

export default function Home() {
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/api/tickers/today")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch todays tickers");
        return res.json();
      })
      .then((data) => {
        setTickers(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const getRecommendationBadge = (rec: "BUY" | "SELL" | "HOLD" | null) => {
    switch (rec) {
      case "BUY":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
            🟢 BUY
          </span>
        );
      case "SELL":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-500/10 text-rose-500 border border-rose-500/20">
            🔴 SELL
          </span>
        );
      case "HOLD":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-500/10 text-amber-500 border border-amber-500/20">
            🟡 HOLD
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/10">
            ⚪ NO REPORT
          </span>
        );
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

  // Backend stores naive UTC timestamps (no "Z"); mark them as UTC so they convert to local time.
  const runDate = tickers.length > 0 ? new Date(tickers[0].date.endsWith("Z") ? tickers[0].date : `${tickers[0].date}Z`) : null;
  const runAgeDays = runDate ? Math.floor((Date.now() - runDate.getTime()) / 86_400_000) : 0;
  const isStale = runAgeDays >= 1;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background Blur */}
      <div className="absolute top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-indigo-500/10 via-purple-500/5 to-transparent pointer-events-none blur-[120px]" />

      <Navbar />

      {/* Main Body Content */}
      <main className="max-w-6xl mx-auto px-6 py-12 relative">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 mb-4 animate-pulse">
            ✨ AI-Powered Market intelligence
          </span>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight text-white mb-4 leading-tight">
            Trending Reddit Stocks
          </h1>
          <p className="text-slate-400 text-lg">
            Daily extraction and AI reconciliation from r/wallstreetbets. Filtered by live exchange pricing to ensure tradeable securities only.
          </p>
          {runDate && (
            <div
              id="latest-run-date"
              className={`inline-flex items-center gap-2 mt-6 px-4 py-1.5 rounded-full text-sm font-medium border ${
                isStale
                  ? "bg-amber-500/10 text-amber-300 border-amber-500/20"
                  : "bg-emerald-500/10 text-emerald-300 border-emerald-500/20"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${isStale ? "bg-amber-400" : "bg-emerald-400 animate-pulse"}`} />
              Picks from run on{" "}
              <time dateTime={runDate.toISOString()} className="font-bold">
                {runDate.toLocaleString(undefined, { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" })}
              </time>
              {isStale && <span className="text-amber-400/80">({runAgeDays} day{runAgeDays === 1 ? "" : "s"} ago)</span>}
            </div>
          )}
        </div>

        {loading && (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-400 text-sm font-medium animate-pulse">Analyzing today's market buzz...</p>
          </div>
        )}

        {error && (
          <div className="max-w-md mx-auto bg-red-500/10 border border-red-500/20 rounded-2xl p-6 text-center">
            <span className="text-2xl mb-2 block">⚠️</span>
            <h3 className="text-lg font-bold text-red-200">Failed to fetch data</h3>
            <p className="text-red-400/80 text-sm mt-1">{error}</p>
          </div>
        )}

        {!loading && !error && tickers.length === 0 && (
          <div className="max-w-md mx-auto bg-slate-900/50 border border-slate-800 rounded-2xl p-8 text-center">
            <span className="text-3xl mb-3 block">📭</span>
            <h3 className="text-lg font-bold text-slate-300">No stocks picked yet</h3>
            <p className="text-slate-500 text-sm mt-1">Today's pipeline might still be running or hasn't started yet.</p>
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {tickers.map((t) => (
            <Link href={`/report/${t.ticker}`} key={t.id} className="group">
              <div className="h-full bg-slate-900/40 border border-slate-800/80 hover:border-indigo-500/40 rounded-2xl p-6 hover:shadow-2xl hover:shadow-indigo-500/5 transition-all duration-300 backdrop-blur-sm hover:-translate-y-1 flex flex-col justify-between">
                <div>
                  {/* Card Header */}
                  <div className="flex justify-between items-center mb-2.5">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700/50">
                      Rank #{t.rank}
                    </span>
                    {getRecommendationBadge(t.recommendation)}
                  </div>

                  {/* Ticker & Smart Money Verdict Row */}
                  <div className="flex justify-between items-center gap-4 mb-3">
                    <h2 className="text-3xl font-black text-white group-hover:text-indigo-400 transition-colors shrink-0">
                      ${t.ticker}
                    </h2>
                    {getSmartMoneyBadge(t.smart_money_verdict)}
                  </div>

                  {/* Stock Industry / Sector info */}
                  <div className="mb-4 text-xs text-slate-500">
                    <p className="truncate font-medium">{t.sector} &bull; {t.industry}</p>
                  </div>

                  {/* Financial Quick Glance */}
                  {t.current_price !== null && (
                    <div className="bg-slate-950/50 border border-slate-850 rounded-xl p-3 mb-6 flex justify-between items-center text-sm">
                      <div>
                        <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider">Live Price</span>
                        <span className="text-slate-200 font-extrabold text-base">${t.current_price.toFixed(2)}</span>
                      </div>
                      {t.target_price !== null && (
                        <div className="text-right">
                          <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider">Target Price</span>
                          <span className="text-slate-200 font-extrabold text-base">${t.target_price.toFixed(2)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Reddit Engagement details */}
                  <div className="grid grid-cols-2 gap-4 border-t border-slate-800/60 pt-4 text-xs text-slate-400">
                    <div>
                      <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-1">Reddit Mentions</span>
                      <span className="font-extrabold text-slate-200 text-sm">{t.mention_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-1">Engagement Score</span>
                      <span className="font-extrabold text-slate-200 text-sm">{t.engagement_score.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-between text-xs font-bold text-indigo-400 group-hover:text-indigo-300 transition-colors">
                  <span>View Intelligence Report</span>
                  <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
