"use client";

import React from "react";

import type { NormSearchResult } from "../../lib/api/norms";

type NormDetailPanelProps = {
  result: NormSearchResult | null;
  query?: string;
};

function escapeRegExp(text: string) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightText(text: string, query: string) {
  const tokens = query.trim().split(/\s+/).filter(Boolean);
  if (!text || tokens.length === 0) return text;

  const pattern = new RegExp(`(${tokens.map(escapeRegExp).join("|")})`, "gi");
  const parts = text.split(pattern);
  return parts.map((part, idx) => {
    if (tokens.some((token) => token.toLowerCase() === part.toLowerCase())) {
      return (
        <mark key={idx} style={{ background: "rgba(16, 163, 127, 0.25)" }}>
          {part}
        </mark>
      );
    }
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

export function NormDetailPanel({ result, query = "" }: NormDetailPanelProps) {
  return (
    <section aria-label="Clause detail">
      <h2>Clause detail</h2>
      {result ? (
        <>
          <h3>
            {result.label} {result.title}
          </h3>
          <p>{result.summaryText}</p>
          {result.contentPreview ? (
            <p style={{ whiteSpace: "pre-wrap" }}>
              {highlightText(result.contentPreview, query)}
            </p>
          ) : null}
          {result.commentarySummary ? <p>{result.commentarySummary}</p> : null}
          {result.tags.length > 0 ? <p>Tags: {result.tags.join(", ")}</p> : null}
          <p>
            Pages {result.pageStart}-{result.pageEnd}
          </p>
        </>
      ) : (
        <p>Select a clause to inspect details.</p>
      )}
    </section>
  );
}
