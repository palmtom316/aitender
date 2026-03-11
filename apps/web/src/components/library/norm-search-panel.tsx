"use client";

import React, { useState } from "react";

import type { NormSearchResult, NormTreeNode } from "../../lib/api/norms";
import { searchNorms } from "../../lib/api/norms";
import { NormDetailPanel } from "./norm-detail-panel";
import { NormHighlightViewer } from "./norm-highlight-viewer";
import { NormResultList } from "./norm-result-list";
import { NormTree } from "./norm-tree";

type NormSearchPanelProps = {
  projectId: string;
  documentId: string;
  tree: NormTreeNode[];
  initialResults: NormSearchResult[];
};

export function NormSearchPanel({
  projectId,
  documentId,
  tree,
  initialResults
}: NormSearchPanelProps) {
  const [query, setQuery] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [results, setResults] = useState<NormSearchResult[]>(initialResults);
  const [selectedResult, setSelectedResult] = useState<NormSearchResult | null>(null);

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const nextResults = await searchNorms({ projectId, documentId, query });
      setErrorMessage(null);
      setResults(nextResults.items);
      setSelectedResult(nextResults.items[0] ?? null);
    } catch {
      setErrorMessage("Failed to load search results.");
    }
  }

  return (
    <section>
      <h2>Norm workspace</h2>
      <form onSubmit={handleSearch}>
        <label htmlFor="norm-search-input">Search norms</label>
        <input
          id="norm-search-input"
          onChange={(event) => setQuery(event.target.value)}
          value={query}
        />
        <button type="submit">Search</button>
      </form>
      {errorMessage ? <p>{errorMessage}</p> : null}
      <div>
        <NormResultList
          onSelect={setSelectedResult}
          results={results}
          selectedLabel={selectedResult?.label ?? null}
        />
        <NormTree nodes={tree} selectedLabel={selectedResult?.label ?? null} />
        <NormDetailPanel result={selectedResult} />
        <NormHighlightViewer query={query} result={selectedResult} />
      </div>
    </section>
  );
}
