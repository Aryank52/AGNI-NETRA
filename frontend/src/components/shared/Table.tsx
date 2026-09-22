"use client";

import React from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown, Loader2 } from "lucide-react";

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T, index: number) => React.ReactNode;
  align?: "left" | "center" | "right";
  width?: string;
  sortable?: boolean;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField?: keyof T | ((item: T) => string);
  sortKey?: string;
  sortDirection?: "asc" | "desc";
  onSort?: (key: string) => void;
  onRowClick?: (item: T) => void;
  selectedKey?: string;
  loading?: boolean;
  emptyText?: string;
  className?: string;
}

export default function Table<T extends Record<string, any>>({
  columns,
  data,
  keyField = "id",
  sortKey,
  sortDirection = "asc",
  onSort,
  onRowClick,
  selectedKey,
  loading = false,
  emptyText = "No records found matching criteria",
  className = "",
}: TableProps<T>) {
  const getKey = (item: T, idx: number): string => {
    if (typeof keyField === "function") return keyField(item);
    if (keyField && item[keyField] !== undefined) return String(item[keyField]);
    return String(idx);
  };

  return (
    <div
      className={`w-full overflow-hidden rounded-xl border border-agni-border bg-slate-950/40 relative ${className}`}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300 border-collapse">
          <thead className="bg-slate-900/90 text-[11px] font-mono uppercase tracking-wider text-slate-400 border-b border-slate-800 select-none">
            <tr>
              {columns.map((col) => {
                const isSorted = sortKey === col.key;
                const alignClass =
                  col.align === "right"
                    ? "text-right justify-end"
                    : col.align === "center"
                    ? "text-center justify-center"
                    : "text-left justify-start";

                return (
                  <th
                    key={col.key}
                    style={{ width: col.width }}
                    className={`px-3.5 py-3 font-semibold ${
                      col.sortable ? "cursor-pointer hover:text-amber-400 transition-colors" : ""
                    }`}
                    onClick={() => col.sortable && onSort && onSort(col.key)}
                  >
                    <div className={`flex items-center gap-1.5 ${alignClass}`}>
                      <span>{col.header}</span>
                      {col.sortable && (
                        <span className="text-slate-500">
                          {isSorted ? (
                            sortDirection === "asc" ? (
                              <ChevronUp className="w-3.5 h-3.5 text-amber-400" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5 text-amber-400" />
                            )
                          ) : (
                            <ChevronsUpDown className="w-3 h-3 opacity-40 hover:opacity-100" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-800/60 font-mono">
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="py-12 text-center text-slate-400">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Loader2 className="w-6 h-6 text-amber-400 animate-spin" />
                    <span className="text-xs">Loading operational telemetry records...</span>
                  </div>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="py-10 text-center text-slate-500 text-xs italic"
                >
                  {emptyText}
                </td>
              </tr>
            ) : (
              data.map((item, idx) => {
                const k = getKey(item, idx);
                const isSelected = selectedKey === k;

                return (
                  <tr
                    key={k}
                    onClick={() => onRowClick && onRowClick(item)}
                    className={`transition-colors ${
                      onRowClick ? "cursor-pointer" : ""
                    } ${
                      isSelected
                        ? "bg-amber-500/15 text-amber-300 font-semibold border-l-2 border-l-amber-400"
                        : "hover:bg-slate-800/40 odd:bg-slate-900/20 even:bg-transparent"
                    }`}
                  >
                    {columns.map((col) => {
                      const alignClass =
                        col.align === "right"
                          ? "text-right"
                          : col.align === "center"
                          ? "text-center"
                          : "text-left";

                      return (
                        <td key={col.key} className={`px-3.5 py-2.5 ${alignClass}`}>
                          {col.render ? col.render(item, idx) : item[col.key] ?? "—"}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
