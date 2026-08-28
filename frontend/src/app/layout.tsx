import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/authContext";

export const metadata: Metadata = {
  title: "AGNI-NETRA — AI Geospatial Industrial Thermal Risk & Anomaly Intelligence",
  description: "AI Geospatial Network for Industrial Thermal Risk & Anomaly Analysis (SIH26162). Transforming NASA FIRMS, OSM, and multi-sensor satellite observations into explainable decision intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" />
      </head>
      <body className="bg-agni-navy text-slate-100 min-h-screen antialiased flex flex-col selection:bg-amber-500 selection:text-slate-950">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
