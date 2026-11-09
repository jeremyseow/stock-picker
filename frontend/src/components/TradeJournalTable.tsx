"use client";

export interface ClosedTradeItem {
  id: number;
  account_id: number;
  ticker: string;
  archetype: string;
  conviction_score: number;
  shares: number;
  entry_date: string;
  entry_price: number;
  exit_date: string | null;
  exit_price: number | null;
  exit_reason: string | null;
  realized_pnl: number | null;
  return_pct: number | null;
  holding_days: number;
  spy_entry_price: number | null;
  spy_exit_price: number | null;
  spy_return_pct: number | null;
  excess_alpha_pct: number | null;
}

interface TradeJournalTableProps {
  trades: ClosedTradeItem[];
}

export default function TradeJournalTable({ trades }: TradeJournalTableProps) {
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

  const getExitReasonBadge = (reason: string | null, archetype?: string) => {
    const isRocket = archetype === "The Rocket";
    const stopLabel = isRocket ? "Stop-Loss (-5%)" : "Stop-Loss (-8%)";
    const tpLabel = isRocket ? "Take-Profit (+12%)" : "Take-Profit (+20%)";

    switch (reason) {
      case "STOP_LOSS":
        return (
          <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
            {stopLabel}
          </span>
        );
      case "TAKE_PROFIT":
        return (
          <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            {tpLabel}
          </span>
        );
      case "TIME_EXIT":
        return (
          <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
            Time Decay Exit
          </span>
        );
      case "MANUAL":
        return (
          <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-sky-500/15 text-sky-300 border border-sky-500/30">
            Manual Override
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-[11px] font-medium rounded bg-slate-800 text-slate-300">
            {reason || "CLOSED"}
          </span>
        );
    }
  };

  if (!trades || trades.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center min-h-[200px] text-center">
        <div className="w-10 h-10 rounded-xl bg-slate-800 text-slate-400 flex items-center justify-center text-xl mb-2">
          📖
        </div>
        <h3 className="text-sm font-semibold text-slate-200">No Closed Trades Yet</h3>
        <p className="text-xs text-slate-400 max-w-sm mt-1">
          Closed trades will be logged with exit reasons, realized PnL, holding duration, and benchmark alpha comparison.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-base font-bold text-slate-100">Trade Journal & Execution Audit</h2>
          <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 text-xs font-semibold">
            {trades.length} Completed Trades
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-950/40 text-slate-400 border-b border-slate-800/80 font-semibold uppercase tracking-wider">
              <th className="py-3 px-4">Ticker</th>
              <th className="py-3 px-3">Archetype</th>
              <th className="py-3 px-3">Entry & Exit</th>
              <th className="py-3 px-3">Holding</th>
              <th className="py-3 px-3">Exit Reason</th>
              <th className="py-3 px-3">Prices (In / Out)</th>
              <th className="py-3 px-3">Realized PnL</th>
              <th className="py-3 px-3">Return %</th>
              <th className="py-3 px-4 text-right">Alpha vs SPY</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {trades.map((t) => {
              const pnl = t.realized_pnl || 0;
              const isProfit = pnl >= 0;
              const alpha = t.excess_alpha_pct || 0;
              const isAlphaPos = alpha >= 0;

              return (
                <tr key={t.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-extrabold text-sm text-slate-100">
                    {t.ticker}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    {getArchetypeBadge(t.archetype)}
                  </td>
                  <td className="py-3 px-3 text-[11px] font-mono text-slate-400 whitespace-nowrap">
                    <div>In: {t.entry_date ? t.entry_date.substring(0, 10) : "N/A"}</div>
                    <div>Out: {t.exit_date ? t.exit_date.substring(0, 10) : "N/A"}</div>
                  </td>
                  <td className="py-3 px-3 text-slate-300 font-medium">
                    {t.holding_days}d
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    {getExitReasonBadge(t.exit_reason, t.archetype)}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300 whitespace-nowrap">
                    ${t.entry_price.toFixed(2)} → ${(t.exit_price ?? t.entry_price).toFixed(2)}
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
                      {(t.return_pct || 0).toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold whitespace-nowrap">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[11px] ${
                        isAlphaPos
                          ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                          : "bg-rose-500/15 text-rose-300 border border-rose-500/30"
                      }`}
                    >
                      {isAlphaPos ? "+" : ""}
                      {alpha.toFixed(2)}%
                    </span>
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

