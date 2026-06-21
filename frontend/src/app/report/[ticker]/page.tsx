"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";

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
  recommendation_key?: string;
}

interface RawNewsItem {
  title?: string | null;
  publisher?: string | null;
  link?: string | null;
  provider_publish_time?: number | null;
}

interface Report {
  id: number;
  ticker: string;
  date: string;
  current_price: number | null;
  target_price: number | null;
  community_sentiment: string;
  community_hype: string;
  ground_truth_status: string;
  ground_truth_filings_news: string;
  events_happenings: string;
  reconciliation_risk_score: string;
  reconciliation_analysis: string;
  reconciliation_actionable_insight: string;
  recommendation: "BUY" | "SELL" | "HOLD";
  recommendation_rationale: string;
  raw_metrics: RawMetrics | null;
  raw_news: RawNewsItem[] | null;
}

export default function ReportPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = use(params);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`http://localhost:8000/api/reports/${ticker}`)
      .then((res) => {
        if (!res.ok) throw new Error("Report not found in database");
        return res.json();
      })
      .then((data) => {
        // Parse JSON strings if returned as string from database (usually handled by FastAPI, but let's be robust)
        const parsedReport = { ...data };
        if (typeof data.raw_metrics === "string") {
          try {
            parsedReport.raw_metrics = JSON.parse(data.raw_metrics);
          } catch (e) {
            console.error("Failed to parse raw_metrics string", e);
          }
        }
        if (typeof data.raw_news === "string") {
          try {
            parsedReport.raw_news = JSON.parse(data.raw_news);
          } catch (e) {
            console.error("Failed to parse raw_news string", e);
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

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm font-medium animate-pulse">Assembling market intelligence report for {ticker}...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 text-center">
        <span className="text-3xl mb-4">⚠️</span>
        <h3 className="text-xl font-bold text-red-400">Report Not Found</h3>
        <p className="text-slate-500 text-sm mt-2 max-w-sm">
          No reports for ${ticker} were found in the database. Ensure the scraping pipeline has processed this stock.
        </p>
        <Link href="/" className="mt-6 px-6 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition-colors">
          &larr; Back to Dashboard
        </Link>
      </div>
    );
  }

  const recColorStyles = {
    BUY: "from-emerald-500 to-teal-600 shadow-emerald-500/20 text-white border-emerald-500/30",
    SELL: "from-rose-500 to-red-600 shadow-rose-500/20 text-white border-rose-500/30",
    HOLD: "from-amber-400 to-orange-500 shadow-amber-500/20 text-white border-amber-500/30",
  };

  const riskBadgeStyles = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case "HIGH":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      case "MEDIUM":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "LOW":
        return "bg-green-500/10 text-green-400 border-green-500/20";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/20";
    }
  };

  // Calculate potential upside
  let upsidePercent: number | null = null;
  if (report.current_price && report.target_price) {
    upsidePercent = ((report.target_price - report.current_price) / report.current_price) * 100;
  }

  const formatMarketCap = (num?: number | null) => {
    if (!num) return "N/A";
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background gradients */}
      <div className="absolute top-0 left-0 right-0 h-[400px] bg-gradient-to-b from-indigo-500/5 via-purple-500/3 to-transparent pointer-events-none blur-[100px]" />

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-800/80">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              📈
            </span>
            <span className="font-extrabold text-xl bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 via-slate-100 to-indigo-200">
              Antigravity <span className="text-indigo-400">StockPicker</span>
            </span>
          </Link>
          <nav className="flex items-center gap-6">
            <Link href="/" className="text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors">
              Dashboard
            </Link>
            <Link href="/stats" className="text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors">
              Historical Trends
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 relative">
        {/* Back Link */}
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 font-medium mb-8 group transition-colors">
          <span className="group-hover:-translate-x-1 transition-transform">&larr;</span> Back to Dashboard
        </Link>

        {/* Hero Section */}
        <div className="flex flex-col lg:flex-row gap-6 mb-8 items-stretch">
          {/* Left Block - Stock Identity */}
          <div className="flex-1 bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-sm">
            <div>
              <span className="text-indigo-400 font-extrabold text-xs uppercase tracking-wider block mb-1">
                {report.raw_metrics?.sector || "Technology"} &bull; {report.raw_metrics?.industry || "Semiconductors"}
              </span>
              <h1 className="text-5xl md:text-6xl font-black text-white leading-none tracking-tight">
                ${report.ticker}
              </h1>
              <p className="text-slate-400 text-sm mt-3">
                Intelligence generated on {new Date(report.date).toLocaleDateString()} at {new Date(report.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            <div className="mt-6 pt-6 border-t border-slate-800/50 flex gap-6 text-sm">
              <div>
                <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-0.5">Analyst Rec</span>
                <span className="font-extrabold text-slate-300 capitalize">{report.raw_metrics?.recommendation_key?.replace("_", " ") || "hold"}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-0.5">Market Cap</span>
                <span className="font-extrabold text-slate-300">{formatMarketCap(report.raw_metrics?.market_cap)}</span>
              </div>
            </div>
          </div>

          {/* Right Block - Price & recommendation */}
          <div className="lg:w-[450px] bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-sm">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">AI Recommendation</span>
              <div className={`px-4 py-1.5 rounded-lg border bg-gradient-to-br font-extrabold text-sm tracking-wide shadow-md ${recColorStyles[report.recommendation]}`}>
                {report.recommendation}
              </div>
            </div>

            {/* Price Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950/60 border border-slate-900 rounded-xl p-4">
                <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-1">Current Price</span>
                <span className="text-white text-3xl font-black">${report.current_price?.toFixed(2) || "N/A"}</span>
              </div>
              <div className="bg-slate-950/60 border border-slate-900 rounded-xl p-4">
                <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-1">Target Price</span>
                <span className="text-white text-3xl font-black">${report.target_price?.toFixed(2) || "N/A"}</span>
              </div>
            </div>

            {/* Potential Upside Calculator */}
            {upsidePercent !== null && (
              <div className="mt-4 pt-3 border-t border-slate-800/50 flex justify-between items-center text-xs">
                <span className="text-slate-500 font-bold uppercase tracking-wider">Calculated Potential Upside</span>
                <span className={`px-2.5 py-1 rounded font-extrabold ${upsidePercent >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
                  {upsidePercent >= 0 ? `+${upsidePercent.toFixed(1)}%` : `${upsidePercent.toFixed(1)}%`}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Highlights panel: Rationale & Callout */}
        <div className="bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-slate-900/30 border border-indigo-500/20 rounded-2xl p-6 md:p-8 mb-8 backdrop-blur-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-[200px] h-[200px] bg-indigo-500/5 blur-[50px] pointer-events-none" />
          <div className="flex flex-col md:flex-row gap-6 items-start relative">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/20 text-indigo-300 flex items-center justify-center shrink-0 font-bold text-2xl shadow-inner shadow-indigo-500/20">
              💡
            </div>
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-black text-white">AI Analyst Rationale</h3>
                <p className="text-slate-300 text-sm leading-relaxed mt-1 italic">
                  "{report.recommendation_rationale}"
                </p>
              </div>
              <div className="pt-4 border-t border-slate-800/80">
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400">Immediate Actionable Insight</h4>
                <p className="text-slate-300 text-sm leading-relaxed mt-1 font-semibold text-slate-100">
                  {report.reconciliation_actionable_insight}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Four Pillar Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
          {/* 1. Community Sentiment */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-sm">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="w-6 h-6 rounded bg-orange-500/10 text-orange-400 flex items-center justify-center text-xs font-bold">💬</span>
                <h3 className="font-extrabold text-slate-200">Community Sentiment</h3>
              </div>
              <div className="bg-slate-950/40 border border-slate-900 rounded-xl p-3 mb-4">
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-0.5">Reddit Sentiment Score</span>
                <span className="font-extrabold text-slate-200 text-sm">{report.community_sentiment}</span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed">
                {report.community_hype}
              </p>
            </div>
          </div>

          {/* 2. Ground Truth */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-sm">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="w-6 h-6 rounded bg-purple-500/10 text-purple-400 flex items-center justify-center text-xs font-bold">🏢</span>
                <h3 className="font-extrabold text-slate-200">Ground Truth</h3>
              </div>
              
              <div className="space-y-4">
                <div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase block mb-1">Corporate Position</span>
                  <p className="text-slate-300 text-xs leading-relaxed">
                    {report.ground_truth_status}
                  </p>
                </div>
                
                <div className="pt-3 border-t border-slate-800/65">
                  <span className="text-[10px] text-slate-500 font-bold uppercase block mb-1">Filings & News Analysis</span>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    {report.ground_truth_filings_news}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 3. Events & Happenings */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-sm">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="w-6 h-6 rounded bg-rose-500/10 text-rose-400 flex items-center justify-center text-xs font-bold">💥</span>
                <h3 className="font-extrabold text-slate-200">Events & Happenings</h3>
              </div>
              <div className="bg-slate-950/40 border border-slate-900 rounded-xl p-3 mb-4">
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-0.5">Macro & Corporate Events</span>
                <span className="font-extrabold text-indigo-400 text-xs">Catalysts & News</span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed">
                {report.events_happenings}
              </p>
            </div>
          </div>

          {/* 3. AI Reconciliation */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-sm">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="w-6 h-6 rounded bg-teal-500/10 text-teal-400 flex items-center justify-center text-xs font-bold">⚖️</span>
                <h3 className="font-extrabold text-slate-200">AI Reconciliation</h3>
              </div>
              <div className="flex items-center justify-between bg-slate-950/40 border border-slate-900 rounded-xl p-3 mb-4">
                <div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase block mb-0.5">Risk Score</span>
                  <span className="font-extrabold text-slate-200 text-sm">Level</span>
                </div>
                <span className={`px-2.5 py-1 text-xs font-bold rounded border ${riskBadgeStyles(report.reconciliation_risk_score)}`}>
                  {report.reconciliation_risk_score}
                </span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed">
                {report.reconciliation_analysis}
              </p>
            </div>
          </div>
        </div>

        {/* Lower Info Grid: Metrics and News Links */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Key Financial Metrics */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
            <h3 className="font-extrabold text-slate-200 text-lg mb-6 flex items-center gap-2">
              <span>📊</span> Key Financial Ratios
            </h3>
            <div className="space-y-4 text-xs">
              <div className="flex justify-between items-center py-2.5 border-b border-slate-800/60">
                <span className="text-slate-500">Trailing P/E Ratio</span>
                <span className="font-extrabold text-slate-300">{report.raw_metrics?.pe_ratio?.toFixed(2) || "N/A"}</span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-slate-800/60">
                <span className="text-slate-500">Forward P/E Ratio</span>
                <span className="font-extrabold text-slate-300">{report.raw_metrics?.forward_pe?.toFixed(2) || "N/A"}</span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-slate-800/60">
                <span className="text-slate-500">52-Week High</span>
                <span className="font-extrabold text-emerald-400">${report.raw_metrics?.fifty_two_week_high?.toFixed(2) || "N/A"}</span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-slate-800/60">
                <span className="text-slate-500">52-Week Low</span>
                <span className="font-extrabold text-rose-400">${report.raw_metrics?.fifty_two_week_low?.toFixed(2) || "N/A"}</span>
              </div>
            </div>
          </div>

          {/* Recent News headlines */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
            <h3 className="font-extrabold text-slate-200 text-lg mb-6 flex items-center gap-2">
              <span>📰</span> Recent Corporate News
            </h3>
            {report.raw_news && report.raw_news.length > 0 && report.raw_news.some(item => item.title) ? (
              <div className="space-y-4">
                {report.raw_news.map((item, idx) => {
                  if (!item.title) return null;
                  return (
                    <div key={idx} className="pb-3 border-b border-slate-800/40 last:border-0 last:pb-0">
                      {item.link ? (
                        <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-slate-300 hover:text-indigo-400 text-xs font-semibold leading-relaxed block hover:underline transition-colors">
                          {item.title}
                        </a>
                      ) : (
                        <span className="text-slate-300 text-xs font-semibold leading-relaxed block">
                          {item.title}
                        </span>
                      )}
                      <span className="text-[10px] text-slate-500 block mt-1 font-medium">
                        Publisher: {item.publisher || "Unknown"}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500 py-4 italic text-center">No standard news headlines available for this stock.</p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
