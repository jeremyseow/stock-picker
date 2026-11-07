"use client";

import { useEffect, useState, use, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import SmartMoneyRadar, { RawInsiderData } from "@/components/SmartMoneyRadar";
import ContrarianPlaybook from "@/components/ContrarianPlaybook";
import OptionsFlowCard from "@/components/OptionsFlowCard";
import { FilingHighlights } from "@/components/FilingHighlights";
import { RetailTrapIcon } from "@/components/RetailTrapIcon";
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
  recommendation_key?: string;
}

interface RawNewsItem {
  title?: string | null;
  publisher?: string | null;
  link?: string | null;
  provider_publish_time?: number | null;
}

interface InflowTransaction {
  date?: string;
  buyer?: string;
  role?: string;
  type?: string;
  shares?: number;
  price?: string;
  value?: string;
  committee?: string;
  delta_own?: string;
}

interface RetailOverlay {
  has_data: boolean;
  rank?: number | null;
  mention_count?: number;
  community_sentiment?: string;
  community_hype?: string;
  recommendation?: "BUY" | "SELL" | "HOLD" | null;
  recommendation_rationale?: string | null;
}

interface SmartMoneyOverlay {
  has_data: boolean;
  rank?: number | null;
  conviction_score?: number;
  conviction_tier?: string;
  cluster_count?: number;
  total_buy_volume?: number;
  top_buyer_summary?: string | null;
  inflow_ledger?: InflowTransaction[];
  political_catalyst_analysis?: string | null;
  corporate_catalyst_analysis?: string | null;
  catalyst_horizon?: string | null;
  actionable_thesis?: string | null;
}

interface SynthesisFacet {
  has_data: boolean;
  archetype?: string;
  retail_awareness_level?: string;
  timing_edge_score?: number;
  synthesis_diagnosis?: string | null;
  recommended_action?: string;
}

interface MasterReport {
  id: number;
  ticker: string;
  company_name?: string;
  sector?: string;
  industry?: string;
  date: string;
  current_price: number | null;
  target_price: number | null;
  potential_upside?: number | null;

  ground_truth_status: string;
  ground_truth_filings_news: string;
  events_happenings: string;
  reconciliation_risk_score: string;
  reconciliation_analysis: string;
  reconciliation_actionable_insight: string;

  recommendation: "BUY" | "SELL" | "HOLD";
  recommendation_rationale: string;
  community_sentiment: string;
  community_hype: string;
  smart_money_verdict?: string | null;
  raw_insider_data?: RawInsiderData | null;
  raw_metrics: RawMetrics | null;
  raw_news: RawNewsItem[] | null;

  retail_overlay?: RetailOverlay;
  smart_money_overlay?: SmartMoneyOverlay;
  synthesis?: SynthesisFacet;
}

