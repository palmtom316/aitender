import React from "react";

type UploadPanelProps = {
  projectId: string;
};

export function UploadPanel({ projectId }: UploadPanelProps) {
  return (
    <section>
      <h2>Upload norm PDF</h2>
      <p>Project: {projectId}</p>
      <form>
        <input accept="application/pdf" name="file" type="file" />
        <button type="submit">Upload</button>
      </form>
    </section>
  );
}
