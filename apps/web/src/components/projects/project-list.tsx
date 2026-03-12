import Link from "next/link";
import React from "react";

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
          <Link href={`/projects/${project.id}/library`}>
            <strong>{project.name}</strong>
          </Link>
          <span>{project.memberRole}</span>
        </li>
      ))}
    </ul>
  );
}
