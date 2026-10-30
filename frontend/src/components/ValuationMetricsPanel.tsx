"use client";

import { HistoryPoint } from "./PriceTrajectoryChart";

interface ValuationMetricsPanelProps {
  data: HistoryPoint[];
}

export default function ValuationMetricsPanel({ data }: ValuationMetricsPanelProps) {
  // Grab latest metrics from the newest run
  const latest = data[data.length - 1];
  const metrics = latest?.raw_metrics || {};

  const formatMarketCap = (num?: number | null) => {
    if (!num) return "N/A";
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
  };

  return (
    <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
      <div className="mb-6">
        <h3 className="text-lg font-black text-white">Valuation Multiples & Trading Range</h3>
        <p className="text-xs text-slate-400">
          Financial fundamentals snapshot from the latest pipeline run
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/60">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Trailing P/E
          </span>
          <span className="text-lg font-black text-white">
            {metrics.pe_ratio ? metrics.pe_ratio.toFixed(1) : "N/A"}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/60">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Forward P/E
          </span>
          <span className="text-lg font-black text-white">
            {metrics.forward_pe ? metrics.forward_pe.toFixed(1) : "N/A"}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/60">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Market Cap
          </span>
          <span className="text-lg font-black text-white">
            {formatMarketCap(metrics.market_cap)}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/60">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Analyst Stance
          </span>
          <span className="text-lg font-black capitalize text-indigo-400">
            {metrics.recommendation_key || "N/A"}
          </span>
        </div>
      </div>

      {/* 52-Week Range Bar */}
      {metrics.fifty_two_week_low && metrics.fifty_two_week_high && latest.current_price && (
        <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/40">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-slate-400">
              52W Low: <strong className="text-white">${metrics.fifty_two_week_low.toFixed(2)}</strong>
            </span>
            <span className="text-xs font-bold text-indigo-300">
              Current: ${latest.current_price.toFixed(2)}
            </span>
            <span className="text-slate-400">
              52W High: <strong className="text-white">${metrics.fifty_two_week_high.toFixed(2)}</strong>
            </span>
          </div>

          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden relative">
            {(() => {
              const low = metrics.fifty_two_week_low;
              const high = metrics.fifty_two_week_high;
              const cur = latest.current_price;
              const pct = Math.max(0, Math.min(100, ((cur - low) / (high - low)) * 100));
              return (
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                  style={{ width: `${pct}%` }}
                />
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}

