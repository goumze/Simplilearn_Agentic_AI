import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Allow the dev server to be accessed via 127.0.0.1 (dev-container port forwarding)
  allowedDevOrigins: ['127.0.0.1'],
  // Proxy /chat (and other backend paths) to the FastAPI server.
  // Server-side rewrites are origin-free, so CORS is not an issue.
  async rewrites() {
    return [
      {
        source: '/chat',
        destination: 'http://localhost:8000/chat',
      },
      {
        source: '/sessions',
        destination: 'http://localhost:8000/sessions',
      },
    ];
  },
};

export default nextConfig;
