"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { API_BASE } from "@/lib/api";

interface SmartMoneyCandidate {
  id: number;
  date: string;
  ticker: string;
  rank: number;
  conviction_score: number;
  insider_score: number;
  political_score: number;
  cluster_count: number;
  total_buy_volume: number;
  top_buyer_summary: string;
  conviction_tier: string;
  sector: string;
  industry: string;
  current_price: number | null;
  target_price: number | null;
}

export default function SmartMoneyPage() {
  const [candidates, setCandidates] = useState<SmartMoneyCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    fetch(`${API_BASE}/api/smart-money/today`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch Smart Money picks");
        return res.json();
      })
      .then((data) => {
        setCandidates(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTriggerRun = async () => {
    setRunning(true);
    try {
      const res = await fetch(`${API_BASE}/api/smart-money/trigger`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to run Smart Money scout");
      fetchData();
    } catch (err: any) {
      alert(err.message || "Error running Smart Money scout");
    } finally {
      setRunning(false);
    }
  };

  const getTierBadge = (tier: string) => {
    if (tier.includes("High Conviction")) {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          🟢 {tier}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
        ⚡ {tier}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background Glow */}
      <div className="absolute top-0 left-0 right-0 h-[450px] bg-gradient-to-b from-indigo-500/10 via-purple-500/5 to-transparent pointer-events-none blur-[120px]" />

      <Navbar />

      <main className="max-w-6xl mx-auto px-6 py-12 relative">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10 pb-6 border-b border-slate-800/80">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-3">
              <span>🏛️</span> Engine 2: Smart Money & Political Scout
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
              Institutional & Political Catalysts
            </h1>
            <p className="text-slate-400 text-sm mt-2 max-w-2xl leading-relaxed">
              Top-down equity discovery targeting market-wide SEC Form 4 insider cluster buying (Code P) and Congressional STOCK Act disclosures.
            </p>
          </div>

          <div>
            <button
              onClick={handleTriggerRun}
              disabled={running}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50 cursor-pointer active:scale-95"
            >
              {running ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Scouting Market...
                </>
              ) : (
                <>⚡ Run Smart Money Scout</>
              )}
            </button>
          </div>
        </div>

        {/* Loading / Error States */}
        {loading && (
          <div className="py-20 text-center flex flex-col items-center justify-center gap-3">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 text-sm">Ingesting Form 4 cluster buys and Congressional disclosures...</p>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm mb-6">
            Failed to load Smart Money data: {error}
          </div>
        )}

        {!loading && !error && candidates.length === 0 && (
          <div className="max-w-md mx-auto bg-slate-900/50 border border-slate-800 rounded-2xl p-8 text-center">
            <span className="text-3xl mb-3 block">🏛️</span>
            <h3 className="text-lg font-bold text-slate-300">No Smart Money picks yet</h3>
            <p className="text-slate-500 text-sm mt-1">
              Click <span className="text-indigo-400 font-semibold">&quot;Run Smart Money Scout&quot;</span> above to scan today&apos;s SEC Form 4 and Congressional filings.
            </p>
          </div>
        )}

        {/* Candidate Cards Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {candidates.map((c) => (
            <Link href={`/smart-money/${c.ticker}`} key={c.id} className="group">
              <div className="h-full bg-slate-900/40 border border-slate-800/80 hover:border-indigo-500/40 rounded-2xl p-6 hover:shadow-2xl hover:shadow-indigo-500/5 transition-all duration-300 backdrop-blur-sm hover:-translate-y-1 flex flex-col justify-between">
                <div>
                  {/* Top Bar */}
                  <div className="flex justify-between items-center mb-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700/50">
                      Rank #{c.rank}
                    </span>
                    {getTierBadge(c.conviction_tier)}
                  </div>

                  {/* Ticker & Buyer Summary */}
                  <div className="mb-2">
                    <h2 className="text-3xl font-black text-white group-hover:text-indigo-400 transition-colors">
                      ${c.ticker}
                    </h2>
                    <p className="text-xs text-slate-500 mt-1 truncate font-medium">
                      {c.sector} &bull; {c.industry}
                    </p>
                  </div>

                  {/* Inflow Summary Banner */}
                  <div className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-xl mb-4 text-xs text-slate-300">
                    <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-1">Inflow Signal</span>
                    <p className="line-clamp-2 leading-relaxed text-[11px] font-medium text-slate-200">
                      {c.top_buyer_summary || "Form 4 Open-Market Purchases detected."}
                    </p>
                  </div>

                  {/* Pricing Overview */}
                  {c.current_price !== null && (
                    <div className="bg-slate-950/50 border border-slate-850 rounded-xl p-3 mb-4 flex justify-between items-center text-sm">
                      <div>
                        <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider">Live Price</span>
                        <span className="text-slate-200 font-extrabold text-base">${c.current_price.toFixed(2)}</span>
                      </div>
                      {c.target_price !== null && (
                        <div className="text-right">
                          <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider">Target Price</span>
                          <span className="text-slate-200 font-extrabold text-base">${c.target_price.toFixed(2)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Score & Volume Grid */}
                  <div className="grid grid-cols-2 gap-3 border-t border-slate-800/60 pt-4 text-xs text-slate-400">
                    <div>
                      <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-0.5">Conviction Score</span>
                      <span className="font-extrabold text-indigo-400 text-sm">{c.conviction_score.toFixed(1)}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px] font-bold uppercase tracking-wider mb-0.5">Buy Outlay</span>
                      <span className="font-extrabold text-slate-200 text-sm">
                        {c.total_buy_volume > 0 ? `$${(c.total_buy_volume / 1000).toFixed(0)}k` : "Disclosed"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800/40 flex items-center justify-between text-xs font-bold text-indigo-400 group-hover:text-indigo-300">
                  <span>View Catalyst Report</span>
                  <span>&rarr;</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}

