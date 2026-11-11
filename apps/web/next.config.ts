import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@growup/config"],
  images: {
    remotePatterns: [],
  },
};

export default nextConfig;
