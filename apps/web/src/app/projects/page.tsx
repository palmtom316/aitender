import React from "react";
import { redirect } from "next/navigation";

import { ProjectsDashboard } from "../../components/dashboard/projects-dashboard";
import { requireAccessToken } from "../../lib/auth/server-session";
import { listProjects } from "../../lib/api/projects";

export default async function ProjectsPage() {
  const accessToken = await requireAccessToken();
  let projects;
  try {
    projects = await listProjects({ accessToken });
  } catch (error) {
    if (error instanceof Error && error.message === "Unauthorized") {
      redirect("/login");
    }
    throw error;
  }

  return (
    <ProjectsDashboard projects={projects} />
  );
}
