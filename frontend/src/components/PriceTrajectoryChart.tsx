"use client";

import { useState } from "react";

export interface HistoryPoint {
  id: number;
  ticker: string;
  date: string;
  current_price: number | null;
  target_price: number | null;
  recommendation: "BUY" | "SELL" | "HOLD" | null;
  recommendation_rationale: string;
  community_sentiment: string;
  community_hype: string;
  ground_truth_status: string;
  reconciliation_risk_score: string;
  reconciliation_actionable_insight: string;
  raw_metrics?: Record<string, any> | null;
}

interface PriceTrajectoryChartProps {
  data: HistoryPoint[];
  ticker: string;
}

export default function PriceTrajectoryChart({ data, ticker }: PriceTrajectoryChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
        No price data available for ${ticker}.
      </div>
    );
  }

  // Filter points that have valid numbers
  const validPoints = data.map((d, index) => ({
    ...d,
    index,
    dateLabel: d.date.split("T")[0],
    price: d.current_price ?? 0,
    target: d.target_price ?? d.current_price ?? 0,
  }));

  if (validPoints.length === 1) {
    const pt = validPoints[0];
    return (
      <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-white">Price & Target Snapshot</h3>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
            1 Run Recorded
          </span>
        </div>
        <div className="p-8 text-center bg-slate-950/40 border border-slate-800/40 rounded-xl">
          <div className="flex items-center justify-center gap-8 mb-4">
            <div>
              <span className="text-xs text-slate-400 block mb-1">Market Price</span>
              <span className="text-2xl font-black text-indigo-400">${pt.price.toFixed(2)}</span>
            </div>
            <div className="text-2xl text-slate-600">&rarr;</div>
            <div>
              <span className="text-xs text-slate-400 block mb-1">Target Price</span>
              <span className="text-2xl font-black text-emerald-400">${pt.target.toFixed(2)}</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Only 1 pipeline run is currently recorded for ${ticker} on {pt.dateLabel}. Trajectory lines will connect as future daily runs process this stock.
          </p>
        </div>
      </div>
    );
  }

  // Calculate scales for SVG
  const prices = validPoints.flatMap((p) => [p.price, p.target]).filter((val) => val > 0);
  const minVal = Math.min(...prices) * 0.95;
  const maxVal = Math.max(...prices) * 1.05;
  const range = maxVal - minVal || 1;

  const width = 700;
  const height = 280;
  const paddingX = 50;
  const paddingY = 40;
  const plotWidth = width - paddingX * 2;
  const plotHeight = height - paddingY * 2;

  const getX = (idx: number) => paddingX + (idx / (validPoints.length - 1)) * plotWidth;
  const getY = (val: number) => height - paddingY - ((val - minVal) / range) * plotHeight;

  // Build SVG paths
  const pricePoints = validPoints.map((p, idx) => `${getX(idx)},${getY(p.price)}`).join(" ");
  const targetPoints = validPoints.map((p, idx) => `${getX(idx)},${getY(p.target)}`).join(" ");

  const activePoint = hoverIndex !== null ? validPoints[hoverIndex] : validPoints[validPoints.length - 1];
  const activeUpside =
    activePoint.price > 0
      ? (((activePoint.target - activePoint.price) / activePoint.price) * 100).toFixed(1)
      : null;

  return (
    <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-lg font-black text-white">Price vs. Target Trajectory</h3>
          <p className="text-xs text-slate-400">
            Historical progression of actual market price against Wall Street target price
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-5 text-xs font-semibold">
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-1 bg-indigo-400 rounded-full" />
            <span className="text-slate-300">Market Price</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-1 border-t-2 border-dashed border-emerald-400" />
            <span className="text-slate-300">Target Price</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto max-h-[300px] select-none"
        >
          {/* Horizontal Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = height - paddingY - pct * plotHeight;
            const val = minVal + pct * range;
            return (
              <g key={i}>
                <line
                  x1={paddingX}
                  y1={y}
                  x2={width - paddingX}
                  y2={y}
                  stroke="#334155"
                  strokeDasharray="4 4"
                  strokeOpacity={0.4}
                />
                <text
                  x={paddingX - 10}
                  y={y + 4}
                  textAnchor="end"
                  className="text-[10px] fill-slate-500 font-mono"
                >
                  ${val.toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Area Fill under market price */}
          <polygon
            points={`${getX(0)},${height - paddingY} ${pricePoints} ${getX(
              validPoints.length - 1
            )},${height - paddingY}`}
            fill="url(#priceGradient)"
            opacity="0.3"
          />

          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#818cf8" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#818cf8" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Target Price Line (Dashed) */}
          <polyline
            fill="none"
            stroke="#34d399"
            strokeWidth="2.5"
            strokeDasharray="6 4"
            points={targetPoints}
          />

          {/* Market Price Line (Solid) */}
          <polyline
            fill="none"
            stroke="#818cf8"
            strokeWidth="3"
            points={pricePoints}
          />

          {/* Data Points */}
          {validPoints.map((p, idx) => {
            const x = getX(idx);
            const yPrice = getY(p.price);
            const yTarget = getY(p.target);
            const isHovered = hoverIndex === idx;

            return (
              <g key={idx}>
                {/* Vertical hover indicator line */}
                {isHovered && (
                  <line
                    x1={x}
                    y1={paddingY}
                    x2={x}
                    y2={height - paddingY}
                    stroke="#818cf8"
                    strokeWidth="1.5"
                    strokeDasharray="3 3"
                    opacity="0.8"
                  />
                )}

                {/* Target Price Point */}
                <circle
                  cx={x}
                  cy={yTarget}
                  r={isHovered ? 5.5 : 4}
                  fill="#064e3b"
                  stroke="#34d399"
                  strokeWidth="2"
                  className="transition-all duration-150"
                />

                {/* Market Price Point */}
                <circle
                  cx={x}
                  cy={yPrice}
                  r={isHovered ? 6.5 : 4.5}
                  fill="#1e1b4b"
                  stroke="#818cf8"
                  strokeWidth="2.5"
                  className="transition-all duration-150"
                />

                {/* Invisible hover capture rect */}
                <rect
                  x={x - 20}
                  y={0}
                  width={40}
                  height={height}
                  fill="transparent"
                  className="cursor-pointer"
                  onMouseEnter={() => setHoverIndex(idx)}
                />

                {/* X-axis date labels */}
                <text
                  x={x}
                  y={height - paddingY + 20}
                  textAnchor="middle"
                  className={`text-[10px] font-medium transition-colors ${
                    isHovered ? "fill-indigo-300 font-bold" : "fill-slate-500"
                  }`}
                >
                  {p.dateLabel.slice(5)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Snapshot Details of Active/Hovered Point */}
      <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-300">Run Snapshot:</span>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-semibold">
            {activePoint.dateLabel}
          </span>
          <span className="text-slate-400">
            ({hoverIndex !== null ? "Hovered" : "Latest"})
          </span>
        </div>

        <div className="flex items-center gap-6">
          <div>
            <span className="text-slate-500 mr-1.5">Market Price:</span>
            <span className="font-black text-indigo-300">${activePoint.price.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-slate-500 mr-1.5">Target:</span>
            <span className="font-black text-emerald-300">${activePoint.target.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-slate-500 mr-1.5">Spread:</span>
            <span
              className={`font-black ${
                activeUpside && parseFloat(activeUpside) >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {activeUpside && parseFloat(activeUpside) >= 0 ? "+" : ""}
              {activeUpside}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