function ReportPageContent({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = use(params);
  const searchParams = useSearchParams();
  const reportDate = searchParams.get("date");
  const [report, setReport] = useState<MasterReport | null>(null);
  const [optionsData, setOptionsData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    const masterUrl = reportDate
      ? `${API_BASE}/api/master/report/${ticker}?date=${reportDate}`
      : `${API_BASE}/api/master/report/${ticker}`;
    const optionsUrl = reportDate
      ? `${API_BASE}/api/options/report/${ticker}?date=${reportDate}`
      : `${API_BASE}/api/options/report/${ticker}`;

    fetch(masterUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`Report not found in database${reportDate ? ` for ${reportDate}` : ""}`);
        return res.json();
      })
      .then((data) => {
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
        if (typeof data.raw_insider_data === "string") {
          try {
            parsedReport.raw_insider_data = JSON.parse(data.raw_insider_data);
          } catch (e) {
            console.error("Failed to parse raw_insider_data string", e);
          }
        }
        setReport(parsedReport);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    fetch(optionsUrl)
      .then((res) => (res.ok ? res.json() : null))
      .then((opt) => setOptionsData(opt))
      .catch(() => {});
  }, [ticker, reportDate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm font-medium animate-pulse">
          Assembling unified master intelligence report for ${ticker}...
        </p>
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
        <Link
          href="/"
          className="mt-6 px-6 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition-colors"
        >
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

  const getArchetypeBadge = (archetype?: string) => {
    switch (archetype) {
      case "The Rocket":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-purple-500/20 text-purple-300 border border-purple-500/40">
            🚀 The Rocket (Full Alignment)
          </span>
        );
      case "The Retail Trap":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-rose-500/20 text-rose-300 border border-rose-500/40">
            <RetailTrapIcon className="w-4 h-4 text-rose-400 shrink-0" /> The Retail Trap (Bearish Divergence)
          </span>
        );
      case "Silent Accumulation":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            🤫 Silent Accumulation (Stealth Entry)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-slate-500/20 text-slate-300 border border-slate-500/40">
            📢 Market Noise
          </span>
        );
    }
  };

  const formatMarketCap = (num?: number | null) => {
    if (!num) return "N/A";
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
  };

  const smOverlay = report.smart_money_overlay;
  const retailOverlay = report.retail_overlay;
  const synthesis = report.synthesis;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      <div className="absolute top-0 left-0 right-0 h-[400px] bg-gradient-to-b from-indigo-500/5 via-purple-500/3 to-transparent pointer-events-none blur-[100px]" />

      <Navbar />

      <main className="max-w-6xl mx-auto px-6 py-8 relative">
        {/* Navigation Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
          {reportDate ? (
            <Link
              href="/stats"
              className="inline-flex items-center gap-2 text-sm text-amber-400 hover:text-amber-300 font-semibold group transition-colors"
            >
              <span className="group-hover:-translate-x-1 transition-transform">&larr;</span> Historical Archive ({reportDate}) &bull; Back to Historical Reports
            </Link>
          ) : (
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 font-medium group transition-colors"
            >
              <span className="group-hover:-translate-x-1 transition-transform">&larr;</span> Back to Dashboard
            </Link>
          )}
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href={`/retail/${report.ticker}${reportDate ? `?date=${reportDate}` : ""}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-900/80 hover:bg-slate-800 text-amber-300 hover:text-white border border-amber-500/30 transition-all"
            >
              <span>💬</span> Retail Momentum Report &rarr;
            </Link>
            <Link
              href={`/smart-money/${report.ticker}${reportDate ? `?date=${reportDate}` : ""}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-900/80 hover:bg-slate-800 text-purple-300 hover:text-white border border-purple-500/30 transition-all"
            >
              <span>🏛️</span> Smart Money Catalyst Report &rarr;
            </Link>
            <Link
              href={`/analytics?ticker=${report.ticker}`}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-900/80 hover:bg-slate-800 text-indigo-300 hover:text-white border border-indigo-500/30 hover:border-indigo-500/60 transition-all shadow-lg shadow-indigo-500/5 group"
            >
              <span>📊</span> Trajectory & Analytics{" "}
              <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
            </Link>
          </div>
        </div>

        {/* Hero Section */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 sm:p-8 backdrop-blur-sm mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-800/60">
            <div>
              <div className="flex flex-wrap items-center gap-2.5 mb-2">
                <span className="px-2.5 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                  ⚡ Unified Master Report
                </span>
                {reportDate && (
                  <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                    📅 Historical Run: {reportDate}
                  </span>
                )}
                {synthesis?.archetype && getArchetypeBadge(synthesis.archetype)}
                {synthesis?.recommended_action && (
                  <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-800 text-white border border-slate-700">
                    Action: {synthesis.recommended_action}
                  </span>
                )}
                {retailOverlay?.has_data && retailOverlay.recommendation && (
                  <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-bold border ${recColorStyles[retailOverlay.recommendation]}`}>
                    Retail: {retailOverlay.recommendation}
                  </span>
                )}
              </div>

              <h1 className="text-4xl md:text-5xl font-black text-white leading-none tracking-tight">
                ${report.ticker}{" "}
                <span className="text-xl md:text-2xl font-bold text-slate-400 ml-2">
                  {report.company_name}
                </span>
              </h1>
              <p className="text-slate-400 text-sm font-medium mt-1">
                {report.sector || report.raw_metrics?.sector || "Technology"} &bull;{" "}
                {report.industry || report.raw_metrics?.industry || "General"}
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
              {report.potential_upside !== null && report.potential_upside !== undefined && (
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Projected Upside</span>
                  <span
                    className={`text-2xl font-black ${
                      report.potential_upside >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {report.potential_upside >= 0 ? `+${report.potential_upside.toFixed(1)}%` : `${report.potential_upside.toFixed(1)}%`}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Synthesis Diagnosis - Full Width */}
          {synthesis?.synthesis_diagnosis && (
            <div className="mt-6 p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/20 text-xs text-indigo-200/90 leading-relaxed">
              <span className="font-bold text-indigo-400 block mb-1 uppercase tracking-wider text-[10px]">
                ⚡ Cross-Engine Synthesis Diagnosis
              </span>
              <p>{synthesis.synthesis_diagnosis}</p>
            </div>
          )}

          {/* Quick Metrics Bar */}
          <div className="mt-4 pt-4 border-t border-slate-800/50 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex gap-6">
              <div>
                <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-0.5">
                  Timing Alpha Edge
                </span>
                <span className="font-extrabold text-emerald-400">
                  {synthesis?.timing_edge_score ? `${synthesis.timing_edge_score.toFixed(0)}/100` : "N/A"}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-0.5">
                  Market Cap
                </span>
                <span className="font-extrabold text-slate-300">
                  {formatMarketCap(report.raw_metrics?.market_cap)}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-0.5">
                  Retail Awareness
                </span>
                <span className="font-semibold text-slate-300 text-xs">
                  {synthesis?.retail_awareness_level || "Stealth"}
                </span>
              </div>
            </div>

            {smOverlay?.has_data && (
              <span className="px-3 py-1 rounded-lg text-xs font-bold bg-purple-500/10 text-purple-300 border border-purple-500/30">
                🏛️ Institutional Conviction: {smOverlay.conviction_score?.toFixed(1)}
              </span>
            )}
          </div>
        </div>

        {/* Actionable Watchpoint Callout */}
        <div className="bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-slate-900/30 border border-indigo-500/20 rounded-2xl p-6 md:p-8 mb-8 backdrop-blur-sm relative overflow-hidden">
          <div className="flex flex-col md:flex-row gap-6 items-start relative">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/20 text-indigo-300 flex items-center justify-center shrink-0 font-bold text-2xl shadow-inner shadow-indigo-500/20">
              💡
            </div>
            <div className="space-y-3">
              <h3 className="text-lg font-black text-white">Actionable Catalyst Watchpoint</h3>
              <p className="text-slate-200 text-sm leading-relaxed font-semibold">
                &ldquo;{report.reconciliation_actionable_insight}&rdquo;
              </p>
              {smOverlay?.catalyst_horizon && (
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  ⏳ Projected Catalyst Horizon: {smOverlay.catalyst_horizon}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* CROSS-ENGINE DIVERGENCE SCORECARD & CONTRARIAN PLAYBOOK */}
        <div className="mb-10">
          <ContrarianPlaybook
            ticker={report.ticker}
            archetype={synthesis?.archetype}
            timingEdgeScore={synthesis?.timing_edge_score ?? 50}
            retailAwarenessLevel={synthesis?.retail_awareness_level ?? (retailOverlay?.has_data ? "Active Discussion" : "Zero Awareness (Stealth)")}
            retailSentiment={retailOverlay?.community_sentiment ?? report.community_sentiment ?? "Neutral"}
            retailMentions={retailOverlay?.mention_count ?? 0}
            retailRank={retailOverlay?.rank}
            smartMoneyConviction={smOverlay?.conviction_score ?? 0}
            smartMoneyTier={smOverlay?.conviction_tier ?? "Neutral"}
            smartMoneyFlow={smOverlay?.has_data ? "Heavy Inflow" : "Neutral / Monitoring"}
            diagnosis={synthesis?.synthesis_diagnosis}
            recommendedAction={synthesis?.recommended_action ?? "WATCH"}
          />
        </div>

        {/* SECTION 1: CORE FUNDAMENTALS & GROUND TRUTH */}
        <div className="mb-10">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Section 1</span>
            <h2 className="text-xl font-black text-white tracking-tight">Core Equity Intelligence & Ground Truth</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {/* Ground Truth Status */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-start backdrop-blur-sm">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-6 h-6 rounded bg-purple-500/10 text-purple-400 flex items-center justify-center text-xs font-bold">
                    🏢
                  </span>
                  <h3 className="font-extrabold text-slate-200">Competitive Moat</h3>
                </div>
                <p className="text-slate-300 text-xs leading-relaxed">{report.ground_truth_status}</p>
              </div>
            </div>

            {/* Filings & News Analysis */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-start backdrop-blur-sm">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-6 h-6 rounded bg-blue-500/10 text-blue-400 flex items-center justify-center text-xs font-bold">
                    📄
                  </span>
                  <h3 className="font-extrabold text-slate-200">SEC 10-Q & 8-K Highlights</h3>
                </div>
                <FilingHighlights text={report.ground_truth_filings_news} />
              </div>
            </div>

            {/* Events & Happenings */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-start backdrop-blur-sm">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-6 h-6 rounded bg-rose-500/10 text-rose-400 flex items-center justify-center text-xs font-bold">
                    💥
                  </span>
                  <h3 className="font-extrabold text-slate-200">Events & Macro Catalysts</h3>
                </div>
                <p className="text-slate-300 text-xs leading-relaxed">{report.events_happenings}</p>
              </div>
            </div>

            {/* Risk Assessment */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-start space-y-4 backdrop-blur-sm">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded bg-teal-500/10 text-teal-400 flex items-center justify-center text-xs font-bold">
                      ⚖️
                    </span>
                    <h3 className="font-extrabold text-slate-200">Risk Assessment</h3>
                  </div>
                  <span
                    className={`px-2 py-0.5 text-xs font-bold rounded border ${riskBadgeStyles(
                      report.reconciliation_risk_score
                    )}`}
                  >
                    {report.reconciliation_risk_score}
                  </span>
                </div>
                <p className="text-slate-300 text-xs leading-relaxed">{report.reconciliation_analysis}</p>
              </div>

              {/* Risk Assessment Table */}
              <div className="pt-3 border-t border-slate-800/60 space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                  Rating Decision Matrix
                </span>
                <div className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-950/60 border border-slate-800/60">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                    LOW
                  </span>
                  <span className="text-[11px] text-slate-300 leading-snug">
                    Strong balance sheet solvency, resilient free cash flow, low customer churn.
                  </span>
                </div>
                <div className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-950/60 border border-slate-800/60">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
                    MED
                  </span>
                  <span className="text-[11px] text-slate-300 leading-snug">
                    Cyclical exposure, debt maturities, or margin compression pressures.
                  </span>
                </div>
                <div className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-950/60 border border-slate-800/60">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 shrink-0">
                    HIGH
                  </span>
                  <span className="text-[11px] text-slate-300 leading-snug">
                    Solvency concerns, heavy dilutive financing, or extreme retail speculation.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 2: SMART MONEY & POLITICAL INFLOW OVERLAY */}
        <div className="mb-10">
          <div className="flex items-center justify-between gap-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-400">Section 2</span>
              <h2 className="text-xl font-black text-white tracking-tight">Smart Money & Political Inflow Overlay</h2>
            </div>
            {smOverlay?.has_data ? (
              <span className="text-xs font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2.5 py-1 rounded-lg">
                Active Inflow Candidate (${(smOverlay.total_buy_volume! / 1000).toFixed(0)}k Cluster)
              </span>
            ) : (
              <span className="text-xs font-medium text-slate-500 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800">
                No Active Inflow Cluster
              </span>
            )}
          </div>

          {smOverlay?.has_data && smOverlay.inflow_ledger && smOverlay.inflow_ledger.length > 0 ? (
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm space-y-6">
              {/* Ledger Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase font-black block mb-1">Buyers</span>
                  <span className="text-xs font-semibold text-slate-200">
                    {smOverlay.top_buyer_summary || "Multiple executive filings"}
                  </span>
                </div>
                <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase font-black block mb-1">Conviction Tier</span>
                  <span className="text-xs font-bold text-purple-300">{smOverlay.conviction_tier}</span>
                </div>
                {smOverlay.catalyst_horizon && (
                  <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl">
                    <span className="text-[10px] text-slate-500 uppercase font-black block mb-1">Projected Horizon</span>
                    <span className="text-xs font-bold text-amber-300">⏳ {smOverlay.catalyst_horizon}</span>
                  </div>
                )}
              </div>

              {/* Actionable Thesis Callout - Full Width & Non-Italic */}
              {smOverlay.actionable_thesis && (
                <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-800/40 space-y-1.5">
                  <span className="text-[10px] text-purple-400 uppercase font-black tracking-wider block">
                    ⚡ Actionable Thesis & Swing Strategy
                  </span>
                  <p className="text-xs font-medium text-slate-200 leading-relaxed font-sans">
                    {smOverlay.actionable_thesis}
                  </p>
                </div>
              )}

              {/* Inflow Ledger Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-2">
                    <tr>
                      <th className="py-2">Date</th>
                      <th className="py-2">Buyer / Politician</th>
                      <th className="py-2">Role / Committee</th>
                      <th className="py-2">Trade Price</th>
                      <th className="py-2">Shares</th>
                      <th className="py-2 text-right">Value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {smOverlay.inflow_ledger.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-950/40 transition-colors">
                        <td className="py-2.5 text-slate-400 font-mono">{item.date || "N/A"}</td>
                        <td className="py-2.5 font-bold text-white">{item.buyer || "Executive"}</td>
                        <td className="py-2.5 text-slate-300">{item.role || item.committee || "Officer"}</td>
                        <td className="py-2.5 font-bold text-indigo-300 font-mono">{item.price || "N/A"}</td>
                        <td className="py-2.5 text-slate-300 font-mono">
                          {item.shares ? item.shares.toLocaleString() : "-"}
                        </td>
                        <td className="py-2.5 text-right font-black text-emerald-400 font-mono">
                          {item.value || "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-2xl bg-slate-900/30 border border-slate-800/80 text-center">
              <p className="text-xs text-slate-400 italic">
                No significant C-suite Form 4 cluster buys or Congressional STOCK Act trade disclosures recorded for ${report.ticker} in the current intelligence window.
              </p>
            </div>
          )}
        </div>

        {/* SECTION 3: RETAIL MOMENTUM & REDDIT OVERLAY */}
        <div className="mb-10">
          <div className="flex items-center justify-between gap-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-orange-400">Section 3</span>
              <h2 className="text-xl font-black text-white tracking-tight">Retail Momentum & Social Sentiment Overlay</h2>
            </div>
            {retailOverlay?.has_data ? (
              <span className="text-xs font-bold text-orange-400 bg-orange-950/60 border border-orange-800/60 px-2.5 py-1 rounded-lg">
                Active Retail Discussion ({retailOverlay.mention_count} mentions)
              </span>
            ) : (
              <span className="text-xs font-medium text-slate-500 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800">
                Stealth / Zero Reddit Hype
              </span>
            )}
          </div>

          {retailOverlay?.has_data ? (
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/60">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-black block">Reddit Sentiment</span>
                  <span className="text-sm font-bold text-indigo-300">{retailOverlay.community_sentiment}</span>
                </div>
                {retailOverlay.recommendation_rationale && (
                  <p className="text-xs text-slate-400 max-w-xl italic">
                    &ldquo;{retailOverlay.recommendation_rationale}&rdquo;
                  </p>
                )}
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{retailOverlay.community_hype}</p>

              {/* Quantitative Rating Decision Gate */}
              {(() => {
                const rec = retailOverlay.recommendation || report.recommendation;
                const upsideVal = report.potential_upside;
                return (
                  <div className="mt-4 p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${rec === "BUY" ? "bg-emerald-400" : rec === "SELL" ? "bg-rose-400" : "bg-amber-400"} animate-pulse`} />
                      <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                        Quantitative Rating Decision Gate: <span className={rec === "BUY" ? "text-emerald-400" : rec === "SELL" ? "text-rose-400" : "text-amber-400"}>{rec}</span>
                      </span>
                    </div>
                    <div className="text-xs text-slate-300 leading-relaxed font-sans">
                      {rec === "BUY" ? (
                        <p>
                          <strong>Why BUY?</strong> Projected upside of <strong>+{upsideVal ? upsideVal.toFixed(1) : "0"}%</strong> clears the 18% quantitative hurdle rate and is supported by fundamental cash flow solvency and healthy margins.
                        </p>
                      ) : rec === "HOLD" ? (
                        <p>
                          <strong>Why HOLD?</strong> {upsideVal && upsideVal >= 18.0 ? `Although the target price indicates +${upsideVal.toFixed(1)}% technical upside, the engine triggered a capital preservation gate. Near-term guidance headwinds, customer churn, or post-earnings capitulation introduce excessive variance, superseding the target upside to enforce a prudent HOLD.` : `Projected upside (+${upsideVal ? upsideVal.toFixed(1) : "0"}%) does not clear the 18% minimum hurdle rate necessary to offset single-stock volatility.`}
                        </p>
                      ) : (
                        <p>
                          <strong>Why SELL?</strong> Disclosed operational deterioration, negative free cash flow trajectory, or severe valuation bubble warnings indicate retail enthusiasm is disconnected from financial reality.
                        </p>
                      )}
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : (
            <div className="p-6 rounded-2xl bg-slate-900/30 border border-slate-800/80 text-center">
              <p className="text-xs text-slate-400 italic">
                🤫 Silent Accumulation: Near-zero discussion on Reddit (r/wallstreetbets, r/stocks, r/ValueInvesting). Maximum pre-catalyst timing edge.
              </p>
            </div>
          )}
        </div>

        {/* SECTION 4: INSTITUTIONAL WHALE OPTIONS RADAR */}
        <div className="mb-10">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-purple-400">Section 4</span>
            <h2 className="text-xl font-black text-white tracking-tight">Institutional Whale Options Radar</h2>
          </div>
          <OptionsFlowCard
            ticker={report.ticker}
            whaleScore={optionsData?.whale_score ?? 0}
            unusualOiMultiplier={optionsData?.unusual_oi_multiplier ?? 1.0}
            putCallRatio={optionsData?.put_call_ratio ?? 1.0}
            netBullishPremium={optionsData?.net_bullish_premium ?? 0}
            sentimentBias={optionsData?.sentiment_bias ?? "Neutral Tape"}
            topStrikeSummary={optionsData?.top_strike_summary}
            unusualContracts={optionsData?.unusual_contracts ?? []}
          />
        </div>

        {/* SECTION 5: FINANCIAL RATIOS & NEWS */}
        <div className="grid gap-6 md:grid-cols-2 mb-10">
          {/* Key Financial Metrics */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
            <h3 className="font-extrabold text-slate-200 text-lg mb-6 flex items-center gap-2">
              <span>📊</span> Valuation Ratios & Range
            </h3>
            <div className="space-y-4 text-xs">
              <div className="flex justify-between items-center py-2.5 border-b border-slate-800/60">
                <span className="text-slate-500">Trailing P/E Ratio</span>
                <span className="font-extrabold text-slate-300">
                  {report.raw_metrics?.pe_ratio ? report.raw_metrics.pe_ratio.toFixed(2) : "N/A"}
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-slate-800/60">
                <span className="text-slate-500">Forward P/E Ratio</span>
                <span className="font-extrabold text-slate-300">
                  {report.raw_metrics?.forward_pe ? report.raw_metrics.forward_pe.toFixed(2) : "N/A"}
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-slate-800/60">
                <span className="text-slate-500">52-Week High</span>
                <span className="font-extrabold text-emerald-400">
                  {report.raw_metrics?.fifty_two_week_high ? `$${report.raw_metrics.fifty_two_week_high.toFixed(2)}` : "N/A"}
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-slate-800/60">
                <span className="text-slate-500">52-Week Low</span>
                <span className="font-extrabold text-rose-400">
                  {report.raw_metrics?.fifty_two_week_low ? `$${report.raw_metrics.fifty_two_week_low.toFixed(2)}` : "N/A"}
                </span>
              </div>
            </div>
          </div>

          {/* Recent News headlines */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
            <h3 className="font-extrabold text-slate-200 text-lg mb-6 flex items-center gap-2">
              <span>📰</span> Corporate News Headlines
            </h3>
            {report.raw_news && report.raw_news.length > 0 && report.raw_news.some((item) => item.title) ? (
              <div className="space-y-4">
                {report.raw_news.map((item, idx) => {
                  if (!item.title) return null;
                  return (
                    <div key={idx} className="pb-3 border-b border-slate-800/40 last:border-0 last:pb-0">
                      {item.link ? (
                        <a
                          href={item.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-slate-300 hover:text-indigo-400 text-xs font-semibold leading-relaxed block hover:underline transition-colors"
                        >
                          {item.title}
                        </a>
                      ) : (
                        <span className="text-slate-300 text-xs font-semibold leading-relaxed block">
                          {item.title}
                        </span>
                      )}
                      <span className="text-[10px] text-slate-500 block mt-1 font-medium">
                        Publisher: {item.publisher || "Corporate Press"}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500 py-4 italic text-center">
                No recent headlines found for this security.
              </p>
            )}
          </div>
        </div>

        {/* Bottom Navigation */}
        <div className="mt-12 pt-6 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
          {reportDate ? (
            <Link href="/stats" className="text-xs font-semibold text-amber-400 hover:text-amber-300 transition-colors">
              &larr; Return to Historical Reports ({reportDate})
            </Link>
          ) : (
            <Link href="/" className="text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors">
              &larr; Return to Daily Dashboard
            </Link>
          )}
          <Link
            href={`/analytics?ticker=${report.ticker}`}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 transition-all group"
          >
            <span>📊</span> View Multi-Run Trajectory & Analytics for ${report.ticker}{" "}
            <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
          </Link>
        </div>
      </main>
    </div>
  );
}

export default function ReportPage({ params }: { params: Promise<{ ticker: string }> }) {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center gap-4">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm font-medium animate-pulse">
            Loading Unified Master Report...
          </p>
        </div>
      }
    >
      <ReportPageContent params={params} />
    </Suspense>
  );
}
