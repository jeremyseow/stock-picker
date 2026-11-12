"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import PortfolioEquityChart, { SnapshotItem } from "@/components/PortfolioEquityChart";
import ActivePositionsTable, { OpenPositionItem } from "@/components/ActivePositionsTable";
import TradeJournalTable, { ClosedTradeItem } from "@/components/TradeJournalTable";
import { API_BASE } from "@/lib/api";

interface PortfolioSummary {
  account_id: number;
  name: string;
  initial_balance: number;
  cash_balance: number;
  invested_capital: number;
  total_equity: number;
  total_return_dollar: number;
  total_return_pct: number;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  open_positions_count: number;
  max_positions: number;
  allocation_per_trade: number;
  closed_trades_count: number;
  win_rate_pct: number;
  excess_alpha_pct: number;
}

export default function PortfolioPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [positions, setPositions] = useState<OpenPositionItem[]>([]);
  const [snapshots, setSnapshots] = useState<SnapshotItem[]>([]);
  const [journal, setJournal] = useState<ClosedTradeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [bannerMessage, setBannerMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [showManagePanel, setShowManagePanel] = useState(false);
  const [slotsInput, setSlotsInput] = useState<number>(10);
  const [allocInput, setAllocInput] = useState<number>(10000);
  const [depositInput, setDepositInput] = useState<string>("25000");

  const fetchPortfolioData = async () => {
    try {
      const [sumRes, posRes, snapRes, jourRes] = await Promise.all([
        fetch(`${API_BASE}/api/portfolio/summary`),
        fetch(`${API_BASE}/api/portfolio/positions`),
        fetch(`${API_BASE}/api/portfolio/snapshots`),
        fetch(`${API_BASE}/api/portfolio/journal?limit=200`),
      ]);

      if (sumRes.ok) {
        const sumData: PortfolioSummary = await sumRes.json();
        setSummary(sumData);
        setSlotsInput(sumData.max_positions);
        setAllocInput(sumData.allocation_per_trade ?? 10000);
      }
      if (posRes.ok) setPositions(await posRes.json());
      if (snapRes.ok) setSnapshots(await snapRes.json());
      if (jourRes.ok) setJournal(await jourRes.json());
    } catch (err) {
      console.error("Failed to load portfolio data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolioData();
  }, []);

  const handleManualClose = async (positionId: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/positions/${positionId}/close`, {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to close position");
      }
      setBannerMessage({ type: "success", text: `Position closed successfully at $${data.position.exit_price}` });
      await fetchPortfolioData();
    } catch (err: any) {
      setBannerMessage({ type: "error", text: err.message || "Error closing position" });
    }
  };

  const handleTriggerMarketOpen = async () => {
    setActionLoading("open");
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/trigger-open`, { method: "POST" });
      const data = await res.json();
      setBannerMessage({
        type: "success",
        text: `Market Open Execution: ${data.executed_count || 0} orders filled, ${data.skipped?.length || 0} skipped.`,
      });
      await fetchPortfolioData();
    } catch (err: any) {
      setBannerMessage({ type: "error", text: "Failed to trigger market open orders" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleTriggerMarketClose = async () => {
    setActionLoading("close");
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/trigger-close`, { method: "POST" });
      const data = await res.json();
      setBannerMessage({
        type: "success",
        text: `Market Close Evaluation: ${data.closed_count || 0} positions exited, ${data.updated_count || 0} marked to market.`,
      });
      await fetchPortfolioData();
    } catch (err: any) {
      setBannerMessage({ type: "error", text: "Failed to evaluate market close exits" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleTriggerBackfill = async () => {
    if (!window.confirm("Replay historical paper trading over all past synthesis reports? This will reset the paper ledger.")) {
      return;
    }
    setActionLoading("backfill");
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/backfill`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reset: true }),
      });
      const data = await res.json();
      setBannerMessage({
        type: "success",
        text: `Historical Bootstrap Complete: Processed ${data.dates_processed || 0} dates, ${data.orders_executed || 0} orders filled, ${data.positions_closed || 0} closed trades.`,
      });
      await fetchPortfolioData();
    } catch (err: any) {
      setBannerMessage({ type: "error", text: "Failed to execute historical backfill" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading("settings");
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/settings`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          max_positions: slotsInput,
          allocation_per_trade: allocInput,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update settings");
      setBannerMessage({
        type: "success",
        text: `Updated fund capacity to ${data.summary.max_positions} slots at $${data.summary.allocation_per_trade.toLocaleString()} per trade.`,
      });
      await fetchPortfolioData();
    } catch (err: any) {
      setBannerMessage({ type: "error", text: err.message || "Failed to update portfolio settings" });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDepositCash = async (amountToDeposit?: number) => {
    const amount = amountToDeposit ?? Number(depositInput);
    if (!amount || amount <= 0) {
      setBannerMessage({ type: "error", text: "Enter a positive cash top-up amount." });
      return;
    }
    setActionLoading("deposit");
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/deposit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to top up cash");
      setBannerMessage({
        type: "success",
        text: `Topped up +$${data.deposited_amount.toLocaleString()} cash. Available cash: $${data.summary.cash_balance.toLocaleString()}.`,
      });
      setDepositInput("");
      await fetchPortfolioData();
    } catch (err: any) {
      setBannerMessage({ type: "error", text: err.message || "Failed to top up cash" });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 flex flex-col gap-8">
        {/* Header with Title and Control Buttons */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5">
              <span className="text-2xl">💼</span>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-indigo-200">
                Paper Trading Portfolio & Trade Journal
              </h1>
            </div>
            <p className="text-sm text-slate-400 max-w-3xl leading-relaxed">
              Automated $100,000 institutional fund simulation. Fills high-conviction Synthesis signals (<em>The Rocket</em>, <em>Silent Accumulation</em>) at US Market Open with strict $10k fixed-slot sizing, calibrated archetype stop-losses (-5% to -8%), profit targets (+12% to +20%), and S&P 500 alpha measurement.
            </p>
          </div>

          {/* Quick Action Controls */}
          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <button
              onClick={handleTriggerMarketOpen}
              disabled={actionLoading !== null}
              className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50 flex items-center gap-2"
            >
              <span>🔔</span>
              <span>{actionLoading === "open" ? "Executing..." : "Run Market Open"}</span>
            </button>
            <button
              onClick={handleTriggerMarketClose}
              disabled={actionLoading !== null}
              className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              <span>🏁</span>
              <span>{actionLoading === "close" ? "Evaluating..." : "Run Market Close"}</span>
            </button>
            <button
              onClick={handleTriggerBackfill}
              disabled={actionLoading !== null}
              className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-purple-900/40 hover:bg-purple-900/60 text-purple-200 border border-purple-700/50 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              <span>⚡</span>
              <span>{actionLoading === "backfill" ? "Bootstrapping..." : "Bootstrap History"}</span>
            </button>
            <button
              onClick={() => setShowManagePanel((v) => !v)}
              className={`px-3.5 py-2 text-xs font-semibold rounded-xl border transition-all flex items-center gap-2 ${
                showManagePanel
                  ? "bg-emerald-600/20 border-emerald-500/40 text-emerald-300"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700"
              }`}
            >
              <span>⚙️</span>
              <span>Slots & Cash</span>
            </button>
          </div>
        </div>

        {/* Collapsible Fund Controls: Slots, Allocation & Cash Top-Up */}
        {showManagePanel && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 bg-slate-900/70 border border-slate-800 rounded-2xl p-5">
            <form onSubmit={handleSaveSettings} className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-100">Slot Capacity & Trade Sizing</h2>
                <span className="text-[11px] text-slate-400">Applies to new Market Open fills</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <label className="flex flex-col gap-1 text-xs text-slate-400">
                  <span>Max Slots (1–50)</span>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => setSlotsInput((s) => Math.max(1, s - 1))}
                      className="px-2.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold"
                    >
                      −
                    </button>
                    <input
                      type="number"
                      min={1}
                      max={50}
                      value={slotsInput}
                      onChange={(e) => setSlotsInput(Math.max(1, Math.min(50, Number(e.target.value) || 1)))}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 focus:border-indigo-500 focus:outline-none text-slate-100 font-mono text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    />
                    <button
                      type="button"
                      onClick={() => setSlotsInput((s) => Math.min(50, s + 1))}
                      className="px-2.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold"
                    >
                      +
                    </button>
                  </div>
                </label>
                <label className="flex flex-col gap-1 text-xs text-slate-400">
                  <span>Allocation / Trade ($)</span>
                  <input
                    type="number"
                    min={500}
                    step={500}
                    value={allocInput}
                    onChange={(e) => setAllocInput(Number(e.target.value) || 500)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 focus:border-indigo-500 focus:outline-none text-slate-100 font-mono [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                </label>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={actionLoading !== null}
                  className="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 transition-all"
                >
                  {actionLoading === "settings" ? "Saving..." : "Save Slots & Sizing"}
                </button>
              </div>
            </form>

            <div className="flex flex-col gap-3 lg:border-l lg:border-slate-800 lg:pl-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-100">Top Up Cash</h2>
                <span className="text-[11px] text-slate-400">Adjusts cost basis to keep Alpha % honest</span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {[10000, 25000, 50000].map((preset) => {
                  const isSelected = Number(depositInput) === preset;
                  return (
                    <button
                      key={preset}
                      type="button"
                      disabled={actionLoading !== null}
                      onClick={() => setDepositInput(String(preset))}
                      className={`px-3 py-2 text-xs font-semibold rounded-lg border disabled:opacity-50 transition-all ${
                        isSelected
                          ? "bg-emerald-500/25 border-emerald-400 text-emerald-200"
                          : "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                      }`}
                    >
                      +${(preset / 1000).toFixed(0)}k
                    </button>
                  );
                })}
                <div className="flex items-center gap-2 flex-1 min-w-[180px]">
                  <input
                    type="number"
                    min={100}
                    step={1000}
                    value={depositInput}
                    onChange={(e) => setDepositInput(e.target.value)}
                    placeholder="Custom $"
                    className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-700 focus:border-emerald-500 focus:outline-none text-slate-100 font-mono [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                  <button
                    type="button"
                    disabled={actionLoading !== null}
                    onClick={() => handleDepositCash()}
                    className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 shrink-0 transition-all"
                  >
                    {actionLoading === "deposit" ? "Adding..." : "Top Up"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Feedback Banner */}
        {bannerMessage && (
          <div
            className={`p-4 rounded-xl text-xs sm:text-sm font-medium flex items-center justify-between border ${
              bannerMessage.type === "success"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-rose-500/10 border-rose-500/30 text-rose-300"
            }`}
          >
            <span>{bannerMessage.text}</span>
            <button
              onClick={() => setBannerMessage(null)}
              className="text-slate-400 hover:text-slate-200 ml-4 font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {/* KPI Metric Cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {/* Total Equity Card */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
              <span className="text-xs font-medium text-slate-400">Total Fund Equity</span>
              <div className="mt-2">
                <span className="text-xl sm:text-2xl font-black text-slate-100">
                  ${summary.total_equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
                <div className="flex items-center gap-1.5 mt-1 text-xs">
                  <span
                    className={`font-bold ${
                      summary.total_return_dollar >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {summary.total_return_dollar >= 0 ? "+" : ""}${summary.total_return_dollar.toFixed(2)}
                  </span>
                  <span className="text-slate-500">
                    ({summary.total_return_pct >= 0 ? "+" : ""}{summary.total_return_pct.toFixed(2)}%)
                  </span>
                </div>
              </div>
            </div>

            {/* Cash Balance Card */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
              <span className="text-xs font-medium text-slate-400">Available Cash</span>
              <div className="mt-2">
                <span className="text-xl sm:text-2xl font-black text-slate-100">
                  ${summary.cash_balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
                <div className="text-xs text-slate-400 mt-1">
                  Invested: <span className="font-semibold text-slate-200">${summary.invested_capital.toLocaleString()}</span>
                </div>
              </div>
            </div>

            {/* Alpha vs SPY Card */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
              <span className="text-xs font-medium text-slate-400">Alpha vs S&P 500</span>
              <div className="mt-2">
                <span
                  className={`text-xl sm:text-2xl font-black ${
                    summary.excess_alpha_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {summary.excess_alpha_pct >= 0 ? "+" : ""}{summary.excess_alpha_pct.toFixed(2)}%
                </span>
                <div className="text-xs text-slate-400 mt-1">
                  Excess benchmark return
                </div>
              </div>
            </div>

            {/* Win Rate Card */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
              <span className="text-xs font-medium text-slate-400">Win Rate</span>
              <div className="mt-2">
                <span className="text-xl sm:text-2xl font-black text-indigo-400">
                  {summary.win_rate_pct.toFixed(1)}%
                </span>
                <div className="text-xs text-slate-400 mt-1">
                  Realized: <span className={summary.total_realized_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}>
                    ${summary.total_realized_pnl.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Holdings Capacity Card */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between col-span-2 md:col-span-1">
              <span className="text-xs font-medium text-slate-400">Capacity Slots</span>
              <div className="mt-2">
                <span className="text-xl sm:text-2xl font-black text-slate-100">
                  {summary.open_positions_count} <span className="text-slate-500 text-sm font-normal">/ {summary.max_positions}</span>
                </span>
                <div className="text-xs text-slate-400 mt-1">
                  ${(summary.allocation_per_trade ?? 10000).toLocaleString()}/trade &bull; {summary.closed_trades_count} closed
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Section 1: Equity Curve vs SPY Benchmark */}
        <PortfolioEquityChart snapshots={snapshots} />

        {/* Section 2: Active Holdings Table */}
        <ActivePositionsTable
          positions={positions}
          maxPositions={summary?.max_positions ?? 10}
          onClosePosition={handleManualClose}
        />

        {/* Section 3: Closed Trade Journal */}
        <TradeJournalTable trades={journal} />
      </main>
    </div>
  );
}

