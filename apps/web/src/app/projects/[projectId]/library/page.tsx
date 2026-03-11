import React from "react";

import { DocumentTable } from "../../../../components/library/document-table";
import { NormSearchPanel } from "../../../../components/library/norm-search-panel";
import { UploadPanel } from "../../../../components/library/upload-panel";
import {
  getNormDocumentBundle,
  listNormDocuments
} from "../../../../lib/api/norms";

type LibraryPageProps = {
  params: Promise<{ projectId: string }>;
};

export default async function LibraryPage({ params }: LibraryPageProps) {
  const { projectId } = await params;
  const documents = await listNormDocuments(projectId);
  const activeDocument = documents[0];
  const bundle = await getNormDocumentBundle(projectId, activeDocument.id);

  return (
    <main>
      <h1>Project library</h1>
      <UploadPanel projectId={projectId} />
      <DocumentTable documents={documents} />
      <NormSearchPanel
        documentId={activeDocument.id}
        initialResults={bundle.results}
        projectId={projectId}
        tree={bundle.tree}
      />
    </main>
  );
}
