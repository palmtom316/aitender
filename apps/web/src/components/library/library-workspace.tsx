"use client";

import React, { useDeferredValue, useState } from "react";
import { useRouter } from "next/navigation";

import type {
  NormDocument,
  NormDocumentBundle,
  NormSearchResult,
  ProcessingJobView
} from "../../lib/api/norms";
import {
  getNormDocumentBundle,
  getProcessingJobStatus,
  searchNorms,
  uploadNormDocument
} from "../../lib/api/norms";
import { getApiBaseUrl } from "../../lib/api/base-url";
import styles from "./library-workspace.module.css";
import { NormDetailPanel } from "./norm-detail-panel";
import { NormPdfViewer } from "./norm-pdf-viewer";

type LibraryWorkspaceProps = {
  projectId: string;
  documents: NormDocument[];
  initialDocumentId: string | null;
  initialBundle: NormDocumentBundle | null;
  initialJob: ProcessingJobView | null;
  initialError?: string | null;
};

export function LibraryWorkspace({
  projectId,
  documents,
  initialDocumentId,
  initialBundle,
  initialJob,
  initialError = null
}: LibraryWorkspaceProps) {
  const router = useRouter();
  const [allDocuments, setAllDocuments] = useState(documents);
  const [activeDocumentId, setActiveDocumentId] = useState(initialDocumentId);
  const [bundle, setBundle] = useState(initialBundle);
  const [job, setJob] = useState(initialJob);
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [results, setResults] = useState(initialBundle?.results ?? []);
  const [selectedResult, setSelectedResult] = useState<NormSearchResult | null>(
    initialBundle?.results[0] ?? null
  );
  const [workspaceError, setWorkspaceError] = useState<string | null>(initialError);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isSwitchingDocument, setIsSwitchingDocument] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const activeDocument =
    allDocuments.find((document) => document.id === activeDocumentId) ?? null;
  const indexedCount = allDocuments.filter(
    (document) => document.status === "indexed"
  ).length;
  const runningCount = allDocuments.filter(
    (document) => document.status === "processing"
  ).length;
  const pdfUrl =
    activeDocument && getApiBaseUrl()
      ? `${getApiBaseUrl()}/projects/${projectId}/norm-library/documents/${activeDocument.id}/file`
      : "";

  async function loadDocument(document: NormDocument) {
    setActiveDocumentId(document.id);
    setWorkspaceError(null);
    setSearchError(null);
    setIsSwitchingDocument(true);

    try {
      const nextBundle = await getNormDocumentBundle(projectId, document.id);
      if (!nextBundle) {
        setBundle(null);
        setResults([]);
        setSelectedResult(null);
        setJob(null);
        setWorkspaceError("Document not found.");
        return;
      }

      const nextJob = document.latestJobId
        ? await getProcessingJobStatus(document.latestJobId)
        : null;
      setBundle(nextBundle);
      setJob(nextJob);
      setResults(nextBundle.results);
      setSelectedResult(nextBundle.results[0] ?? null);
    } catch {
      setWorkspaceError("无法加载所选文档的资料库内容。");
    } finally {
      setIsSwitchingDocument(false);
    }
  }

  function handleDocumentSelect(document: NormDocument) {
    if (document.id === activeDocumentId) {
      return;
    }

    void loadDocument(document);
  }

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!activeDocumentId) {
      return;
    }

    if (!query.trim()) {
      setSearchError(null);
      setResults(bundle?.results ?? []);
      setSelectedResult(bundle?.results[0] ?? null);
      return;
    }

    try {
      const response = await searchNorms({
        projectId,
        documentId: activeDocumentId,
        query
      });
      setSearchError(null);
      setResults(response.items);
      setSelectedResult(response.items[0] ?? null);
    } catch {
      setSearchError("Failed to load search results.");
    }
  }

  function handleClearSearch() {
    setQuery("");
    setSearchError(null);
    setResults(bundle?.results ?? []);
    setSelectedResult(bundle?.results[0] ?? null);
  }

  async function handleTreeSelect(label: string) {
    const match = results.find(
      (result) => result.label === label || result.pathLabels.includes(label)
    );
    if (match) {
      setSelectedResult(match);
      return;
    }

    if (!activeDocumentId) {
      return;
    }

    try {
      const response = await searchNorms({
        projectId,
        documentId: activeDocumentId,
        pathPrefix: label
      });
      setResults(response.items);
      setSelectedResult(response.items[0] ?? null);
      setSearchError(null);
    } catch {
      setSearchError("Failed to load tree selection.");
    }
  }

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const file = formData.get("file");

    if (!(file instanceof File) || file.size === 0) {
      setUploadError("请选择一个 PDF 文件后再上传。");
      setUploadMessage(null);
      return;
    }

    setIsUploading(true);

    try {
      const uploadedDocument = await uploadNormDocument({
        projectId,
        file
      });
      const nextDocuments = [
        uploadedDocument,
        ...allDocuments.filter((document) => document.id !== uploadedDocument.id)
      ];
      setAllDocuments(nextDocuments);
      setUploadError(null);
      setUploadMessage("上传已提交，工作区正在刷新最新文档状态。");
      form.reset();
      await loadDocument(uploadedDocument);
      router.refresh();
    } catch {
      setUploadError("Failed to upload the selected PDF.");
      setUploadMessage(null);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className={styles.page}>
      <section className={styles.summary}>
        <div>
          <p className={styles.eyebrow}>项目工作区</p>
          <h2 className={styles.title}>投标资料库工作台</h2>
          <p className={styles.description}>
            参考 ChatGPT 的主界面方式，这里把文档切换、检索和详情集中在一个主画布里，减少来回跳页。
          </p>
        </div>

        <div className={styles.summaryStats}>
          <article className={styles.summaryCard}>
            <span>资料库文档</span>
            <strong>{allDocuments.length}</strong>
          </article>
          <article className={styles.summaryCard}>
            <span>已建索引</span>
            <strong>{indexedCount}</strong>
          </article>
          <article className={styles.summaryCard}>
            <span>处理中</span>
            <strong>{runningCount}</strong>
          </article>
        </div>
      </section>

      <section className={styles.managementGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.panelEyebrow}>上传区</p>
              <h3 className={styles.panelTitle}>导入投标规范资料</h3>
            </div>
          </div>

          <form className={styles.uploadForm} onSubmit={handleUpload}>
            <label className={styles.uploadField} htmlFor="library-upload">
              <span>选择 PDF 规范文件</span>
              <input
                accept="application/pdf"
                id="library-upload"
                name="file"
                type="file"
              />
            </label>
            <button className={styles.primaryButton} disabled={isUploading} type="submit">
              {isUploading ? "Uploading..." : "Upload"}
            </button>
          </form>

          <p className={styles.panelHint}>
            上传后会触发 OCR/结构化处理，并在右侧状态卡中显示最新步骤。
          </p>
          {uploadMessage ? <p className={styles.successNote}>{uploadMessage}</p> : null}
          {uploadError ? <p className={styles.errorNote}>{uploadError}</p> : null}
        </article>

        <article className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.panelEyebrow}>文档列表</p>
              <h3 className={styles.panelTitle}>投标资料库文件</h3>
            </div>
            <span className={styles.panelMeta}>
              {isSwitchingDocument ? "切换中..." : "点击切换当前工作文档"}
            </span>
          </div>

          {allDocuments.length > 0 ? (
            <div className={styles.documentList}>
              {allDocuments.map((document) => {
                const isActive = document.id === activeDocumentId;

                return (
                  <button
                    className={`${styles.documentCard} ${
                      isActive ? styles.documentCardActive : ""
                    }`}
                    key={document.id}
                    onClick={() => handleDocumentSelect(document)}
                    type="button"
                  >
                    <div className={styles.documentHead}>
                      <strong>{document.fileName}</strong>
                      <span className={styles.documentStatus}>{document.status}</span>
                    </div>
                    <div className={styles.documentMeta}>
                      <span>{document.libraryType}</span>
                      <span>{document.latestJobId ?? "未开始处理"}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className={styles.emptyState}>
              <strong>No norm documents uploaded yet.</strong>
              <span>先上传 PDF，资料库工作区会在这里展示文档和条款内容。</span>
            </div>
          )}
        </article>

        <article className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.panelEyebrow}>处理状态</p>
              <h3 className={styles.panelTitle}>OCR 与索引流水</h3>
            </div>
          </div>

          {job ? (
            <div className={styles.jobCard}>
              <p>Status: {job.status}</p>
              <p>Provider: {job.providerName}</p>
              <ul className={styles.auditList}>
                {job.auditSteps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ul>
              {job.errorMessage ? <p className={styles.errorNote}>{job.errorMessage}</p> : null}
            </div>
          ) : (
            <div className={styles.emptyState}>
              <strong>尚未生成处理任务</strong>
              <span>上传文档后，这里会展示 OCR 与结构化处理步骤。</span>
            </div>
          )}
        </article>
      </section>

      <section className={styles.workspaceGrid}>
        <article className={`${styles.panel} ${styles.explorerPanel}`}>
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.panelEyebrow}>检索工作区</p>
              <h3 className={styles.panelTitle}>
                {activeDocument ? activeDocument.fileName : "等待选择文档"}
              </h3>
            </div>
            <span className={styles.panelMeta}>
              {bundle ? `${bundle.results.length} 条初始条款` : "未加载文档内容"}
            </span>
          </div>

          <form className={styles.searchForm} onSubmit={handleSearch}>
            <label className={styles.searchLabel} htmlFor="norm-search-input">
              Search norms
            </label>
              <div className={styles.searchControls}>
                <input
                  id="norm-search-input"
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="搜索文件内容、条款号或摘要"
                  value={query}
                />
              <button className={styles.primaryButton} type="submit">
                Search
              </button>
              <button
                className={styles.secondaryButton}
                onClick={handleClearSearch}
                type="button"
              >
                清空
              </button>
            </div>
          </form>
          {searchError ? <p className={styles.errorNote}>{searchError}</p> : null}
          {workspaceError ? <p className={styles.errorNote}>{workspaceError}</p> : null}

          <div className={styles.explorerGrid}>
            <section aria-label="Search results" className={styles.subPanel}>
              <div className={styles.subPanelHeader}>
                <h4>Search results</h4>
                <span>{results.length} 条</span>
              </div>
              <div className={styles.resultList}>
                {results.map((result) => (
                  <button
                    aria-pressed={selectedResult?.label === result.label}
                    className={`${styles.resultButton} ${
                      selectedResult?.label === result.label
                        ? styles.resultButtonActive
                        : ""
                    }`}
                    key={result.label}
                    onClick={() => setSelectedResult(result)}
                    type="button"
                  >
                    <strong>
                      {result.label} {result.title}
                    </strong>
                    <span>{result.summaryText}</span>
                  </button>
                ))}
              </div>
            </section>

            <section aria-label="Norm tree" className={styles.subPanel}>
              <div className={styles.subPanelHeader}>
                <h4>Structure</h4>
                <span>目录树</span>
              </div>
              <ul className={styles.tree} role="tree">
                {(bundle?.tree ?? []).map((node) => (
                  <TreeNode
                    key={node.label}
                    node={node}
                    onSelect={(label) => {
                      void handleTreeSelect(label);
                    }}
                    selectedLabel={selectedResult?.label ?? null}
                  />
                ))}
              </ul>
            </section>
          </div>
        </article>

        <div className={styles.detailColumn}>
          <article className={styles.panel}>
            <NormDetailPanel result={selectedResult} />
          </article>
          <article aria-label="PDF 原文对比" className={styles.panel} style={{ padding: 0, overflow: "hidden", display: "flex", flexDirection: "column", height: "100%", minHeight: "600px" }}>
            <NormPdfViewer
              fileUrl={pdfUrl}
              result={selectedResult}
              query={deferredQuery}
            />
          </article>
        </div>
      </section>
    </div>
  );
}

type TreeNodeProps = {
  node: NormDocumentBundle["tree"][number];
  selectedLabel: string | null;
  onSelect: (label: string) => void;
};

function TreeNode({ node, selectedLabel, onSelect }: TreeNodeProps) {
  return (
    <li
      aria-current={selectedLabel === node.label ? "true" : undefined}
      aria-label={node.label}
      className={styles.treeItem}
      role="treeitem"
    >
      <button
        className={styles.treeButton}
        onClick={() => onSelect(node.label)}
        type="button"
      >
        <span data-testid={selectedLabel === node.label ? "active-tree-node" : undefined}>
          {node.label}
        </span>
        <small>{node.title}</small>
      </button>
      {node.children && node.children.length > 0 ? (
        <ul className={styles.treeGroup} role="group">
          {node.children.map((child) => (
            <TreeNode
              key={child.label}
              node={child}
              onSelect={onSelect}
              selectedLabel={selectedLabel}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}
