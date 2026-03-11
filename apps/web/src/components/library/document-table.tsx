type LibraryDocument = {
  id: string;
  fileName: string;
  status: string;
  libraryType: string;
};

type DocumentTableProps = {
  documents: LibraryDocument[];
};

export function DocumentTable({ documents }: DocumentTableProps) {
  return (
    <table>
      <thead>
        <tr>
          <th>File</th>
          <th>Status</th>
          <th>Library</th>
        </tr>
      </thead>
      <tbody>
        {documents.map((document) => (
          <tr key={document.id}>
            <td>{document.fileName}</td>
            <td>{document.status}</td>
            <td>{document.libraryType}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
