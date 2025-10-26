import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Export as static files for Electron
  output: 'export',

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
