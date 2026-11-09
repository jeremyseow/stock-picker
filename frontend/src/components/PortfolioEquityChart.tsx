"use client";

import { useState } from "react";

export interface SnapshotItem {
  id: number;
  snapshot_date: string;
  cash_balance: number;
  invested_capital: number;
  total_equity: number;
  portfolio_return_pct: number;
  spy_price: number | null;
  spy_return_pct: number | null;
  excess_alpha_pct: number | null;
  open_positions_count: number;
}

interface PortfolioEquityChartProps {
  snapshots: SnapshotItem[];
}

export default function PortfolioEquityChart({ snapshots }: PortfolioEquityChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!snapshots || snapshots.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center min-h-[300px] text-center">
        <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center text-2xl mb-3">
          📊
        </div>
        <h3 className="text-base font-semibold text-slate-200">No Portfolio Snapshots Yet</h3>
        <p className="text-xs text-slate-400 max-w-sm mt-1">
          Historical equity snapshots will automatically appear once market open fills or historical bootstrapping runs.
        </p>
      </div>
    );
  }

  // Calculate scales
  const width = 800;
  const height = 300;
  const padLeft = 50;
  const padRight = 30;
  const padTop = 30;
  const padBottom = 40;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const portReturns = snapshots.map((s) => s.portfolio_return_pct || 0);
  const spyReturns = snapshots.map((s) => s.spy_return_pct || 0);

  const allVals = [...portReturns, ...spyReturns, 0];
  const minVal = Math.min(...allVals) - 1.0;
  const maxVal = Math.max(...allVals) + 1.0;
  const range = maxVal - minVal || 1.0;

  const getX = (idx: number) => {
    if (snapshots.length <= 1) return padLeft + chartW / 2;
    return padLeft + (idx / (snapshots.length - 1)) * chartW;
  };

  const getY = (val: number) => {
    return padTop + chartH - ((val - minVal) / range) * chartH;
  };

  // Build SVG path strings
  const portPoints = snapshots.map((s, idx) => `${getX(idx)},${getY(s.portfolio_return_pct || 0)}`).join(" ");
  const spyPoints = snapshots.map((s, idx) => `${getX(idx)},${getY(s.spy_return_pct || 0)}`).join(" ");

  // Gradient area path for portfolio
  const firstX = getX(0);
  const lastX = getX(snapshots.length - 1);
  const zeroY = getY(0);
  const areaPath = `M ${firstX},${zeroY} L ${portPoints.split(" ").join(" L ")} L ${lastX},${zeroY} Z`;

  const hoveredItem = hoverIndex !== null ? snapshots[hoverIndex] : snapshots[snapshots.length - 1];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
      {/* Header with KPI and Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>Equity Growth vs S&P 500 Benchmark</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-medium">
              Daily Mark-to-Market
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Normalized cumulative percentage return vs SPY ETF baseline
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-medium">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-indigo-400 shadow-sm shadow-indigo-500/50" />
            <span className="text-slate-200">Portfolio</span>
            <span className="font-bold text-indigo-300">
              {hoveredItem ? `${(hoveredItem.portfolio_return_pct || 0) >= 0 ? "+" : ""}${hoveredItem.portfolio_return_pct.toFixed(2)}%` : ""}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 rounded-sm bg-amber-400/80" />
            <span className="text-slate-400">SPY (S&P 500)</span>
            <span className="font-semibold text-amber-300">
              {hoveredItem ? `${(hoveredItem.spy_return_pct || 0) >= 0 ? "+" : ""}${(hoveredItem.spy_return_pct || 0).toFixed(2)}%` : ""}
            </span>
          </div>
          {hoveredItem && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold">
              <span>Alpha:</span>
              <span>
                {(hoveredItem.excess_alpha_pct || 0) >= 0 ? "+" : ""}
                {(hoveredItem.excess_alpha_pct || 0).toFixed(2)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* SVG Chart Container */}
      <div className="relative w-full aspect-[8/3] max-h-[320px]">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-full overflow-visible select-none"
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            <linearGradient id="portGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Zero baseline */}
          <line
            x1={padLeft}
            y1={zeroY}
            x2={width - padRight}
            y2={zeroY}
            stroke="#475569"
            strokeDasharray="4 4"
            strokeWidth="1"
          />

          {/* Y Axis Gridlines */}
          {[minVal, (minVal + maxVal) / 2, maxVal].map((val, idx) => {
            const y = getY(val);
            return (
              <g key={idx}>
                <line
                  x1={padLeft}
                  y1={y}
                  x2={width - padRight}
                  y2={y}
                  stroke="#334155"
                  strokeOpacity="0.4"
                  strokeWidth="1"
                />
                <text
                  x={padLeft - 8}
                  y={y + 4}
                  fill="#94a3b8"
                  fontSize="10"
                  textAnchor="end"
                  fontFamily="sans-serif"
                >
                  {val >= 0 ? `+${val.toFixed(1)}%` : `${val.toFixed(1)}%`}
                </text>
              </g>
            );
          })}

          {/* Area fill under portfolio curve */}
          <path d={areaPath} fill="url(#portGradient)" />

          {/* SPY Benchmark Line */}
          <polyline
            fill="none"
            stroke="#fbbf24"
            strokeWidth="2"
            strokeDasharray="5 3"
            strokeOpacity="0.85"
            points={spyPoints}
          />

          {/* Portfolio Equity Line */}
          <polyline
            fill="none"
            stroke="#818cf8"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={portPoints}
          />

          {/* Interactive vertical hover indicator */}
          {hoverIndex !== null && (
            <line
              x1={getX(hoverIndex)}
              y1={padTop}
              x2={getX(hoverIndex)}
              y2={height - padBottom}
              stroke="#cbd5e1"
              strokeDasharray="2 2"
              strokeWidth="1.5"
            />
          )}

          {/* Data point dots & hover touch targets */}
          {snapshots.map((s, idx) => {
            const cx = getX(idx);
            const cyPort = getY(s.portfolio_return_pct || 0);
            const isHovered = hoverIndex === idx;

            return (
              <g
                key={s.id || idx}
                className="cursor-pointer"
                onMouseEnter={() => setHoverIndex(idx)}
              >
                {/* Invisible wide hit area */}
                <rect
                  x={cx - (chartW / (snapshots.length * 2 || 1))}
                  y={padTop}
                  width={chartW / (snapshots.length || 1)}
                  height={chartH}
                  fill="transparent"
                />

                {/* Visible dot on portfolio curve */}
                <circle
                  cx={cx}
                  cy={cyPort}
                  r={isHovered ? 6 : 3.5}
                  className="transition-all"
                  fill={isHovered ? "#38bdf8" : "#818cf8"}
                  stroke="#0f172a"
                  strokeWidth="2"
                />
              </g>
            );
          })}

          {/* X Axis Date labels */}
          {snapshots.map((s, idx) => {
            // Display only a subset of labels to prevent crowding
            const step = Math.max(1, Math.floor(snapshots.length / 5));
            if (idx % step !== 0 && idx !== snapshots.length - 1) return null;

            const cx = getX(idx);
            const dateLabel = s.snapshot_date ? s.snapshot_date.substring(5, 10) : "";
            return (
              <text
                key={idx}
                x={cx}
                y={height - padBottom + 18}
                fill="#94a3b8"
                fontSize="10"
                textAnchor="middle"
                fontFamily="sans-serif"
              >
                {dateLabel}
              </text>
            );
          })}
        </svg>
      </div>

      {/* Tooltip Card below chart for touch/mobile or active hover */}
      {hoveredItem && (
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Snapshot Date:</span>
            <span className="font-semibold text-slate-200">
              {hoveredItem.snapshot_date ? hoveredItem.snapshot_date.substring(0, 10) : "N/A"}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div>
              <span className="text-slate-400">Equity: </span>
              <span className="font-bold text-slate-100">
                ${hoveredItem.total_equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div>
              <span className="text-slate-400">Cash: </span>
              <span className="text-slate-300">
                ${hoveredItem.cash_balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div>
              <span className="text-slate-400">Invested: </span>
              <span className="text-slate-300">
                ${hoveredItem.invested_capital.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div>
              <span className="text-slate-400">Active Positions: </span>
              <span className="font-semibold text-indigo-400">
                {hoveredItem.open_positions_count}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

