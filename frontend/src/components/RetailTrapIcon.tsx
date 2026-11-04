import React from "react";

export function RetailTrapIcon({ className = "w-4 h-4 inline-block text-rose-400" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M4 19h16" />
      <path d="M5 19C5 12 8 8 12 8c4 0 7 4 7 11" />
      <path d="M7 16l2-3 2 3" />
      <path d="M13 16l2-3 2 3" />
      <circle cx="12" cy="15" r="1.5" fill="currentColor" />
    </svg>
  );
}

