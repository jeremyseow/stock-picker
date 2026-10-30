"use client";

import { useState, useEffect } from "react";

interface MetaAnalysisData {
  id?: number;
  ticker: string;
  created_at: string;
  report_count: number;
  divergence_analysis: string;
  catalyst_follow_through: string;
  trajectory_outlook: string;
}

interface MetaAnalysisCardProps {
  ticker: string;
  reportCount: number;
}

export default function MetaAnalysisCard({ ticker, reportCount }: MetaAnalysisCardProps) {
  const [analysis, setAnalysis] = useState<MetaAnalysisData | null>(null);
  const [isCached, setIsCached] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError("");

    fetch(`http://localhost:8000/api/analytics/ticker/${ticker}/meta-analysis`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to check trajectory analysis cache");
        return res.json();
      })
      .then((data) => {
        if (!isMounted) return;
        if (data.cached && data.analysis) {
          setAnalysis(data.analysis);
          setIsCached(true);
        } else {
          setAnalysis(null);
          setIsCached(false);
        }
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message);
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [ticker]);

  const handleGenerate = async (forceRefresh = false) => {
    setGenerating(true);
    setError("");
    try {
      const url = `http://localhost:8000/api/analytics/ticker/${ticker}/meta-analysis?force_refresh=${forceRefresh}`;
      const res = await fetch(url, { method: "POST" });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to generate trajectory meta-analysis");
      }
      const data = await res.json();
      setAnalysis(data.analysis);
      setIsCached(data.cached);
    } catch (err: any) {
      setError(err.message || "Error running meta-analysis");
    } finally {
      setGenerating(false);
    }
  };

  if (reportCount < 2) {
    return (
      <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-xl">🤖</span>
          <h3 className="text-base font-bold text-white">AI Trajectory Meta-Analysis</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-semibold border border-slate-700/50">
            Awaiting More Runs
          </span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">
          Longitudinal meta-analysis synthesizes multi-run trends, sentiment divergence, and catalyst follow-through.
          Because only <strong>1 pipeline run</strong> is recorded for ${ticker}, at least 1 more daily run is needed before an aggregated trajectory meta-analysis can be generated.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-indigo-950/20 via-slate-900/40 to-purple-950/20 border border-indigo-500/20 rounded-2xl p-6 backdrop-blur-sm shadow-xl relative overflow-hidden">
      {/* Background Accent */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">🤖</span>
            <h3 className="text-lg font-black text-white">AI Trajectory Meta-Analysis</h3>
            {analysis && (
              <span
                className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                  isCached
                    ? "bg-slate-800/80 text-slate-300 border-slate-700"
                    : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 animate-pulse"
                }`}
              >
                {isCached ? "⚡ Cached in DB" : "✨ Newly Generated"}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">
            Longitudinal synthesis of retail sentiment divergence, thesis milestones, and consensus stability across {reportCount} runs.
          </p>
        </div>

        <div>
          <button
            onClick={() => handleGenerate(!!analysis)}
            disabled={generating || loading}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50 cursor-pointer active:scale-95"
          >
            {generating ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Synthesizing Trends...
              </>
            ) : analysis ? (
              <>🔄 Re-analyze Trajectory</>
            ) : (
              <>⚡ Generate Meta-Analysis</>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-8 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
          <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          Checking cached meta-analysis...
        </div>
      ) : !analysis ? (
        <div className="py-6 text-center bg-slate-950/40 rounded-xl border border-slate-800/50 p-6">
          <p className="text-xs text-slate-300 font-medium mb-3">
            No trajectory analysis has been generated yet for ${ticker} across its {reportCount} historical runs.
          </p>
          <button
            onClick={() => handleGenerate(false)}
            disabled={generating}
            className="px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            Generate AI Trajectory Meta-Analysis
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Divergence Analysis */}
          <div className="bg-slate-950/50 border border-slate-800/60 rounded-xl p-5 flex flex-col">
            <div className="flex items-center gap-2 mb-2 text-indigo-400 font-bold text-xs uppercase tracking-wider">
              <span>📉</span> Sentiment vs. Price Divergence
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {analysis.divergence_analysis}
            </p>
          </div>

          {/* Catalyst Follow Through */}
          <div className="bg-slate-950/50 border border-slate-800/60 rounded-xl p-5 flex flex-col">
            <div className="flex items-center gap-2 mb-2 text-purple-400 font-bold text-xs uppercase tracking-wider">
              <span>🎯</span> Catalyst & Insight Follow-Through
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {analysis.catalyst_follow_through}
            </p>
          </div>

          {/* Trajectory Outlook */}
          <div className="bg-slate-950/50 border border-slate-800/60 rounded-xl p-5 flex flex-col">
            <div className="flex items-center gap-2 mb-2 text-emerald-400 font-bold text-xs uppercase tracking-wider">
              <span>🔭</span> Longitudinal Thesis & Outlook
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {analysis.trajectory_outlook}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

