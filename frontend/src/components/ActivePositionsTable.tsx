"use client";

import { useState } from "react";

export interface OpenPositionItem {
  id: number;
  account_id: number;
  ticker: string;
  archetype: string;
  conviction_score: number;
  status: string;
  shares: number;
  entry_date: string;
  entry_price: number;
  current_price: number | null;
  target_price: number | null;
  stop_loss_price: number;
  unrealized_pnl: number | null;
  return_pct: number | null;
  holding_days: number;
  spy_entry_price: number | null;
}

interface ActivePositionsTableProps {
  positions: OpenPositionItem[];
  onClosePosition: (positionId: number) => Promise<void>;
}

export default function ActivePositionsTable({
  positions,
  onClosePosition,
}: ActivePositionsTableProps) {
  const [closingId, setClosingId] = useState<number | null>(null);

  const handleClose = async (id: number, ticker: string) => {
    if (!window.confirm(`Are you sure you want to manually close position ${ticker} at market price?`)) {
      return;
    }
    setClosingId(id);
    try {
      await onClosePosition(id);
    } finally {
      setClosingId(null);
    }
  };

  const getArchetypeBadge = (archetype: string) => {
    if (archetype === "The Rocket") {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-purple-500/20 text-purple-300 border border-purple-500/30">
          🚀 Rocket
        </span>
      );
    }
    if (archetype === "Silent Accumulation") {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
          🏦 Accumulation
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-slate-700 text-slate-300">
        {archetype}
      </span>
    );
  };

  if (!positions || positions.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center min-h-[220px] text-center">
        <div className="w-10 h-10 rounded-xl bg-slate-800 text-slate-400 flex items-center justify-center text-xl mb-2">
          💼
        </div>
        <h3 className="text-sm font-semibold text-slate-200">No Active Positions</h3>
        <p className="text-xs text-slate-400 max-w-sm mt-1">
          The simulated portfolio is currently 100% in cash. New high-conviction signals will be executed at the next US Market Open.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-base font-bold text-slate-100">Active Portfolio Holdings</h2>
          <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold">
            {positions.length} / 10 Slots Active
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-950/40 text-slate-400 border-b border-slate-800/80 font-semibold uppercase tracking-wider">
              <th className="py-3 px-4">Ticker</th>
              <th className="py-3 px-3">Archetype</th>
              <th className="py-3 px-3">Shares</th>
              <th className="py-3 px-3">Entry Price</th>
              <th className="py-3 px-3">Mark Price</th>
              <th className="py-3 px-3">Unrealized PnL</th>
              <th className="py-3 px-3">Return</th>
              <th className="py-3 px-3">Holding</th>
              <th className="py-3 px-3">Stop / Target</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {positions.map((pos) => {
              const pnl = pos.unrealized_pnl || 0;
              const ret = pos.return_pct || 0;
              const isProfit = pnl >= 0;

              return (
                <tr key={pos.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-sm text-slate-100">{pos.ticker}</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {pos.conviction_score.toFixed(0)} pts
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500">
                      Entry: {pos.entry_date ? pos.entry_date.substring(0, 10) : "N/A"}
                    </span>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    {getArchetypeBadge(pos.archetype)}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-200">
                    {pos.shares.toLocaleString()}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-200">
                    ${pos.entry_price.toFixed(2)}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-100 font-bold">
                    ${(pos.current_price ?? pos.entry_price).toFixed(2)}
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold">
                    <span className={isProfit ? "text-emerald-400" : "text-rose-400"}>
                      {isProfit ? "+" : ""}${pnl.toFixed(2)}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono font-bold">
                    <span
                      className={`inline-block px-1.5 py-0.5 rounded text-[11px] ${
                        isProfit
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}
                    >
                      {isProfit ? "+" : ""}
                      {ret.toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-300">
                    <span className="font-medium">{pos.holding_days}d</span>
                  </td>
                  <td className="py-3 px-3 text-[11px] font-mono">
                    <div className="text-rose-400/90">
                      Stop: ${pos.stop_loss_price.toFixed(2)}
                    </div>
                    <div className="text-emerald-400/90">
                      Tgt: ${pos.target_price ? pos.target_price.toFixed(2) : "N/A"}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={() => handleClose(pos.id, pos.ticker)}
                      disabled={closingId === pos.id}
                      className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-rose-500/10 text-rose-300 hover:bg-rose-500/25 border border-rose-500/30 transition-all disabled:opacity-50"
                    >
                      {closingId === pos.id ? "Closing..." : "Close Now"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

