import React from "react";

import { NormSearchPanel } from "../../../../../../components/library/norm-search-panel";
import { getNormDocumentBundle } from "../../../../../../lib/api/norms";

type NormDocumentPageProps = {
  params: Promise<{ documentId: string; projectId: string }>;
};

export default async function NormDocumentPage({ params }: NormDocumentPageProps) {
  const { documentId, projectId } = await params;
  const bundle = await getNormDocumentBundle(projectId, documentId);
  if (!bundle) {
    return (
      <main>
        <h1>Document not found.</h1>
        <p>Project: {projectId}</p>
      </main>
    );
  }

  return (
    <main>
      <h1>{bundle.document.fileName}</h1>
      <p>Status: {bundle.document.status}</p>
      <p>Indexed clauses: {bundle.results.length}</p>
      <NormSearchPanel
        documentId={documentId}
        initialResults={bundle.results}
        projectId={projectId}
        tree={bundle.tree}
      />
    </main>
  );
}
