import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Export as static files for Electron
  output: 'export',

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },

  // Fix for OneDrive symlink issues during build
  outputFileTracingRoot: path.join(__dirname),

  // Disable webpack caching to avoid OneDrive symlink issues
  webpack: (config, { isServer }) => {
    // Disable filesystem caching for OneDrive compatibility
    config.cache = false;
    return config;
  },
};

export default nextConfig;
