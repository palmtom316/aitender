"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import {
  getProjectAiSettings,
  saveProjectAiSettings
} from "../../../../../lib/api/project-ai-settings";
import styles from "./settings.module.css";

export default function AiSettingsPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = String(params.projectId ?? "");
  const [ocrConfig, setOcrConfig] = useState({ baseUrl: "", apiKey: "", model: "" });
  const [analysisConfig, setAnalysisConfig] = useState({
    baseUrl: "",
    apiKey: "",
    model: ""
  });
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const settings = await getProjectAiSettings(projectId);
        if (cancelled) {
          return;
        }
        setOcrConfig(settings.ocr);
        setAnalysisConfig(settings.analysis);
        setErrorMessage(null);
      } catch {
        if (!cancelled) {
          setErrorMessage("无法加载当前项目的 OCR / AI 配置。");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function handleSave() {
    setIsSaving(true);
    try {
      await saveProjectAiSettings({
        projectId,
        ocr: ocrConfig,
        analysis: analysisConfig
      });
      setErrorMessage(null);
      setStatusMessage("保存成功，后续上传会使用这组 OCR 与 AI 配置。");
    } catch {
      setStatusMessage(null);
      setErrorMessage("保存失败，请检查 API 地址、鉴权信息和后端连接。");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className={styles.container}>
      {isLoading ? <p>加载配置中...</p> : null}
      {statusMessage ? <p>{statusMessage}</p> : null}
      {errorMessage ? <p>{errorMessage}</p> : null}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>OCR 模型配置</h2>
        <p className={styles.sectionDescription}>
          填写可接收 PDF multipart 上传的 OCR 接口地址、密钥和模型名称。
        </p>
        <div className={styles.formGrid}>
          <div className={styles.formGroup}>
            <label className={styles.label}>API Base URL</label>
            <input 
              className={styles.input} 
              type="text" 
              placeholder="https://api.example.com/ocr" 
              value={ocrConfig.baseUrl} 
              onChange={(e) => setOcrConfig({...ocrConfig, baseUrl: e.target.value})}
            />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>API Key</label>
            <input 
              className={styles.input} 
              type="password" 
              placeholder="sk-..." 
              value={ocrConfig.apiKey} 
              onChange={(e) => setOcrConfig({...ocrConfig, apiKey: e.target.value})}
            />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>模型名称 (Model)</label>
            <input 
              className={styles.input} 
              type="text" 
              placeholder="mineru / qwen-vl-plus" 
              value={ocrConfig.model} 
              onChange={(e) => setOcrConfig({...ocrConfig, model: e.target.value})}
            />
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>拆解与分析模型配置</h2>
        <p className={styles.sectionDescription}>
          填写 OpenAI 兼容的 `chat/completions` 根地址或完整接口地址，用于生成摘要、标签和条文说明。
        </p>
        <div className={styles.formGrid}>
          <div className={styles.formGroup}>
            <label className={styles.label}>API Base URL</label>
            <input 
              className={styles.input} 
              type="text" 
              placeholder="https://api.example.com/v1" 
              value={analysisConfig.baseUrl} 
              onChange={(e) => setAnalysisConfig({...analysisConfig, baseUrl: e.target.value})}
            />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>API Key</label>
            <input 
              className={styles.input} 
              type="password" 
              placeholder="sk-..." 
              value={analysisConfig.apiKey} 
              onChange={(e) => setAnalysisConfig({...analysisConfig, apiKey: e.target.value})}
            />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>模型名称 (Model)</label>
            <input 
              className={styles.input} 
              type="text" 
              placeholder="gpt-4 / deepseek-chat" 
              value={analysisConfig.model} 
              onChange={(e) => setAnalysisConfig({...analysisConfig, model: e.target.value})}
            />
          </div>
        </div>
      </section>

      <div className={styles.buttonRow}>
        <button className={styles.button} disabled={isSaving || isLoading} onClick={handleSave}>
          {isSaving ? "保存中..." : "保存配置"}
        </button>
      </div>
    </div>
  );
}
