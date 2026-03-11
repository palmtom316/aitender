"use client";

import React from "react";

import type { ProcessingJobView } from "../../lib/api/norms";
import { ErrorState } from "./error-state";

type JobStatusPanelProps = {
  job: ProcessingJobView | null;
};

export function JobStatusPanel({ job }: JobStatusPanelProps) {
  if (!job) {
    return (
      <section aria-label="Processing status">
        <h2>Processing status</h2>
        <p>No processing job has been started yet.</p>
      </section>
    );
  }

  return (
    <section aria-label="Processing status">
      <h2>Processing status</h2>
      <p>Status: {job.status}</p>
      <p>Provider: {job.providerName}</p>
      <p>Recent steps: {job.auditSteps.join(" -> ")}</p>
      {job.errorMessage ? <ErrorState message={job.errorMessage} /> : null}
    </section>
  );
}
