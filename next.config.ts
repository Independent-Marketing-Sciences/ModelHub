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

  // Disable experimental features that use symlinks
  experimental: {
    // @ts-ignore - disable symlinks completely
    disableOptimizedLoading: true,
  },

  // Disable webpack caching to avoid OneDrive symlink issues
  webpack: (config, { isServer }) => {
    // Disable filesystem caching for OneDrive compatibility
    config.cache = false;

    // Disable symlinks in resolution
    config.resolve = {
      ...config.resolve,
      symlinks: false,
    };

    // Disable CSS optimization that creates symlinks
    config.optimization = {
      ...config.optimization,
      splitChunks: false,
    };

    return config;
  },

  // Disable static optimization
  generateBuildId: async () => {
    return 'build-' + Date.now();
  },
};

export default nextConfig;
