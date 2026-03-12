"use client";

import React, { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { uploadNormDocument } from "../../lib/api/norms";

type UploadPanelProps = {
  projectId: string;
};

export function UploadPanel({ projectId }: UploadPanelProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const file = formData.get("file");

    if (!(file instanceof File) || file.size === 0) {
      setErrorMessage("Please choose a PDF file.");
      setStatusMessage(null);
      return;
    }

    try {
      await uploadNormDocument({ projectId, file });
      form.reset();
      setErrorMessage(null);
      setStatusMessage("Upload queued. Refreshing library data.");
      startTransition(() => {
        router.refresh();
      });
    } catch {
      setErrorMessage("Failed to upload the selected PDF.");
      setStatusMessage(null);
    }
  }

  return (
    <section>
      <h2>Upload norm PDF</h2>
      <p>Project: {projectId}</p>
      <form onSubmit={handleSubmit}>
        <input accept="application/pdf" name="file" type="file" />
        <button disabled={isPending} type="submit">
          {isPending ? "Uploading..." : "Upload"}
        </button>
      </form>
      {statusMessage ? <p>{statusMessage}</p> : null}
      {errorMessage ? <p>{errorMessage}</p> : null}
    </section>
  );
}
