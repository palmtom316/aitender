"use client";

import React from "react";

import type { NormSearchResult } from "../../lib/api/norms";

type NormHighlightViewerProps = {
  result: NormSearchResult | null;
  query: string;
};

export function NormHighlightViewer({ result, query }: NormHighlightViewerProps) {
  return (
    <section aria-label="Highlight preview">
      <h2>Highlight preview</h2>
      {result ? (
        <>
          <p>Highlight match: {query}</p>
          <p>
            Preview pages {result.pageStart}-{result.pageEnd}
          </p>
        </>
      ) : (
        <p>Run a search and select a result to preview the hit.</p>
      )}
    </section>
  );
}
