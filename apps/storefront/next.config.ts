import type { NextConfig } from "next";

const mediaBaseUrl = process.env.NEXT_PUBLIC_MEDIA_BASE_URL;
const mediaPattern = (() => {
  if (!mediaBaseUrl) {
    return null;
  }
  try {
    const url = new URL(mediaBaseUrl);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      return null;
    }
    if (url.username || url.password || url.search || url.hash) {
      return null;
    }
    url.pathname = `${url.pathname.replace(/\/$/, "")}/**`;
    return url;
  } catch {
    return null;
  }
})();

const nextConfig: NextConfig = {
  agentRules: false,
  transpilePackages: ["@growup/contracts", "@growup/config"],
  async headers() {
    const rawOrigins = process.env.GROWUP_ADMIN_ORIGIN ?? "http://localhost:3001,http://localhost:3011";
    const adminOrigins = rawOrigins
      .split(",")
      .map((origin) => origin.trim().replace(/\/$/, ""))
      .filter(Boolean)
      .join(" ");
    return [
      {
        source: "/preview",
        headers: [
          {
            key: "Content-Security-Policy",
            value: `frame-ancestors 'self' ${adminOrigins}`,
          },
          { key: "Cache-Control", value: "no-store" },
        ],
      },
    ];
  },
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "localhost" },
      { protocol: "http", hostname: "127.0.0.1" },
      { protocol: "https", hostname: "cdn.growup.com" },
      { protocol: "https", hostname: "*.r2.dev" },
      ...(mediaPattern ? [mediaPattern] : []),
    ],
  },
};

export default nextConfig;
