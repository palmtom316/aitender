import React from "react";
import { redirect } from "next/navigation";

import { LibraryWorkspace } from "../../../../components/library/library-workspace";
import { requireAccessToken } from "../../../../lib/auth/server-session";
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
  const accessToken = await requireAccessToken();
  let documents;
  try {
    documents = await listNormDocuments(projectId, { accessToken });
  } catch (error) {
    if (error instanceof Error && error.message === "Unauthorized") {
      redirect("/login");
    }
    throw error;
  }

  if (documents.length === 0) {
    return (
      <LibraryWorkspace
        documents={documents}
        initialBundle={null}
        initialDocumentId={null}
        initialJob={null}
        projectId={projectId}
      />
    );
  }

  const activeDocument = documents[0];
  const bundle = await getNormDocumentBundle(projectId, activeDocument.id, {
    accessToken
  });
  const job = activeDocument.latestJobId
    ? await getProcessingJobStatus(activeDocument.latestJobId, { accessToken })
    : null;
  if (!bundle) {
    return (
      <LibraryWorkspace
        documents={documents}
        initialBundle={null}
        initialDocumentId={activeDocument.id}
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
      initialDocumentId={activeDocument.id}
      initialJob={job}
      projectId={projectId}
    />
  );
}
