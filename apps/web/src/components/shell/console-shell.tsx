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
    key: "dashboard",
    label: "项目总览",
    description: "驾驶舱",
    icon: <DashboardIcon />
  },
  {
    key: "library",
    label: "投标资料库",
    description: "规范检索",
    icon: <LibraryIcon />
  },
  {
    key: "schedule",
    label: "进度协同",
    description: "规划中",
    icon: <TimelineIcon />
  },
  {
    key: "review",
    label: "评审中心",
    description: "规划中",
    icon: <ReviewIcon />
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
                item.key === "library" ? currentProjectLibraryHref : "/projects";
              const isActive =
                item.key === "library"
                  ? pathname.includes("/library")
                  : item.key === "dashboard"
                    ? pathname === "/projects"
                    : false;

              return (
                <Link
                  aria-current={isActive ? "page" : undefined}
                  className={`${styles.navItem} ${
                    isActive ? styles.navItemActive : ""
                  } ${item.key === "dashboard" || item.key === "library" ? "" : styles.navItemMuted}`}
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
              {pathname.includes("/library") ? "投标资料库" : "项目总览"}
            </p>
            <h1 className={styles.title}>
              {pathname.includes("/library")
                ? "投标资料库工作台"
                : "投标项目驾驶舱"}
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
