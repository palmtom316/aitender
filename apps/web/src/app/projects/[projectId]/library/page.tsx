import React from "react";

import { DocumentTable } from "../../../../components/library/document-table";
import { JobStatusPanel } from "../../../../components/library/job-status-panel";
import { NormSearchPanel } from "../../../../components/library/norm-search-panel";
import { UploadPanel } from "../../../../components/library/upload-panel";
import {
  getNormDocumentBundle,
  getProcessingJobStatus,
  listNormDocuments
} from "../../../../lib/api/norms";

type LibraryPageProps = {
  params: Promise<{ projectId: string }>;
};

export default async function LibraryPage({ params }: LibraryPageProps) {
  const { projectId } = await params;
  const documents = await listNormDocuments(projectId);

  if (documents.length === 0) {
    return (
      <main>
        <h1>Project library</h1>
        <UploadPanel projectId={projectId} />
        <DocumentTable documents={documents} />
        <p>No norm documents uploaded yet.</p>
      </main>
    );
  }

  const activeDocument = documents[0];
  const bundle = await getNormDocumentBundle(projectId, activeDocument.id);
  const job = await getProcessingJobStatus(activeDocument.id);
  if (!bundle) {
    return (
      <main>
        <h1>Project library</h1>
        <UploadPanel projectId={projectId} />
        <DocumentTable documents={documents} />
        <p>Document not found.</p>
      </main>
    );
  }

  return (
    <main>
      <h1>Project library</h1>
      <UploadPanel projectId={projectId} />
      <DocumentTable documents={documents} />
      <JobStatusPanel job={job} />
      <NormSearchPanel
        documentId={activeDocument.id}
        initialResults={bundle.results}
        projectId={projectId}
        tree={bundle.tree}
      />
    </main>
  );
}
