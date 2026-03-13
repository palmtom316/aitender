"use client";

import React from "react";

import type { NormSearchResult } from "../../lib/api/norms";

type NormDetailPanelProps = {
  result: NormSearchResult | null;
};

export function NormDetailPanel({ result }: NormDetailPanelProps) {
  return (
    <section aria-label="Clause detail">
      <h2>Clause detail</h2>
      {result ? (
        <>
          <h3>
            {result.label} {result.title}
          </h3>
          <p>{result.summaryText}</p>
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
