import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/authContext";

export const metadata: Metadata = {
  title: "AGNI-NETRA — Geospatial Thermal Intelligence & Industrial Monitoring Platform",
  description: "National-scale geospatial intelligence platform fusing NASA FIRMS satellite observations, OpenStreetMap cadastre, CEA utilities, and PostGIS 3.4 spatial analytics for industrial thermal anomaly detection and environmental risk assessment.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
  openGraph: {
    type: "website",
    title: "AGNI-NETRA — Geospatial Thermal Intelligence Platform",
    description: "AI-based detection, classification, and segregation of industrial fires and persistent thermal sources using NASA FIRMS, OSM, and multi-sensor satellite telemetry.",
    siteName: "AGNI-NETRA",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  let _devToolsReportSoftNavs = window.devToolsReportSoftNavs;
                  Object.defineProperty(window, 'devToolsReportSoftNavs', {
                    configurable: true,
                    enumerable: true,
                    get: function() { return _devToolsReportSoftNavs; },
                    set: function(fn) {
                      if (typeof fn === 'function') {
                        _devToolsReportSoftNavs = function(type, metric) {
                          if (metric && Array.isArray(metric.entries) && metric.entries.length === 0) {
                            return;
                          }
                          return fn.apply(this, arguments);
                        };
                      } else {
                        _devToolsReportSoftNavs = fn;
                      }
                    }
                  });
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body suppressHydrationWarning className="bg-agni-navy text-slate-100 min-h-screen antialiased flex flex-col selection:bg-amber-500 selection:text-slate-950">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
