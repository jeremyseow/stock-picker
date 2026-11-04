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

function getOptionsFlowAnalysis({
  ticker,
  whaleScore,
  unusualOiMultiplier,
  putCallRatio,
  netBullishPremium,
  sentimentBias,
  topStrikeSummary,
}: {
  ticker: string;
  whaleScore: number;
  unusualOiMultiplier: number;
  putCallRatio: number;
  netBullishPremium: number;
  sentimentBias: string;
  topStrikeSummary?: string;
}) {
  // 1. Primary Signal Driver for Card 4
  let driverSummary = "";
  if (unusualOiMultiplier >= 2.5 && putCallRatio <= 0.6) {
    const callRatio = (1 / Math.max(putCallRatio, 0.05)).toFixed(1);
    driverSummary = `Fresh Positioning (${unusualOiMultiplier.toFixed(1)}x OI) + ${callRatio}:1 Call Skew`;
  } else if (unusualOiMultiplier >= 2.5) {
    driverSummary = `Heavy Volume Buildup (${unusualOiMultiplier.toFixed(1)}x Open Interest)`;
  } else if (putCallRatio <= 0.6) {
    driverSummary = `Directional Call Flow (${putCallRatio.toFixed(2)} P/C Ratio)`;
  } else if (putCallRatio >= 1.2) {
    driverSummary = `Defensive Put Dominance (${putCallRatio.toFixed(2)} P/C Ratio)`;
  } else {
    driverSummary = "Standard Options Liquidity & Baseline Flow";
  }

  // 2. Market Mechanics Observation: What does this mean?
  let oiMeaning = "";
  if (unusualOiMultiplier >= 3.0) {
    oiMeaning = `Single-day trading volume surged to ${unusualOiMultiplier.toFixed(1)}x existing open interest. In options microstructure, when traded volume dramatically exceeds total open interest, it signifies institutional whales aggressively opening brand-new contracts today rather than rolling or closing existing positions.`;
  } else if (unusualOiMultiplier >= 2.0) {
    oiMeaning = `Volume outpaced open interest by ${unusualOiMultiplier.toFixed(1)}x, indicating active new capital allocation above routine market-making turnover.`;
  } else {
    oiMeaning = `Option volume remained proportional to open interest (${unusualOiMultiplier.toFixed(1)}x), reflecting normal market liquidity without abnormal expansion.`;
  }

  let pcMeaning = "";
  if (putCallRatio <= 0.4) {
    const callMult = (1 / Math.max(putCallRatio, 0.05)).toFixed(1);
    pcMeaning = `With a Put/Call ratio of ${putCallRatio.toFixed(2)}, bullish call volume outpaces protective puts by nearly ${callMult} to 1, showing unambiguous directional upside conviction with minimal downside hedging.`;
  } else if (putCallRatio <= 0.65) {
    pcMeaning = `With a Put/Call ratio of ${putCallRatio.toFixed(2)}, order flow leans decisively bullish toward upside calls.`;
  } else if (putCallRatio >= 1.3) {
    pcMeaning = `With a Put/Call ratio of ${putCallRatio.toFixed(2)}, put volume heavily exceeds calls, signaling institutional downside hedging or bearish anticipation.`;
  } else {
    pcMeaning = `A Put/Call ratio of ${putCallRatio.toFixed(2)} reflects relatively balanced two-sided trading.`;
  }

  const observationMeaning = `${oiMeaning} ${pcMeaning}`;

  // 3. Scoring & Label Rationale: Why this score and label?
  const oiPts = Math.min(unusualOiMultiplier * 7.0, 35.0);
  const skewPts = Math.max(0.0, (1.0 - Math.min(putCallRatio, 1.0)) * 25.0);
  const premPts = Math.min(netBullishPremium / 25000.0, 40.0);
  const premK = Math.round(netBullishPremium / 1000);

  const scoringRationale = `The Whale Conviction Score of ${whaleScore.toFixed(0)}/100 combines: (1) Volume/OI Spike factor contributing ${oiPts.toFixed(1)}/35 max points, (2) Bullish Call Skew contributing ${skewPts.toFixed(1)}/25 points, and (3) Net Bullish Premium (${premK > 0 ? `$${premK}k` : "low cash outlay"}) contributing ${premPts.toFixed(1)}/40 points. Crossing the 40+ threshold triggers the "${sentimentBias}" classification.`;

  return { driverSummary, observationMeaning, scoringRationale };
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

  const { driverSummary, observationMeaning, scoringRationale } = getOptionsFlowAnalysis({
    ticker,
    whaleScore,
    unusualOiMultiplier,
    putCallRatio,
    netBullishPremium,
    sentimentBias,
    topStrikeSummary,
  });

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
        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60 flex flex-col justify-between">
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">
              Put / Call Ratio
            </span>
            <span className="text-lg font-extrabold text-white mt-1 block">
              {putCallRatio.toFixed(2)}
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1">
            {putCallRatio <= 0.6 ? "Bullish call skew" : putCallRatio >= 1.2 ? "Bearish put skew" : "Balanced flow"}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60 flex flex-col justify-between">
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">
              Peak Volume / OI
            </span>
            <span className="text-lg font-extrabold text-emerald-400 mt-1 block">
              {unusualOiMultiplier.toFixed(1)}x
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1">
            {unusualOiMultiplier >= 2.5 ? "Unusual accumulation" : "Standard activity"}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60 flex flex-col justify-between">
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">
              Net Bullish Premium
            </span>
            <span className="text-lg font-extrabold text-indigo-300 mt-1 block">
              ${(netBullishPremium / 1000).toFixed(0)}k
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1">OTM call sweeps</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60 flex flex-col justify-between">
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-bold block">
              Primary Signal Driver
            </span>
            <span
              className="text-xs font-semibold text-cyan-300 mt-1 block leading-snug break-words"
              title={driverSummary}
            >
              {driverSummary}
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Conviction catalyst</span>
        </div>
      </div>

      {/* Institutional Flow Interpretation & Score Rationale Panel */}
      <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-3">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-xs font-bold text-cyan-300 uppercase tracking-wider">
            Whale Flow Interpretation & Score Rationale
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300 leading-relaxed">
          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800/60 space-y-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>🔍</span> 1. What the Market Observation Means
            </span>
            <p className="text-slate-300 leading-relaxed">{observationMeaning}</p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800/60 space-y-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>⚖️</span> 2. Why This Score & Label Were Given
            </span>
            <p className="text-slate-300 leading-relaxed">{scoringRationale}</p>
          </div>
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
                    <td className="py-2.5 px-3 text-white font-bold">${c.strike}</td>
                    <td className="py-2.5 px-3 text-slate-400">{c.expiration}</td>
                    <td className="py-2.5 px-3 text-slate-400">{c.dte}d</td>
                    <td className="py-2.5 px-3 text-slate-200">{c.volume.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-slate-400">{c.open_interest.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-bold">{c.ratio.toFixed(1)}x</td>
                    <td className="py-2.5 px-3 text-slate-200">
                      {c.premium > 0 ? `$${(c.premium / 1000).toFixed(0)}k` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/40 text-xs text-slate-400">
          No individual contracts exceeded the 2.5x Volume/OI threshold today. Flow is based on aggregate tape volume.
        </div>
      )}
    </div>
  );
}
