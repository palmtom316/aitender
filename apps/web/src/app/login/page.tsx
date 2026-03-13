import React from "react";
import { redirect } from "next/navigation";

import { LoginForm } from "../../components/auth/login-form";
import { getAccessToken } from "../../lib/auth/server-session";
import styles from "./page.module.css";

export default async function LoginPage() {
  if (await getAccessToken()) {
    redirect("/projects");
  }

  return (
    <main className={styles.page}>
      <section className={styles.brandPanel}>
        <div className={styles.brandTop}>
          <div className={styles.brandBadge}>Aitender Console</div>
          <div className={styles.statusDot}>Local / PostgreSQL</div>
        </div>
        <h1 className={styles.title}>把投标资料、规范检索和处理链路收进一个工作台</h1>
        <p className={styles.description}>
          采用极简、护眼风格与清晰的面板设计，保留资料库场景所需的业务密度和操作闭环。
        </p>

        <div className={styles.signalList}>
          <article className={styles.signalCard}>
            <strong>统一入口</strong>
            <span>登录后直接进入项目控制台与资料库工作面。</span>
          </article>
          <article className={styles.signalCard}>
            <strong>真实操作流</strong>
            <span>上传、文档切换、检索、条款详情与处理状态不再拆散。</span>
          </article>
          <article className={styles.signalCard}>
            <strong>本地联调</strong>
            <span>当前环境已接通前端、API 与 PostgreSQL。</span>
          </article>
        </div>
      </section>

      <section className={styles.formPanel}>
        <div className={styles.formCard}>
          <p className={styles.formEyebrow}>账号登录</p>
          <h2 className={styles.formTitle}>继续进入 aitender</h2>
          <p className={styles.formDescription}>
            使用项目组织账号登录，直接进入当前本地测试环境中的项目控制台。
          </p>
          <LoginForm />
        </div>
      </section>
    </main>
  );
}
