import { DocumentTable } from "../../../../components/library/document-table";
import { UploadPanel } from "../../../../components/library/upload-panel";

const demoDocuments = [
  {
    id: "doc-1",
    fileName: "grid-standard.pdf",
    status: "uploaded",
    libraryType: "norm_library",
  },
];

type LibraryPageProps = {
  params: Promise<{ projectId: string }>;
};

export default async function LibraryPage({ params }: LibraryPageProps) {
  const { projectId } = await params;

  return (
    <main>
      <h1>Project library</h1>
      <UploadPanel projectId={projectId} />
      <DocumentTable documents={demoDocuments} />
    </main>
  );
}
