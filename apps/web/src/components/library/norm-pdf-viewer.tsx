"use client";

import React, { useState, useMemo } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import { readAccessTokenFromDocumentCookie } from "../../lib/auth/session";
import type { NormSearchResult } from "../../lib/api/norms";

// Set worker URL to load the pdf.js worker from CDN for Next.js to avoid Webpack issues
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

type NormPdfViewerProps = {
  fileUrl: string;
  result: NormSearchResult | null;
  query: string;
};

export function NormPdfViewer({ fileUrl, result, query }: NormPdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const accessToken = readAccessTokenFromDocumentCookie();
  const fileSource = useMemo(() => {
    if (!fileUrl) {
      return "";
    }

    return {
      url: fileUrl,
      httpHeaders: accessToken
        ? { Authorization: `Bearer ${accessToken}` }
        : undefined
    };
  }, [accessToken, fileUrl]);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  // Update page when result changes
  React.useEffect(() => {
    if (result) {
      setPageNumber(result.pageStart);
    }
  }, [result]);

  const customTextRenderer = useMemo(() => {
    return (textItem: any) => {
      const text = textItem.str;
      if (!result?.summaryText) return text;
      
      // Simple highlighting: if the text snippet is in our result summary or vice versa
      const highlightMode =
        text.includes(result.summaryText) ||
        result.summaryText.includes(text) ||
        (query && text.toLowerCase().includes(query.toLowerCase()));
      
      if (highlightMode) {
        return `<mark style="background-color: rgba(16, 163, 127, 0.3); padding: 0 2px; border-radius: 2px;">${text}</mark>`;
      }
      return text;
    };
  }, [result, query]);

  if (!fileUrl) {
    return (
      <div style={{ padding: 24, textAlign: "center", color: "var(--muted)" }}>
        <strong>No PDF Selected</strong>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ padding: "12px", background: "var(--bg-panel-muted)", borderBottom: "1px solid var(--line-soft)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0, fontSize: "14px" }}>原文对比查看</h3>
        <div style={{ fontSize: "12px", color: "var(--muted)" }}>
          <button 
            disabled={pageNumber <= 1} 
            onClick={() => setPageNumber(p => p - 1)}
            style={{ border: "1px solid var(--line-soft)", background: "#fff", padding: "4px 8px", borderRadius: "4px", marginRight: "8px", cursor: "pointer" }}
          >
            上一页
          </button>
          <span>Page {pageNumber} of {numPages ?? "--"}</span>
          <button 
            disabled={!numPages || pageNumber >= numPages} 
            onClick={() => setPageNumber(p => p + 1)}
            style={{ border: "1px solid var(--line-soft)", background: "#fff", padding: "4px 8px", borderRadius: "4px", marginLeft: "8px", cursor: "pointer" }}
          >
            下一页
          </button>
        </div>
      </div>
      <div style={{ flex: 1, overflow: "auto", padding: "16px", display: "flex", justifyContent: "center", backgroundColor: "#e5e7eb" }}>
        <Document
          file={fileSource}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<div>加载PDF中 (Loading PDF)...</div>}
          error={<div>无法加载PDF或文件不存在。</div>}
        >
          <Page 
            pageNumber={pageNumber} 
            customTextRenderer={customTextRenderer}
            renderTextLayer={true}
            renderAnnotationLayer={true}
            width={600}
            className="pdf-page-shadow"
          />
        </Document>
      </div>
      <style>{`
        .pdf-page-shadow {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
      `}</style>
    </div>
  );
}
