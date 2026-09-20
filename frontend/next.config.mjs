/** @type {import('next').NextConfig} */
const securityHeaders = [
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  {
    key: "X-Frame-Options",
    value: "DENY",
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  {
    key: "Permissions-Policy",
    value: "microphone=(self), camera=(), geolocation=()",
  },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
      "worker-src 'self' blob:",
      "child-src 'self' blob:",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://basemaps.cartocdn.com https://*.basemaps.cartocdn.com",
      "font-src 'self' https://fonts.gstatic.com data: https://basemaps.cartocdn.com https://*.basemaps.cartocdn.com",
      "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://demotiles.maplibre.org https://*.basemaps.cartocdn.com https://basemaps.cartocdn.com https://*.cartocdn.com",
      "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 https://demotiles.maplibre.org https://*.tile.openstreetmap.org https://*.basemaps.cartocdn.com https://basemaps.cartocdn.com https://*.cartocdn.com",
      "frame-ancestors 'none'",
      "form-action 'self'",
    ].join("; "),
  },
];

const nextConfig = {
  reactStrictMode: false,
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;

