import React from "react";
import { redirect } from "next/navigation";

import { LibraryWorkspace } from "../../../../../../components/library/library-workspace";
import {
  getNormDocumentBundle,
  getProcessingJobStatus,
  listNormDocuments
} from "../../../../../../lib/api/norms";
import { requireAccessToken } from "../../../../../../lib/auth/server-session";

type NormDocumentPageProps = {
  params: Promise<{ documentId: string; projectId: string }>;
};

export default async function NormDocumentPage({ params }: NormDocumentPageProps) {
  const { documentId, projectId } = await params;
  const accessToken = await requireAccessToken();
  let documents;
  let bundle;
  try {
    documents = await listNormDocuments(projectId, { accessToken });
    bundle = await getNormDocumentBundle(projectId, documentId, { accessToken });
  } catch (error) {
    if (error instanceof Error && error.message === "Unauthorized") {
      redirect("/login");
    }
    throw error;
  }

  const activeDocument = documents.find((document) => document.id === documentId) ?? null;
  const job =
    activeDocument?.latestJobId != null
      ? await getProcessingJobStatus(activeDocument.latestJobId, { accessToken })
      : null;

  if (!bundle) {
    return (
      <LibraryWorkspace
        documents={documents}
        initialBundle={null}
        initialDocumentId={activeDocument?.id ?? null}
        initialError="Document not found."
        initialJob={job}
        projectId={projectId}
      />
    );
  }

  return (
    <LibraryWorkspace
      documents={documents}
      initialBundle={bundle}
      initialDocumentId={documentId}
      initialJob={job}
      projectId={projectId}
    />
  );
}
