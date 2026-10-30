"use client";

import { HistoryPoint } from "./PriceTrajectoryChart";

interface SentimentTrajectoryTimelineProps {
  data: HistoryPoint[];
}

export default function SentimentTrajectoryTimeline({ data }: SentimentTrajectoryTimelineProps) {
  const getRecommendationBadge = (rec: "BUY" | "SELL" | "HOLD" | null) => {
    switch (rec) {
      case "BUY":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            🟢 BUY
          </span>
        );
      case "SELL":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            🔴 SELL
          </span>
        );
      case "HOLD":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            🟡 HOLD
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-slate-500/10 text-slate-400 border border-slate-500/20">
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

  return (
    <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
      <div className="mb-6">
        <h3 className="text-lg font-black text-white">Sentiment & Recommendation Progression</h3>
        <p className="text-xs text-slate-400">
          Chronological record of model recommendations and Reddit social sentiment across pipeline runs
        </p>
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {data.map((item, idx) => {
          const dateStr = item.date.split("T")[0];
          return (
            <div key={item.id || idx} className="relative group">
              {/* Timeline Dot */}
              <div className="absolute -left-[27px] top-1.5 w-3 h-3 rounded-full bg-indigo-500 border-2 border-slate-950 group-hover:scale-125 transition-transform" />

              <div className="bg-slate-950/50 border border-slate-800/70 hover:border-slate-700 rounded-xl p-4 transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-white">
                      📅 {dateStr}
                    </span>
                    {getRecommendationBadge(item.recommendation)}
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getRiskBadge(
                        item.reconciliation_risk_score
                      )}`}
                    >
                      Risk: {item.reconciliation_risk_score || "Medium"}
                    </span>
                  </div>

                  <div className="text-xs font-bold text-indigo-300">
                    Sentiment: {item.community_sentiment}
                  </div>
                </div>

                <div className="text-xs text-slate-300 mb-2">
                  <strong className="text-slate-400">Narrative: </strong>
                  {item.community_hype}
                </div>

                <div className="text-xs text-slate-400 italic">
                  &ldquo;{item.recommendation_rationale}&rdquo;
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

