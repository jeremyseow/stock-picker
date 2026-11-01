"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { API_BASE } from "@/lib/api";

interface InflowEntry {
  type: string;
  name: string;
  role: string;
  price?: string;
  amount: string;
  date: string;
  delta_own: string;
}

interface SmartMoneyReportDetail {
  id: number;
  ticker: string;
  date: string;
  company_name: string;
  sector: string;
  industry: string;
  current_price: number | null;
  target_price: number | null;
  conviction_score: number;
  conviction_tier: string;
  inflow_ledger: InflowEntry[];
  political_catalyst_analysis: string;
  corporate_catalyst_analysis: string;
  catalyst_horizon: string;
  actionable_thesis: string;
  raw_metrics: Record<string, any>;
}

export default function SmartMoneyDetailPage() {
  const params = useParams();
  const ticker = (params.ticker as string)?.toUpperCase();
  const [report, setReport] = useState<SmartMoneyReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    fetch(`${API_BASE}/api/smart-money/report/${ticker}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load Smart Money report for ${ticker}`);
        return res.json();
      })
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [ticker]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background Glow */}
      <div className="absolute top-0 left-0 right-0 h-[450px] bg-gradient-to-b from-indigo-500/10 via-purple-500/5 to-transparent pointer-events-none blur-[120px]" />

      <Navbar />

      <main className="max-w-5xl mx-auto px-6 py-12 relative">
        {/* Breadcrumb & Navigation */}
        <div className="flex items-center justify-between gap-4 mb-8 text-xs font-semibold">
          <Link href="/smart-money" className="text-slate-400 hover:text-white transition-colors flex items-center gap-1.5">
            <span>&larr;</span> Back to Smart Money Scout
          </Link>
          <div className="flex items-center gap-3">
            <Link href={`/report/${ticker}`} className="text-indigo-400 hover:text-indigo-300 transition-colors">
              View Retail Report &rarr;
            </Link>
            <span className="text-slate-700">|</span>
            <Link href="/synthesis" className="text-purple-400 hover:text-purple-300 transition-colors">
              View Synthesis Matrix &rarr;
            </Link>
          </div>
        </div>

        {loading && (
          <div className="py-24 text-center flex flex-col items-center justify-center gap-3">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 text-sm">Synthesizing catalyst disclosures for ${ticker}...</p>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            {error}
          </div>
        )}

        {report && (
          <div className="space-y-8">
            {/* Hero Header */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 sm:p-8 backdrop-blur-sm">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-800/60">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-4xl font-black text-white">${report.ticker}</h1>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      🟢 {report.conviction_tier}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm font-medium">
                    {report.company_name} &bull; {report.sector} &bull; {report.industry}
                  </p>
                </div>

                <div className="flex items-center gap-6">
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
                  <div>
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Conviction</span>
                    <span className="text-2xl font-black text-purple-400">{report.conviction_score.toFixed(1)}</span>
                  </div>
                </div>
              </div>

              {/* Actionable Thesis Callout */}
              <div className="mt-6 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                <span className="text-indigo-400 text-[10px] font-extrabold uppercase tracking-wider block mb-1">
                  ⚡ Smart Money Swing Thesis
                </span>
                <p className="text-sm font-medium text-slate-200 leading-relaxed">
                  {report.actionable_thesis}
                </p>
              </div>
            </div>

            {/* Inflow Ledger */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 sm:p-8 backdrop-blur-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>🏛️</span> Smart Money Inflow Ledger
                </h2>
                <span className="text-xs text-slate-500">
                  {report.inflow_ledger?.length || 0} recorded filings
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800/80 text-slate-400 font-semibold">
                      <th className="py-2.5 px-3">Type</th>
                      <th className="py-2.5 px-3">Buyer / Politician</th>
                      <th className="py-2.5 px-3">Role / Chamber</th>
                      <th className="py-2.5 px-3">Price at Trade</th>
                      <th className="py-2.5 px-3">Transaction Value</th>
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3">Position Growth</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {report.inflow_ledger?.map((row, i) => (
                      <tr key={i} className="hover:bg-slate-800/20 transition-colors">
                        <td className="py-3 px-3 font-semibold text-slate-300">{row.type}</td>
                        <td className="py-3 px-3 font-bold text-white">{row.name}</td>
                        <td className="py-3 px-3 text-slate-400">{row.role}</td>
                        <td className="py-3 px-3 font-bold text-slate-200">{row.price && row.price !== "N/A" ? row.price : (report.current_price ? `~$${report.current_price.toFixed(2)}` : "Market")}</td>
                        <td className="py-3 px-3 font-extrabold text-emerald-400">{row.amount}</td>
                        <td className="py-3 px-3 text-slate-400">{row.date}</td>
                        <td className="py-3 px-3 text-indigo-400 font-medium">{row.delta_own}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Dual Catalyst Pillars Grid */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Political & Legislative Catalyst */}
              <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm flex flex-col justify-between">
                <div>
                  <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                    <span>📜</span> Political & Legislative Catalysts
                  </h3>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {report.political_catalyst_analysis}
                  </p>
                </div>
              </div>

              {/* Corporate Turnaround & Fundamental Catalyst */}
              <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm flex flex-col justify-between">
                <div>
                  <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                    <span>💼</span> Corporate Fundamentals & Turnaround
                  </h3>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {report.corporate_catalyst_analysis}
                  </p>
                </div>
              </div>
            </div>

            {/* Catalyst Horizon Banner */}
            <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  Catalyst Time Horizon
                </span>
                <span className="text-sm font-extrabold text-indigo-400">
                  {report.catalyst_horizon}
                </span>
              </div>
              <Link
                href="/synthesis"
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
              >
                Inspect Synthesis &rarr;
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

