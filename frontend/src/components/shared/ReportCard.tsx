"use client";

import React, { useState } from "react";
import { 
  FileText, Download, Loader2, AlertTriangle, 
  RefreshCw, CheckCircle2, Clock, Calendar 
} from "lucide-react";
import Button from "./Button";
import StatusBadge from "./StatusBadge";

export type ReportState = "GENERATING" | "READY" | "FAILED" | "RETRY";

export interface ReportItem {
  id: string;
  title: string;
  reportType: "DOSSIER" | "COMPLIANCE" | "PREVENTION" | "EXPORTS" | string;
  status: ReportState;
  generatedAt?: string;
  fileSizeBytes?: number;
  downloadUrl?: string;
  errorMessage?: string;
}

export interface ReportCardProps {
  report: ReportItem;
  onDownload?: (report: ReportItem) => Promise<void>;
  onRetry?: (report: ReportItem) => Promise<void>;
  className?: string;
}

export default function ReportCard({
  report,
  onDownload,
  onRetry,
  className = "",
}: ReportCardProps) {
  const [downloading, setDownloading] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const handleDownload = async () => {
    if (!onDownload && report.downloadUrl) {
      window.open(report.downloadUrl, "_blank");
      return;
    }
    if (onDownload) {
      setDownloading(true);
      try {
        await onDownload(report);
      } finally {
        setDownloading(false);
      }
    }
  };

  const handleRetry = async () => {
    if (onRetry) {
      setRetrying(true);
      try {
        await onRetry(report);
      } finally {
        setRetrying(false);
      }
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div
      className={`p-4 rounded-xl border border-agni-border bg-slate-900/80 font-mono text-xs flex flex-col justify-between gap-3 shadow-md hover:border-slate-700 transition-all ${className}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
            <FileText className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <h4 className="font-bold text-slate-200 truncate">{report.title}</h4>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider">
              {report.reportType} REPORT
            </span>
          </div>
        </div>

        <div className="shrink-0">
          {report.status === "READY" && (
            <StatusBadge status="ACTIVE" label="READY" size="xs" />
          )}
          {report.status === "GENERATING" && (
            <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40">
              <Loader2 className="w-2.5 h-2.5 animate-spin" />
              <span>GENERATING</span>
            </span>
          )}
          {report.status === "FAILED" && (
            <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/40 font-bold">
              <AlertTriangle className="w-2.5 h-2.5" />
              <span>FAILED</span>
            </span>
          )}
          {report.status === "RETRY" && (
            <StatusBadge status="PENDING" label="QUEUED" size="xs" />
          )}
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800">
        <div className="flex items-center gap-2">
          {report.generatedAt && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-500" />
              <span>{report.generatedAt}</span>
            </span>
          )}
        </div>
        <span className="text-slate-500 font-mono">
          {formatFileSize(report.fileSizeBytes)}
        </span>
      </div>

      {report.status === "FAILED" && report.errorMessage && (
        <div className="p-2 rounded bg-red-950/40 border border-red-500/30 text-red-300 text-[10px]">
          {report.errorMessage}
        </div>
      )}

      <div className="pt-1 flex items-center justify-end gap-2">
        {report.status === "FAILED" && onRetry && (
          <Button
            size="xs"
            variant="outline"
            onClick={handleRetry}
            loading={retrying}
            icon={<RefreshCw className="w-3 h-3" />}
          >
            Retry Generation
          </Button>
        )}

        {report.status === "READY" && (
          <Button
            size="xs"
            variant="primary"
            onClick={handleDownload}
            loading={downloading}
            icon={<Download className="w-3 h-3" />}
          >
            Download PDF
          </Button>
        )}
      </div>
    </div>
  );
}
