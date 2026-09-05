"use client";

import React, { ReactNode } from "react";
import Link from "next/link";
import { LucideIcon, ChevronRight } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface PageHeaderProps {
  badge?: string;
  badgeColor?: string;
  category?: string;
  categoryColor?: string;
  title: string;
  description?: string;
  icon?: LucideIcon | ReactNode;
  titleIcon?: LucideIcon | ReactNode;
  iconColor?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: ReactNode;
}

export default function PageHeader({
  badge,
  badgeColor = "bg-amber-500/10 text-amber-300 border-amber-500/25",
  category,
  categoryColor,
  title,
  description,
  icon,
  titleIcon,
  iconColor = "text-amber-400",
  breadcrumbs,
  actions,
}: PageHeaderProps) {
  // Support either icon or titleIcon prop, and either component type or JSX element
  const iconToRender = titleIcon ?? icon;

  const renderIcon = () => {
    if (!iconToRender) return null;
    if (React.isValidElement(iconToRender)) {
      return iconToRender;
    }
    const IconComponent = iconToRender as LucideIcon;
    return <IconComponent className={`w-6 h-6 shrink-0 ${iconColor}`} />;
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800/80 mb-6 shrink-0">
      <div>
        {/* Breadcrumbs or Category Badge */}
        {breadcrumbs && breadcrumbs.length > 0 ? (
          <nav className="flex items-center gap-1.5 mb-1.5 text-xs text-slate-400 font-medium">
            {breadcrumbs.map((bc, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <ChevronRight className="w-3 h-3 text-slate-600" />}
                {bc.href ? (
                  <Link href={bc.href} className="hover:text-white transition-colors">
                    {bc.label}
                  </Link>
                ) : (
                  <span className="text-slate-300 font-bold">{bc.label}</span>
                )}
              </React.Fragment>
            ))}
            {category && (
              <span className={`ml-2 text-[10px] uppercase font-mono px-2 py-0.5 rounded border font-bold ${categoryColor || badgeColor}`}>
                {category}
              </span>
            )}
          </nav>
        ) : (
          (category || badge) && (
            <div className="flex items-center gap-2 mb-1">
              {badge && (
                <span className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded border font-bold ${badgeColor}`}>
                  {badge}
                </span>
              )}
              {category && (
                <span className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded border font-bold ${categoryColor || "text-slate-400 border-slate-800 bg-slate-900/60"}`}>
                  {category}
                </span>
              )}
            </div>
          )
        )}

        <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 tracking-tight">
          {renderIcon()}
          <span>{title}</span>
        </h1>
        {description && (
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">{description}</p>
        )}
      </div>

      {actions && <div className="flex items-center gap-2.5 shrink-0">{actions}</div>}
    </div>
  );
}
