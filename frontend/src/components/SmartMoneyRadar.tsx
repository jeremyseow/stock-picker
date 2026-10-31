"use client";

export interface InsiderTransaction {
  date: string;
  insider: string;
  position: string;
  shares: number;
  value: number;
  text: string;
  type: "BUY" | "SELL" | "OTHER";
  ownership: string;
}

export interface CongressionalTrade {
  title?: string;
  link?: string;
  snippet?: string;
}

export interface RawInsiderData {
  has_data?: boolean;
  purchases_shares?: number;
  purchases_trans?: number;
  sales_shares?: number;
  sales_trans?: number;
  net_shares?: number;
  total_held?: number;
  sentiment_label?: string;
  recent_transactions?: InsiderTransaction[];
  congressional_trades?: CongressionalTrade[];
  insider_activity_summary?: string;
}

interface SmartMoneyRadarProps {
  verdict?: string | null;
  insiderData?: RawInsiderData | null;
}

export default function SmartMoneyRadar({ verdict, insiderData }: SmartMoneyRadarProps) {
  const hasData = Boolean(insiderData && insiderData.has_data);
  const transactions = insiderData?.recent_transactions || [];
  const congressionalTrades = insiderData?.congressional_trades || [];

  const purchasesShares = insiderData?.purchases_shares || 0;
  const purchasesTrans = insiderData?.purchases_trans || 0;
  const salesShares = insiderData?.sales_shares || 0;
  const salesTrans = insiderData?.sales_trans || 0;
  const netShares = insiderData?.net_shares || 0;

  // Calculate ratio for visual flow gauge
  const totalVolume = purchasesShares + salesShares;
  const buyPercent = totalVolume > 0 ? (purchasesShares / totalVolume) * 100 : 50;
  const sellPercent = totalVolume > 0 ? (salesShares / totalVolume) * 100 : 50;

  const formatNumber = (num: number) => {
    return Math.abs(num).toLocaleString(undefined, { maximumFractionDigits: 0 });
  };

  const formatCurrency = (val: number) => {
    if (val === 0) return "$0";
    if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
    if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
    if (val >= 1e3) return `$${(val / 1e3).toFixed(1)}k`;
    return `$${val.toLocaleString()}`;
  };

  const getVerdictStyle = (v?: string | null) => {
    const text = (v || "").toLowerCase();
    if (text.includes("no form 4") || text.includes("no data") || text.includes("neutral")) {
      return {
        badge: "bg-slate-850 text-slate-300 border-slate-700",
        indicator: "📋",
      };
    }
    if (text.includes("bearish") || text.includes("selling") || text.includes("distribution") || text.includes("divergence")) {
      return {
        badge: "bg-rose-500/10 text-rose-400 border-rose-500/30",
        indicator: "🔴",
      };
    }
    if (text.includes("bullish") || text.includes("accumulation") || text.includes("buying")) {
      return {
        badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
        indicator: "🟢",
      };
    }
    return {
      badge: "bg-amber-500/10 text-amber-400 border-amber-500/30",
      indicator: "⚖️",
    };
  };

  const verdictStyle = getVerdictStyle(verdict);

  return (
    <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 md:p-8 backdrop-blur-sm shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center text-xl shadow-inner">
            👔
          </div>
          <div>
            <h3 className="text-xl font-black text-white flex items-center gap-2">
              Smart Money & Insider Trading Radar
            </h3>
            <p className="text-xs text-slate-400">
              Form 4 executive disclosures & Capitol Hill STOCK Act political trading
            </p>
          </div>
        </div>

        {verdict && (
          <div className="flex items-center gap-2 self-start sm:self-center">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Smart Money Verdict:
            </span>
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg border text-xs font-black tracking-wide ${verdictStyle.badge}`}
            >
              <span>{verdictStyle.indicator}</span>
              {verdict}
            </span>
          </div>
        )}
      </div>

      {/* AI Smart Money Synthesis Callout */}
      {insiderData?.insider_activity_summary && (
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 mb-6 text-xs text-slate-300 leading-relaxed flex gap-3 items-start">
          <span className="text-base shrink-0">💡</span>
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 block mb-1">
              AI Smart Money Synthesis
            </span>
            <p className="text-slate-300 text-xs leading-relaxed italic">
              "{insiderData.insider_activity_summary}"
            </p>
          </div>
        </div>
      )}

      {/* Form 4 Section */}
      <div className="space-y-6">
        {!hasData ? (
          <div className="bg-slate-950/40 border border-slate-900 rounded-xl p-6 text-center">
            <span className="text-2xl block mb-1">📋</span>
            <h4 className="text-xs font-bold text-slate-300">No Corporate Form 4 Filings Available</h4>
            <p className="text-[11px] text-slate-500 mt-1 max-w-md mx-auto">
              No recent SEC Form 4 executive insider transactions or 6-month aggregate statistics were reported for this security.
            </p>
          </div>
        ) : (
          <>
            {/* 6-Month Flow Gauge Card */}
            <div className="bg-slate-950/50 border border-slate-850 rounded-xl p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  6-Month Aggregate Executive Flow
                </span>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400">Net Flow:</span>
                  <span
                    className={`font-black ${
                      netShares > 0
                        ? "text-emerald-400"
                        : netShares < 0
                        ? "text-rose-400"
                        : "text-slate-300"
                    }`}
                  >
                    {netShares > 0 ? "+" : netShares < 0 ? "-" : ""}
                    {formatNumber(netShares)} shares
                  </span>
                </div>
              </div>

              {/* Split Flow Bar */}
              <div className="h-3 w-full bg-slate-900 rounded-full overflow-hidden flex border border-slate-800">
                {totalVolume > 0 ? (
                  <>
                    <div
                      style={{ width: `${buyPercent}%` }}
                      className="bg-emerald-500 transition-all duration-500"
                      title={`Insider Buying: ${buyPercent.toFixed(1)}%`}
                    />
                    <div
                      style={{ width: `${sellPercent}%` }}
                      className="bg-rose-500 transition-all duration-500"
                      title={`Insider Selling: ${sellPercent.toFixed(1)}%`}
                    />
                  </>
                ) : (
                  <div className="w-full bg-slate-800" title="No transaction volume" />
                )}
              </div>

              {/* Summary Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-850 text-xs">
                <div>
                  <span className="text-slate-400 text-[10px] font-bold uppercase block mb-0.5">
                    Insider Buying (6m)
                  </span>
                  <span className="font-extrabold text-emerald-400 text-sm">
                    {formatNumber(purchasesShares)} shares
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    {purchasesTrans} transactions
                  </span>
                </div>

                <div>
                  <span className="text-slate-400 text-[10px] font-bold uppercase block mb-0.5">
                    Insider Selling (6m)
                  </span>
                  <span className="font-extrabold text-rose-400 text-sm">
                    {formatNumber(salesShares)} shares
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    {salesTrans} transactions
                  </span>
                </div>

                <div className="col-span-2 sm:col-span-1">
                  <span className="text-slate-400 text-[10px] font-bold uppercase block mb-0.5">
                    Executive Sentiment
                  </span>
                  <span className="font-extrabold text-slate-200 text-sm capitalize">
                    {insiderData?.sentiment_label || "Neutral"}
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    Total Held: {formatNumber(insiderData?.total_held || 0)}
                  </span>
                </div>
              </div>
            </div>

            {/* Form 4 Transactions Table */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Recent Form 4 Executive Filings
                </h4>
                <span className="text-[11px] text-slate-400">
                  Showing latest {transactions.length} filings
                </span>
              </div>

              {transactions.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-4">No recent individual Form 4 filings recorded.</p>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/80 text-[10px] uppercase tracking-wider text-slate-400 font-bold border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-4">Date</th>
                        <th className="py-2.5 px-4">Insider / Position</th>
                        <th className="py-2.5 px-4">Type</th>
                        <th className="py-2.5 px-4 text-right">Shares</th>
                        <th className="py-2.5 px-4 text-right">Value</th>
                        <th className="py-2.5 px-4">Details</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/20">
                      {transactions.map((tx, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-3 px-4 font-mono text-slate-400 text-[11px] whitespace-nowrap">
                            {tx.date}
                          </td>
                          <td className="py-3 px-4">
                            <span className="font-bold text-slate-200 block truncate max-w-[180px]">
                              {tx.insider}
                            </span>
                            <span className="text-[10px] text-slate-400 truncate max-w-[180px] block">
                              {tx.position}
                            </span>
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            {tx.type === "BUY" ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-black bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                BUY
                              </span>
                            ) : tx.type === "SELL" ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-black bg-rose-500/10 text-rose-400 border border-rose-500/20">
                                SELL
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                                {tx.type}
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right font-mono font-bold text-slate-200">
                            {tx.shares > 0 ? formatNumber(tx.shares) : "-"}
                          </td>
                          <td className="py-3 px-4 text-right font-mono font-bold text-slate-200">
                            {tx.value > 0 ? formatCurrency(tx.value) : "-"}
                          </td>
                          <td className="py-3 px-4 text-slate-400 text-[11px] max-w-[220px] truncate" title={tx.text}>
                            {tx.text || "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

        {/* Congressional & Political Trading (STOCK Act) Section */}
        <div className="pt-6 border-t border-slate-800/80">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-base">🏛️</span>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Capitol Hill & Congressional Trades (STOCK Act Disclosures)
              </h4>
            </div>
            <span className="text-[11px] text-slate-400">
              {congressionalTrades.length > 0 ? `${congressionalTrades.length} filings detected` : "No filings"}
            </span>
          </div>

          {congressionalTrades.length === 0 ? (
            <div className="bg-slate-950/40 border border-slate-900 rounded-xl p-4 text-center">
              <p className="text-xs text-slate-500 italic">No recent Congressional stock trading disclosures detected for this ticker.</p>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {congressionalTrades.map((trade, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/50 border border-slate-800/60 rounded-xl p-3.5 hover:border-slate-700/80 transition-all flex flex-col justify-between"
                >
                  <div>
                    {trade.link ? (
                      <a
                        href={trade.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs font-bold text-slate-200 hover:text-indigo-400 leading-snug line-clamp-2 hover:underline transition-colors block mb-1"
                      >
                        {trade.title || "Congressional Trade Disclosure"}
                      </a>
                    ) : (
                      <span className="text-xs font-bold text-slate-200 leading-snug line-clamp-2 block mb-1">
                        {trade.title || "Congressional Trade Disclosure"}
                      </span>
                    )}
                    <p className="text-[11px] text-slate-400 line-clamp-3 leading-relaxed mt-1">
                      {trade.snippet}
                    </p>
                  </div>
                  {trade.link && (
                    <a
                      href={trade.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 transition-colors mt-2.5 inline-flex items-center gap-1 self-start"
                    >
                      View Disclosure Source &rarr;
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
