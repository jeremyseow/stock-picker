"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Ticker {
  id: number;
  ticker: string;
  rank: number;
  mention_count: number;
  engagement_score: number;
  date: string;
}

export default function StatsPage() {
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/stats")
      .then((res) => res.json())
      .then((data) => {
        setTickers(data);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background Blur */}
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
            <Link href="/stats" className="text-sm font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
              Historical Trends
            </Link>
          </nav>
        </div>
      </header>

      {/* Main Body */}
      <main className="max-w-6xl mx-auto px-6 py-12 relative">
        <div className="mb-12">
          <h1 className="text-4xl font-black tracking-tight text-white mb-2 leading-none">
            Historical Trends
          </h1>
          <p className="text-slate-400 text-sm">
            All-time historical list of trending tickers extracted from social media.
          </p>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 text-xs">Loading analytics data...</p>
          </div>
        ) : (
          <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl overflow-hidden backdrop-blur-sm shadow-xl">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-800/80 text-left text-sm">
                <thead className="bg-slate-900/60">
                  <tr>
                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Ticker</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Mentions</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Max Engagement</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Date Scraped</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850 bg-slate-950/20">
                  {tickers.map((t, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/20 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap font-black text-white text-base">${t.ticker}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-300 font-semibold">{t.mention_count}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-300 font-semibold">{t.engagement_score.toLocaleString(undefined, { maximumFractionDigits: 1 })}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-400">{new Date(t.date).toLocaleDateString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-xs font-bold">
                        <Link href={`/report/${t.ticker}`} className="text-indigo-400 hover:text-indigo-300 transition-colors">
                          View Intel &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
