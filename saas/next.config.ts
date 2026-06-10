import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "export",        // Static HTML export for AWS deployment
  images: {
    unoptimized: true,     // Required for static export (no Next.js image server)
  },
};

export default nextConfig;
