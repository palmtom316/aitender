"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { type ReactNode } from "react";

import styles from "./console-shell.module.css";

type ConsoleShellProps = {
  children: ReactNode;
};

type NavItem = {
  key: string;
  label: string;
  description: string;
  icon: React.ReactNode;
};

const navItems: NavItem[] = [
  {
    key: "library",
    label: "投标资料库",
    description: "规范检索、拆解与分析",
    icon: <LibraryIcon />
  },
  {
    key: "ai-settings",
    label: "ai设置",
    description: "AI模型与API配置",
    icon: <SettingsIcon />
  }
];

export function ConsoleShell({ children }: ConsoleShellProps) {
  const pathname = usePathname();
  const currentProjectLibraryHref = resolveLibraryHref(pathname);

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <Link className={styles.brand} href="/projects">
          <span className={styles.brandMark}>AT</span>
          <span>
            <strong>aitender</strong>
            <small>Bid Console</small>
          </span>
        </Link>

        <div className={styles.sidebarSection}>
          <p className={styles.sectionLabel}>系统模块</p>
          <nav className={styles.navList}>
            {navItems.map((item) => {
              const href =
                item.key === "library" 
                  ? currentProjectLibraryHref 
                  : item.key === "ai-settings"
                  ? resolveSettingsHref(pathname)
                  : "/projects";
              const isActive =
                item.key === "library"
                  ? pathname.includes("/library")
                  : item.key === "ai-settings"
                  ? pathname.includes("/settings/ai")
                  : false;

              return (
                <Link
                  aria-current={isActive ? "page" : undefined}
                  className={`${styles.navItem} ${
                    isActive ? styles.navItemActive : ""
                  }`}
                  href={href}
                  key={item.key}
                >
                  <span className={styles.navIcon}>{item.icon}</span>
                  <span className={styles.navText}>
                    <strong>{item.label}</strong>
                    <small>{item.description}</small>
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className={styles.sidebarSection}>
          <p className={styles.sectionLabel}>当前状态</p>
          <article className={styles.statusCard}>
            <p>本地联调环境</p>
            <strong>前后端与 PostgreSQL 已连接</strong>
            <span>资料上传、检索、项目页可在同一控制台内操作。</span>
          </article>
        </div>
      </aside>

      <div className={styles.main}>
        <header className={styles.topbar}>
          <div>
            <p className={styles.eyebrow}>
              {pathname.includes("/library") ? "投标资料库" : pathname.includes("/settings/ai") ? "系统设置" : "项目操作台"}
            </p>
            <h1 className={styles.title}>
              {pathname.includes("/library")
                ? "投标资料库工作台"
                : pathname.includes("/settings/ai")
                ? "AI模型与API设置"
                : "投标项目控制台"}
            </h1>
          </div>

          <div className={styles.topbarActions}>
            <div className={styles.searchBadge}>
              <SearchIcon />
              <span>项目、文件、条款</span>
            </div>
            <div className={styles.userBadge}>
              <span className={styles.userAvatar}>P</span>
              <span>
                <strong>Palmtom</strong>
                <small>项目管理员</small>
              </span>
            </div>
          </div>
        </header>

        <div className={styles.content}>{children}</div>
      </div>
    </div>
  );
}

function resolveLibraryHref(pathname: string): string {
  const match = pathname.match(/^\/projects\/([^/]+)\/library/);
  if (match) {
    return `/projects/${match[1]}/library`;
  }
  // Fallback to a valid format or projects list if the ID is missing
  const projMatch = pathname.match(/^\/projects\/([^/]+)/);
  if (projMatch) {
    return `/projects/${projMatch[1]}/library`;
  }
  return "/projects";
}

function resolveSettingsHref(pathname: string): string {
  const match = pathname.match(/^\/projects\/([^/]+)/);
  if (match) {
    return `/projects/${match[1]}/settings/ai`;
  }
  return "/projects";
}

function DashboardIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M4 5h7v6H4zM13 5h7v10h-7zM4 13h7v6H4zM13 17h7v2h-7z" />
    </svg>
  );
}

function LibraryIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M4 6a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v9a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3z" />
    </svg>
  );
}

function TimelineIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M6 4h2v16H6zm5 4h2v8h-2zm5-2h2v12h-2z" />
    </svg>
  );
}

function ReviewIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M5 4h11l3 3v13H5zm2 3v11h10V8.2L15.8 7zm2 4h6v2H9zm0 4h4v2H9z" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M10.5 4a6.5 6.5 0 1 1 0 13a6.5 6.5 0 0 1 0-13m0 2a4.5 4.5 0 1 0 0 9a4.5 4.5 0 0 0 0-9m8.4 10.99L21 19.09L19.09 21l-2.11-2.01z" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.06-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.73,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.06,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.43-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.49-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/>
    </svg>
  );
}
