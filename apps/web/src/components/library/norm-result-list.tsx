"use client";

import React from "react";

import type { NormSearchResult } from "../../lib/api/norms";

type NormResultListProps = {
  results: NormSearchResult[];
  selectedLabel: string | null;
  onSelect: (result: NormSearchResult) => void;
};

export function NormResultList({
  results,
  selectedLabel,
  onSelect
}: NormResultListProps) {
  return (
    <section aria-label="Search results">
      <h2>Search results</h2>
      <ul>
        {results.map((result) => (
          <li key={result.label}>
            <button
              aria-pressed={selectedLabel === result.label}
              onClick={() => onSelect(result)}
              type="button"
            >
              {result.label} {result.title}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
