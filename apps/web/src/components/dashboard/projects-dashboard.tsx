import Link from "next/link";
import React from "react";

import type { ProjectSummary } from "../../lib/api/projects";
import styles from "./projects-dashboard.module.css";

type ProjectsDashboardProps = {
  projects: ProjectSummary[];
};

export function ProjectsDashboard({ projects }: ProjectsDashboardProps) {
  const totalProjects = projects.length;
  const writerCount = projects.filter((project) => project.memberRole === "writer").length;
  const managerCount = projects.filter(
    (project) => project.memberRole === "project_manager"
  ).length;

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>控制台概览</p>
          <h2 className={styles.title}>从这里进入每个项目工作面</h2>
          <p className={styles.description}>
            参考 ChatGPT 的主界面节奏，这里把项目入口做成更清晰的主工作区。左侧负责导航，主区只保留当前最重要的项目、模块和操作入口。
          </p>
        </div>

        <div className={styles.heroActions}>
          <div className={styles.heroCard}>
            <span>当前项目</span>
            <strong>项目 {totalProjects}</strong>
          </div>
          <div className={styles.heroCard}>
            <span>核心模块</span>
            <strong>{projects[0] ? "已就绪" : "待创建项目"}</strong>
          </div>
        </div>
      </section>

      <section className={styles.metrics}>
        <article className={styles.metricCard}>
          <p>编写角色</p>
          <strong>{writerCount}</strong>
          <span>负责正文编写与资料组织</span>
        </article>
        <article className={styles.metricCard}>
          <p>项目管理</p>
          <strong>{managerCount}</strong>
          <span>负责节点、审核和资源调度</span>
        </article>
        <article className={styles.metricCard}>
          <p>资料库状态</p>
          <strong>{projects.length > 0 ? "在线" : "未初始化"}</strong>
          <span>前后端与 PostgreSQL 已联通</span>
        </article>
      </section>

      <section className={styles.workspaceGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.panelEyebrow}>项目入口</p>
              <h3 className={styles.panelTitle}>投标项目清单</h3>
            </div>
            <span className={styles.panelMeta}>选择项目进入资料库</span>
          </div>

          <div className={styles.projectList}>
            {projects.map((project) => (
              <article className={styles.projectCard} key={project.id}>
                <div className={styles.projectHead}>
                  <div>
                    <Link
                      className={styles.projectName}
                      href={`/projects/${project.id}/library`}
                    >
                      {project.name} {roleLabel(project.memberRole)}
                    </Link>
                    <p className={styles.projectRole}>
                      当前身份：{roleDescription(project.memberRole)}
                    </p>
                  </div>
                  <span className={styles.projectBadge}>已连接</span>
                </div>

                <div className={styles.projectMetaGrid}>
                  <span>规范资料库</span>
                  <span>OCR/索引链路</span>
                  <span>条款检索</span>
                </div>

                <div className={styles.projectActions}>
                  <Link
                    aria-label="打开资料库"
                    className={styles.primaryAction}
                    href={`/projects/${project.id}/library`}
                  >
                    打开资料库
                  </Link>
                  <span className={styles.secondaryAction}>
                    项目 ID: {project.id}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.panelEyebrow}>系统模块</p>
              <h3 className={styles.panelTitle}>当前控制台已接通的能力</h3>
            </div>
          </div>

          <div className={styles.moduleList}>
            <div className={styles.moduleRow}>
              <strong>项目总览</strong>
              <span>查看项目入口与角色分布</span>
            </div>
            <div className={styles.moduleRow}>
              <strong>投标资料库</strong>
              <span>上传规范、查看处理状态、执行条款检索</span>
            </div>
            <div className={styles.moduleRow}>
              <strong>后续模块</strong>
              <span>进度协同、评审中心已在左侧预留位置</span>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}

function roleLabel(role: string): string {
  if (role === "writer") {
    return "编写人";
  }

  if (role === "project_manager") {
    return "项目经理";
  }

  return role;
}

function roleDescription(role: string): string {
  if (role === "writer") {
    return "资料整理、章节编写、条款引用";
  }

  if (role === "project_manager") {
    return "项目推进、任务分配、资料审核";
  }

  return role;
}
