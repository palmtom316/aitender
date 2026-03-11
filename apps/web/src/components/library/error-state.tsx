"use client";

import React from "react";

type ErrorStateProps = {
  message: string;
};

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <section aria-label="Processing error">
      <h2>Processing needs attention</h2>
      <p>{message}</p>
      <p>Retry suggestion: review the source PDF and rerun OCR with another provider.</p>
    </section>
  );
}
