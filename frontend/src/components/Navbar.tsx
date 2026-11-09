"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { label: "Retail Momentum", href: "/" },
    { label: "Smart Money & Gov", href: "/smart-money" },
    { label: "Synthesis Matrix", href: "/synthesis" },
    { label: "Historical Reports", href: "/stats" },
    { label: "Ticker Analytics", href: "/analytics" },
    { label: "Model Calibration", href: "/calibration" },
    { label: "Paper Portfolio", href: "/portfolio" },
  ];

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-8">
        <Link href="/" className="flex items-center gap-2.5 group shrink-0 mr-4">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            📈
          </span>
          <span className="font-extrabold text-lg sm:text-xl bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 via-slate-100 to-indigo-200">
            Antigravity <span className="text-indigo-400">StockPicker</span>
          </span>
        </Link>
        <nav className="flex items-center gap-1 sm:gap-2 lg:gap-3 shrink-0">
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname?.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`text-xs sm:text-sm font-semibold transition-all whitespace-nowrap px-3 py-1.5 rounded-lg ${
                  isActive
                    ? "text-indigo-300 bg-indigo-500/15 font-bold shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

