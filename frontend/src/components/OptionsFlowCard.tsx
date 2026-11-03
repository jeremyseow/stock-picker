"use client";

interface OptionsContract {
  type: string;
  strike: number;
  expiration: string;
  dte: number;
  volume: number;
  open_interest: number;
  ratio: number;
  premium: number;
  is_sweep?: boolean;
}

interface OptionsFlowCardProps {
  ticker: string;
  whaleScore?: number;
  unusualOiMultiplier?: number;
  putCallRatio?: number;
  netBullishPremium?: number;
  sentimentBias?: string;
  topStrikeSummary?: string;
  unusualContracts?: OptionsContract[];
}

export default function OptionsFlowCard({
  ticker,
  whaleScore = 0,
  unusualOiMultiplier = 1.0,
  putCallRatio = 1.0,
  netBullishPremium = 0,
  sentimentBias = "Neutral Tape",
  topStrikeSummary,
  unusualContracts = [],
}: OptionsFlowCardProps) {
  const isHighConviction = whaleScore >= 50;

  return (
    <div className="rounded-2xl bg-slate-900/40 border border-slate-800 p-6 space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg">🐳</span>
            <h2 className="text-lg font-bold text-white">
              Institutional Whale Options Radar
            </h2>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                isHighConviction
                  ? "bg-purple-500/10 text-purple-300 border border-purple-500/30"
                  : "bg-slate-800 text-slate-400 border border-slate-700"
              }`}
            >
              Whale Conviction: {whaleScore.toFixed(0)}/100
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Engine 3 institutional footprint: Aggressive call sweeps, volume/OI spikes, and put/call sentiment.
          </p>
        </div>
        <div className="text-xs font-semibold px-3 py-1 rounded-lg bg-indigo-950/60 border border-indigo-800/60 text-indigo-300">
          {sentimentBias}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-500 uppercase font-bold block">
            Put / Call Ratio
          </span>
          <span className="text-lg font-extrabold text-white mt-1 block">
            {putCallRatio.toFixed(2)}
          </span>
          <span className="text-[11px] text-slate-400">
            {putCallRatio <= 0.6 ? "Bullish call skew" : putCallRatio >= 1.2 ? "Bearish put skew" : "Balanced flow"}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-500 uppercase font-bold block">
            Peak Volume / OI
          </span>
          <span className="text-lg font-extrabold text-emerald-400 mt-1 block">
            {unusualOiMultiplier.toFixed(1)}x
          </span>
          <span className="text-[11px] text-slate-400">
            {unusualOiMultiplier >= 2.5 ? "Unusual accumulation" : "Standard activity"}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-500 uppercase font-bold block">
            Net Bullish Premium
          </span>
          <span className="text-lg font-extrabold text-indigo-300 mt-1 block">
            ${(netBullishPremium / 1000).toFixed(0)}k
          </span>
          <span className="text-[11px] text-slate-400">OTM call sweeps</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-500 uppercase font-bold block">
            Key Sweeps Summary
          </span>
          <span className="text-xs font-semibold text-slate-200 mt-1 block truncate" title={topStrikeSummary || "None"}>
            {topStrikeSummary || "Standard options flow"}
          </span>
          <span className="text-[11px] text-slate-400">Target strike horizon</span>
        </div>
      </div>

      {/* Flagged Contracts Table */}
      {unusualContracts.length > 0 ? (
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Flagged Institutional Option Sweeps & Blocks
          </span>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Strike</th>
                  <th className="py-2.5 px-3">Expiration</th>
                  <th className="py-2.5 px-3">DTE</th>
                  <th className="py-2.5 px-3">Volume</th>
                  <th className="py-2.5 px-3">Open Interest</th>
                  <th className="py-2.5 px-3">Vol / OI</th>
                  <th className="py-2.5 px-3">Premium Est.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {unusualContracts.slice(0, 5).map((c, idx) => (
                  <tr key={idx} className="hover:bg-slate-950/40">
                    <td className="py-2.5 px-3 font-sans font-bold">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${
                          c.type === "CALL"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        }`}
                      >
                        {c.type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-bold text-white">${c.strike}</td>
                    <td className="py-2.5 px-3 text-slate-300">{c.expiration}</td>
                    <td className="py-2.5 px-3 text-slate-400">{c.dte}d</td>
                    <td className="py-2.5 px-3 text-white">{c.volume.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-slate-400">{c.open_interest.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-bold">{c.ratio}x</td>
                    <td className="py-2.5 px-3 text-indigo-300 font-bold">
                      ${Math.round(c.premium).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-center text-xs text-slate-400">
          No institutional sweep orders above $50k premium detected in today&apos;s tape for ${ticker}.
        </div>
      )}
    </div>
  );
}

