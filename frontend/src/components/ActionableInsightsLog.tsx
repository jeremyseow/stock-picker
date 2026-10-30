"use client";

import { HistoryPoint } from "./PriceTrajectoryChart";

interface ActionableInsightsLogProps {
  data: HistoryPoint[];
}

export default function ActionableInsightsLog({ data }: ActionableInsightsLogProps) {
  return (
    <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
      <div className="mb-6">
        <h3 className="text-lg font-black text-white">Actionable Insights & Catalysts Log</h3>
        <p className="text-xs text-slate-400">
          Chronological record of key watchpoints, earnings metrics, and operational disclosures
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {data.map((item, idx) => {
          const dateStr = item.date.split("T")[0];
          return (
            <div
              key={item.id || idx}
              className="bg-slate-950/50 border border-slate-800/70 rounded-xl p-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-mono font-bold text-indigo-400">📅 {dateStr}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold">
                    Run #{idx + 1}
                  </span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-medium mb-3">
                  &ldquo;{item.reconciliation_actionable_insight}&rdquo;
                </p>
              </div>

              <div className="pt-2 border-t border-slate-900 text-[11px] text-slate-500">
                Ground Truth: {item.ground_truth_status}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

