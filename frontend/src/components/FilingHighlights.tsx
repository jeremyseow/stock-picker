import React from "react";

interface FilingHighlightsProps {
  text?: string | null;
  emptyText?: string;
}

export function FilingHighlights({
  text,
  emptyText = "No SEC filings or regulatory disclosures recorded.",
}: FilingHighlightsProps) {
  if (!text) {
    return <p className="text-slate-500 text-xs italic">{emptyText}</p>;
  }

  // Normalize splits on both newlines and inline bullet boundaries
  const normalizedText = text.replace(/\)\s*-\s*(\d{4}-\d{2}-\d{2})/g, ")\n- $1");
  const lines = normalizedText.split("\n").filter((l) => l.trim().length > 0);
  const parsed = lines.map((line) => {
    const match = line.match(
      /^-\s*(\d{4}-\d{2}-\d{2})\s*\(([^)]+)\):\s*([^(]+?)(?:\s*\(EDGAR:\s*([^)]+)\))?$/
    );
    if (match) {
      return {
        date: match[1],
        type: match[2],
        title: match[3].trim(),
        url: match[4]?.trim(),
      };
    }
    return null;
  });

  const allMatched = parsed.every((p) => p !== null);

  if (allMatched && parsed.length > 0) {
    return (
      <div className="space-y-2">
        {parsed.map((item, idx) => (
          <div
            key={idx}
            className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/60 text-xs"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-slate-200">{item!.date}</span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                {item!.type}
              </span>
            </div>
            <p className="text-slate-300 text-[11px] leading-snug line-clamp-2">
              {item!.title}
            </p>
            {item!.url && (
              <a
                href={item!.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold mt-1 inline-flex items-center gap-1 transition-colors"
              >
                View EDGAR Filing &rarr;
              </a>
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <p className="text-slate-300 text-xs leading-relaxed whitespace-pre-line break-words">
      {text}
    </p>
  );
}
