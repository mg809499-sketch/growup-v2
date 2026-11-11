import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false,
  transpilePackages: ["@growup/contracts", "@growup/config"],
};

export default nextConfig;
