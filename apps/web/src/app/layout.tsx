import type { Metadata } from "next";
import React, { type ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "aitender Console",
  description: "投标资料、规范条款与处理流程的统一作业台"
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
