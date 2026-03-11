type ProjectSummary = {
  id: string;
  name: string;
  memberRole: string;
};

type ProjectListProps = {
  projects: ProjectSummary[];
};

export function ProjectList({ projects }: ProjectListProps) {
  return (
    <ul>
      {projects.map((project) => (
        <li key={project.id}>
          <strong>{project.name}</strong>
          <span>{project.memberRole}</span>
        </li>
      ))}
    </ul>
  );
}
