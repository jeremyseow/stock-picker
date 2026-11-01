"use client";

import React from "react";

export interface ContrarianPlaybookProps {
  ticker: string;
  archetype?: string;
  timingEdgeScore?: number;
  retailAwarenessLevel?: string;
  retailSentiment?: string;
  retailMentions?: number;
  retailRank?: number | null;
  smartMoneyConviction?: number;
  smartMoneyTier?: string;
  smartMoneyFlow?: string;
  diagnosis?: string | null;
  recommendedAction?: string;
}

export default function ContrarianPlaybook({
  ticker,
  archetype = "Market Noise",
  timingEdgeScore = 50,
  retailAwarenessLevel = "Zero Awareness (Stealth)",
  retailSentiment = "Neutral",
  retailMentions = 0,
  retailRank,
  smartMoneyConviction = 0,
  smartMoneyTier = "Neutral",
  smartMoneyFlow = "Neutral",
  diagnosis,
  recommendedAction = "WATCH",
}: ContrarianPlaybookProps) {
  // Normalize archetype
  const normalizedArchetype = archetype || "Market Noise";

  // Tactical playbook rules based on Archetype
  const getPlaybookRules = (arch: string) => {
    switch (arch) {
      case "Silent Accumulation":
        return {
          title: "Front-Run the Hype Cycle",
          stance: "Aggressive Stealth Accumulation",
          badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
          accentColor: "emerald",
          entryTiming: "Accumulate in phased tranches on pullbacks to VWAP/moving averages while retail volume remains dormant.",
          horizon: "3 to 6 Months (Institutional filing horizon & regulatory catalysts)",
          exitSignal: "Retail sentiment escalates into top 3 Reddit rankings or social engagement surges >500% without new insider buying.",
          pitfall: "Selling prematurely during quiet consolidation periods before the public narrative unlocks.",
        };
      case "The Rocket":
        return {
          title: "Momentum Ride with Institutional Underpinning",
          stance: "High Conviction Trend Follow",
          badgeColor: "bg-purple-500/10 text-purple-400 border-purple-500/30",
          accentColor: "purple",
          entryTiming: "Immediate market or limit buy on momentum breakout, anchored by insider transaction floor.",
          horizon: "2 to 8 Weeks (Rapid liquidity expansion window)",
          exitSignal: "Sudden cessation of insider accumulation or Form 4 insider distributions dumping into retail bid.",
          pitfall: "Ignoring parabolic exhaustion candles when social sentiment turns overwhelmingly euphoric.",
        };
      case "The Retail Trap":
        return {
          title: "Capital Preservation & Contrarian Fade",
          stance: "Strict Risk-Off / AVOID LONG",
          badgeColor: "bg-rose-500/10 text-rose-400 border-rose-500/30",
          accentColor: "rose",
          entryTiming: "DO NOT BUY. If already holding, trim aggressively on strength into retail frenzy liquidity.",
          horizon: "1 to 3 Weeks (Distribution liquidation phase)",
          exitSignal: "Complete washout of retail mentions (>70% drop) and emergence of fresh smart money clusters at discount.",
          pitfall: "Averaging down on social media hype while institutional participants and insiders are actively exiting.",
        };
      default:
        return {
          title: "Observation & Signal Validation",
          stance: "Neutral / Selective Watchlist",
          badgeColor: "bg-slate-500/10 text-slate-400 border-slate-500/30",
          accentColor: "slate",
          entryTiming: "Maintain on radar until either a verified Smart Money cluster ($100k+) or organic retail consensus forms.",
          horizon: "Tactical / Flexible",
          exitSignal: "Transition into an active conviction quadrant.",
          pitfall: "Committing capital without a confirmed catalyst edge.",
        };
    }
  };

  const playbook = getPlaybookRules(normalizedArchetype);

  // Archetype lifecycle progression vector
  const lifecyclePhases = [
    { name: "Silent Accumulation", label: "1. Stealth Accumulation", icon: "🤫", desc: "Insiders build position; zero retail buzz" },
    { name: "The Rocket", label: "2. The Rocket", icon: "🚀", desc: "Dual alignment: crowd + smart money breakout" },
    { name: "The Retail Trap", label: "3. The Retail Trap", icon: "🪤", desc: "Retail euphoria while smart money exits" },
    { name: "Market Noise", label: "4. Market Noise", icon: "📢", desc: "Consolidation or lack of directional catalyst" },
  ];

  return (
    <div className="space-y-6">
      {/* 1. DIVERGENCE SCORECARD / QUADRANT HEATMAP */}
      <div className="bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 backdrop-blur-md relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-black uppercase tracking-wider text-indigo-400">
                Alpha Diagnostic Engine
              </span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold border ${playbook.badgeColor}`}>
                {normalizedArchetype}
              </span>
            </div>
            <h3 className="text-xl font-black text-white tracking-tight">
              Cross-Engine Divergence Heatmap
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Quantifying the spread between retail social consensus and institutional capital commitment.
            </p>
          </div>

          <div className="flex items-center gap-4 bg-slate-950/80 border border-slate-800/80 px-4 py-2.5 rounded-xl">
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">
                Recommended Action
              </span>
              <span className="text-sm font-black text-indigo-300">{recommendedAction}</span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">
                Timing Edge
              </span>
              <span className="text-sm font-black text-emerald-400">{timingEdgeScore.toFixed(0)}/100</span>
            </div>
          </div>
        </div>

        {/* Side-by-Side Divergence Matrix */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          {/* Retail Engine Signal */}
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                <span>💬</span> Retail Sentiment Engine
              </span>
              <span className="text-[11px] font-semibold text-slate-400">
                {retailRank ? `Rank #${retailRank}` : "Unranked"}
              </span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Awareness Level:</span>
                <span className="font-bold text-slate-200">{retailAwarenessLevel}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Mentions & Volume:</span>
                <span className="font-bold text-slate-200">{retailMentions} posts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Consensus Sentiment:</span>
                <span className="font-bold text-amber-300">{retailSentiment}</span>
              </div>
            </div>
          </div>

          {/* Smart Money Engine Signal */}
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-purple-400 flex items-center gap-1.5">
                <span>🏛️</span> Smart Money Catalyst Engine
              </span>
              <span className="text-[11px] font-semibold text-slate-400">
                Conviction: {smartMoneyConviction.toFixed(1)}
              </span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Capital Flow:</span>
                <span className="font-bold text-slate-200">{smartMoneyFlow}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Conviction Tier:</span>
                <span className="font-bold text-purple-300">{smartMoneyTier}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Insiders & Politicians:</span>
                <span className="font-bold text-emerald-400">Cluster Verified</span>
              </div>
            </div>
          </div>
        </div>

        {/* Timing Edge Meter */}
        <div className="mt-5 pt-5 border-t border-slate-800/60">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="font-bold text-slate-400 flex items-center gap-1.5">
              <span>⏱️</span> Timing Alpha Score (Asymmetric Opportunity Edge)
            </span>
            <span className="font-black text-emerald-400">{timingEdgeScore.toFixed(0)}%</span>
          </div>
          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-amber-500 via-indigo-500 to-emerald-400 transition-all duration-700"
              style={{ width: `${Math.min(100, Math.max(5, timingEdgeScore))}%` }}
            />
          </div>
          {diagnosis && (
            <p className="mt-3 text-xs text-slate-300 bg-slate-950/70 p-3 rounded-xl border border-slate-800/80 leading-relaxed">
              <span className="font-bold text-indigo-400">Diagnostic Verdict:</span> {diagnosis}
            </p>
          )}
        </div>
      </div>

      {/* 2. TACTICAL CONTRARIAN EXECUTION PLAYBOOK */}
      <div className="bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 backdrop-blur-md">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-7 h-7 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center text-sm font-bold">
            ⚔️
          </span>
          <div>
            <h4 className="text-base font-bold text-white">Contrarian Execution Playbook</h4>
            <span className="text-[11px] text-slate-400">{playbook.title} &bull; Strategy: {playbook.stance}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <span className="text-[10px] font-black text-emerald-400 uppercase tracking-wider block mb-1">
              🎯 Tactical Entry Strategy
            </span>
            <p className="text-xs text-slate-300 leading-relaxed font-medium">
              {playbook.entryTiming}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <span className="text-[10px] font-black text-indigo-400 uppercase tracking-wider block mb-1">
              ⏳ Target Holding Horizon
            </span>
            <p className="text-xs text-slate-300 leading-relaxed font-medium">
              {playbook.horizon}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <span className="text-[10px] font-black text-rose-400 uppercase tracking-wider block mb-1">
              🚨 Take-Profit / Exit Triggers
            </span>
            <p className="text-xs text-slate-300 leading-relaxed font-medium">
              {playbook.exitSignal}
            </p>
          </div>
        </div>

        <div className="mt-4 p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200/90 flex items-center gap-2">
          <span className="text-sm">⚠️</span>
          <span><strong className="text-amber-300">Key Psychological Pitfall:</strong> {playbook.pitfall}</span>
        </div>
      </div>

      {/* 3. ARCHETYPE LIFECYCLE PROGRESSION VECTOR */}
      <div className="bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 backdrop-blur-md">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <span>🔄</span> Alpha Lifecycle Progression Vector
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {lifecyclePhases.map((phase) => {
            const isActive = phase.name === normalizedArchetype;
            return (
              <div
                key={phase.name}
                className={`p-3.5 rounded-xl border transition-all ${
                  isActive
                    ? "bg-indigo-600/15 border-indigo-500/60 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/30"
                    : "bg-slate-950/40 border-slate-800/60 opacity-60"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-base">{phase.icon}</span>
                  {isActive && (
                    <span className="text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500 text-white">
                      Current Phase
                    </span>
                  )}
                </div>
                <div className={`text-xs font-bold mt-1 ${isActive ? "text-white" : "text-slate-400"}`}>
                  {phase.label}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                  {phase.desc}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

