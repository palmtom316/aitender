"use client";

import React, { useActionState } from "react";

import { loginAction } from "../../app/login/actions";
import styles from "./login-form.module.css";

export function LoginForm() {
  const [state, formAction, isPending] = useActionState(
    loginAction,
    { errorMessage: null }
  );

  return (
    <form action={formAction} className={styles.form}>
      <label className={styles.field} htmlFor="email">
        <span>邮箱</span>
        <input
          autoComplete="email"
          id="email"
          name="email"
          placeholder="pm@aitender.local"
          type="email"
        />
      </label>

      <label className={styles.field} htmlFor="password">
        <span>密码</span>
        <input
          autoComplete="current-password"
          id="password"
          name="password"
          placeholder="输入密码"
          type="password"
        />
      </label>

      <button className={styles.submitButton} disabled={isPending} type="submit">
        {isPending ? "正在登录..." : "继续"}
      </button>
      <div className={styles.helperRow}>
        <span>本地测试环境走真实 API 登录链路。</span>
        <span>服务端会写入会话 Cookie。</span>
      </div>
      {state.errorMessage ? <p className={styles.error}>{state.errorMessage}</p> : null}
    </form>
  );
}
