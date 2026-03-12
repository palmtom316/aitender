import React, { type ReactNode } from "react";

import { ConsoleShell } from "../../components/shell/console-shell";

type ProjectsLayoutProps = {
  children: ReactNode;
};

export default function ProjectsLayout({ children }: ProjectsLayoutProps) {
  return <ConsoleShell>{children}</ConsoleShell>;
}
