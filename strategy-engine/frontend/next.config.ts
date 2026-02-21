import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",  // Required for Cloud Run Docker image (self-contained bundle)
  // Allow API images from external domains if needed
  images: {
    remotePatterns: [],
  },
};

export default nextConfig;
