"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { API_BASE } from "@/lib/api";

interface RawMetrics {
  current_price?: number | null;
  target_price?: number | null;
  market_cap?: number | null;
  pe_ratio?: number | null;
  forward_pe?: number | null;
  fifty_two_week_high?: number | null;
  fifty_two_week_low?: number | null;
  industry?: string;
  sector?: string;
}

interface RawNewsItem {
  title?: string | null;
  publisher?: string | null;
  link?: string | null;
  provider_publish_time?: number | null;
}

interface RetailReportDetail {
  id: number;
  ticker: string;
  date: string;
  rank?: number | null;
  current_price: number | null;
  target_price: number | null;
  recommendation: "BUY" | "SELL" | "HOLD";
  recommendation_rationale: string;
  community_sentiment: string;
  community_hype: string;
  ground_truth_status: string;
  ground_truth_filings_news: string;
  events_happenings: string;
  reconciliation_risk_score: string;
  reconciliation_analysis: string;
  reconciliation_actionable_insight: string;
  raw_metrics: RawMetrics | null;
  raw_news: RawNewsItem[] | null;
  core_intel?: {
    has_data: boolean;
    company_name: string;
    sector: string;
    industry: string;
    raw_metrics?: Record<string, any>;
  };
}

export default function RetailDetailPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = use(params);
  const [report, setReport] = useState<RetailReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/api/retail/report/${ticker}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Retail Momentum report for $${ticker.toUpperCase()} not found`);
        return res.json();
      })
      .then((data) => {
        const parsedReport = { ...data };
        if (typeof data.raw_metrics === "string") {
          try {
            parsedReport.raw_metrics = JSON.parse(data.raw_metrics);
          } catch {
            parsedReport.raw_metrics = null;
          }
        }
        setReport(parsedReport);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [ticker]);

  const recColorStyles: Record<string, string> = {
    BUY: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    HOLD: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    SELL: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  };

  const riskBadgeStyles = (score?: string) => {
    switch (score) {
      case "Low":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "High":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      default:
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm font-medium animate-pulse">
            Loading Retail Momentum Intelligence for ${ticker.toUpperCase()}...
          </p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center gap-6 p-6">
          <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-8 max-w-md text-center">
            <span className="text-4xl mb-3 block">⚠️</span>
            <h2 className="text-xl font-bold text-red-200">Report Unavailable</h2>
            <p className="text-red-400/80 text-sm mt-2">{error || "No retail report found."}</p>
            <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/"
                className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white transition-colors"
              >
                &larr; Retail Feed
              </Link>
              <Link
                href={`/smart-money/${ticker}`}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
              >
                Check Smart Money Scout &rarr;
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const upside =
    report.current_price && report.target_price && report.current_price > 0
      ? (((report.target_price - report.current_price) / report.current_price) * 100).toFixed(1)
      : null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      <div className="absolute top-0 left-0 right-0 h-[400px] bg-gradient-to-b from-indigo-500/5 via-purple-500/3 to-transparent pointer-events-none blur-[100px]" />

      <Navbar />

      <main className="max-w-6xl mx-auto px-6 py-8 relative">
        {/* Navigation Breadcrumbs & Cross-Engine Links */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 font-medium group transition-colors"
          >
            <span className="group-hover:-translate-x-1 transition-transform">&larr;</span> Back to Retail Momentum Feed
          </Link>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              href={`/smart-money/${report.ticker}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-900/80 hover:bg-slate-800 text-purple-300 hover:text-white border border-purple-500/30 transition-all"
            >
              <span>🏛️</span> View Smart Money Catalyst Report &rarr;
            </Link>
            <Link
              href={`/report/${report.ticker}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 hover:text-white border border-indigo-500/40 transition-all"
            >
              <span>⚡</span> View Unified Master Report &rarr;
            </Link>
            <Link
              href={`/analytics?ticker=${report.ticker}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition-all"
            >
              <span>📊</span> Trajectory & Analytics &rarr;
            </Link>
          </div>
        </div>

        {/* Hero Header */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 sm:p-8 backdrop-blur-sm mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-800/60">
            <div>
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <h1 className="text-4xl font-black text-white">${report.ticker}</h1>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${recColorStyles[report.recommendation]}`}>
                  {report.recommendation === "BUY" ? "🟢" : report.recommendation === "SELL" ? "🔴" : "🟡"} {report.recommendation}
                </span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  💬 {report.community_sentiment}
                </span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Rank #{report.rank || 1}
                </span>
              </div>
              <p className="text-slate-400 text-sm font-medium">
                {report.core_intel?.company_name || report.ticker} &bull; {report.core_intel?.sector || report.raw_metrics?.sector || "Technology"} &bull; {report.core_intel?.industry || report.raw_metrics?.industry || "General"}
              </p>
            </div>

            <div className="flex items-center gap-6 shrink-0">
              {report.current_price !== null && (
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Live Price</span>
                  <span className="text-2xl font-black text-white">${report.current_price.toFixed(2)}</span>
                </div>
              )}
              {report.target_price !== null && (
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Target Price</span>
                  <span className="text-2xl font-black text-indigo-400">${report.target_price.toFixed(2)}</span>
                </div>
              )}
              {upside !== null && (
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Projected Upside</span>
                  <span className={`text-2xl font-black ${parseFloat(upside) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {parseFloat(upside) >= 0 ? `+${upside}%` : `${upside}%`}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* AI Evaluator Rationale - Full Width */}
          <div className="mt-6 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <span className="text-[10px] text-slate-500 uppercase font-black tracking-wider block mb-1">
              ⚡ AI Recommendation Rationale
            </span>
            <p className="text-xs font-medium text-slate-200 leading-relaxed italic">
              &ldquo;{report.recommendation_rationale}&rdquo;
            </p>
          </div>

          {/* Ground Truth Moat Description Box - Full Width */}
          {report.ground_truth_status && (
            <div className="mt-4 p-4 rounded-xl bg-slate-950/60 border border-indigo-500/20 text-xs text-slate-300 leading-relaxed">
              <div className="flex items-center gap-1.5 text-indigo-400 font-bold uppercase tracking-wider text-[10px] mb-1.5">
                <span>🏢</span> Fundamental Ground Truth & Competitive Moat
              </div>
              <p>{report.ground_truth_status}</p>
            </div>
          )}
        </div>

        {/* Community Narrative & Hype Analysis */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 mb-8 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-6 h-6 rounded bg-amber-500/10 text-amber-400 flex items-center justify-center text-xs font-bold">
              💬
            </span>
            <h3 className="font-extrabold text-slate-200">Reddit Community Sentiment & Hype Narrative</h3>
          </div>
          <p className="text-slate-300 text-xs leading-relaxed">
            {report.community_hype}
          </p>
        </div>

        {/* Actionable Watchpoint Callout */}
        <div className="bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-slate-900/30 border border-indigo-500/20 rounded-2xl p-6 md:p-8 mb-8 backdrop-blur-sm">
          <div className="flex gap-4 items-start">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-300 flex items-center justify-center shrink-0 font-bold text-xl">
              💡
            </div>
            <div>
              <h3 className="text-base font-black text-white mb-1">Actionable Intelligence Watchpoint</h3>
              <p className="text-slate-200 text-sm leading-relaxed font-semibold italic">
                &ldquo;{report.reconciliation_actionable_insight}&rdquo;
              </p>
            </div>
          </div>
        </div>

        {/* Ground Truth & Reconciliation Grid */}
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          {/* Filings */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-sm">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-6 h-6 rounded bg-blue-500/10 text-blue-400 flex items-center justify-center text-xs font-bold">
                  📄
                </span>
                <h3 className="font-extrabold text-slate-200 text-sm">SEC 10-Q & 8-K Highlights</h3>
              </div>
              <p className="text-slate-300 text-xs leading-relaxed">{report.ground_truth_filings_news}</p>
            </div>
          </div>

          {/* Events */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-sm">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-6 h-6 rounded bg-rose-500/10 text-rose-400 flex items-center justify-center text-xs font-bold">
                  💥
                </span>
                <h3 className="font-extrabold text-slate-200 text-sm">Key Corporate Events</h3>
              </div>
              <p className="text-slate-300 text-xs leading-relaxed">{report.events_happenings}</p>
            </div>
          </div>

          {/* Risk */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-sm">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded bg-teal-500/10 text-teal-400 flex items-center justify-center text-xs font-bold">
                    ⚖️
                  </span>
                  <h3 className="font-extrabold text-slate-200 text-sm">Risk Assessment</h3>
                </div>
                <span className={`px-2 py-0.5 text-xs font-bold rounded border ${riskBadgeStyles(report.reconciliation_risk_score)}`}>
                  {report.reconciliation_risk_score}
                </span>
              </div>
              <p className="text-slate-300 text-xs leading-relaxed">{report.reconciliation_analysis}</p>
            </div>
          </div>
        </div>

        {/* Valuation Ratios & News */}
        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
            <h3 className="font-extrabold text-slate-200 text-base mb-4 flex items-center gap-2">
              <span>📊</span> Valuation Metrics & Trading Range
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center py-2 border-b border-slate-800/60">
                <span className="text-slate-500">Trailing P/E Ratio</span>
                <span className="font-bold text-slate-200">
                  {report.raw_metrics?.pe_ratio ? `${report.raw_metrics.pe_ratio.toFixed(1)}x` : "N/A"}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800/60">
                <span className="text-slate-500">Forward P/E Ratio</span>
                <span className="font-bold text-slate-200">
                  {report.raw_metrics?.forward_pe ? `${report.raw_metrics.forward_pe.toFixed(1)}x` : "N/A"}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800/60">
                <span className="text-slate-500">52-Week Range</span>
                <span className="font-bold text-slate-200">
                  {report.raw_metrics?.fifty_two_week_low && report.raw_metrics?.fifty_two_week_high
                    ? `$${report.raw_metrics.fifty_two_week_low.toFixed(0)} - $${report.raw_metrics.fifty_two_week_high.toFixed(0)}`
                    : "N/A"}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
            <h3 className="font-extrabold text-slate-200 text-base mb-4 flex items-center gap-2">
              <span>📰</span> Corporate News Headlines
            </h3>
            {report.raw_news && report.raw_news.length > 0 && report.raw_news.some((n) => n.title) ? (
              <div className="space-y-3">
                {report.raw_news.slice(0, 3).map((item, idx) => (
                  <div key={idx} className="pb-2 border-b border-slate-800/40 last:border-0">
                    <a
                      href={item.link || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-300 hover:text-indigo-400 text-xs font-semibold block transition-colors"
                    >
                      {item.title}
                    </a>
                    <span className="text-[10px] text-slate-500">{item.publisher || "Corporate Press"}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic py-4 text-center">No recent news headlines available.</p>
            )}
          </div>
        </div>

        {/* Bottom Navigation */}
        <div className="pt-6 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
          <Link href="/" className="text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors">
            &larr; Back to Retail Momentum Feed
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href={`/report/${report.ticker}`}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 transition-all"
            >
              <span>⚡</span> Inspect Unified Master Report &rarr;
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}

