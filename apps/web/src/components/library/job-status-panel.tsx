"use client";

import React from "react";

import type { ProcessingJobView } from "../../lib/api/norms";
import { ErrorState } from "./error-state";

type JobStatusPanelProps = {
  job: ProcessingJobView;
};

export function JobStatusPanel({ job }: JobStatusPanelProps) {
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
