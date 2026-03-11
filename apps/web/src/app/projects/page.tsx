import { ProjectList } from "../../components/projects/project-list";

const demoProjects = [
  {
    id: "project-alpha",
    name: "Alpha Substation Bid",
    memberRole: "writer",
  },
  {
    id: "project-beta",
    name: "Beta Transmission Line Bid",
    memberRole: "project_manager",
  },
];

export default function ProjectsPage() {
  return (
    <main>
      <h1>Your projects</h1>
      <p>Projects visible to the signed-in user appear here.</p>
      <ProjectList projects={demoProjects} />
    </main>
  );
}
