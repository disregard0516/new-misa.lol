/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  basePath: "/dashboard",
  experimental: {
    optimizePackageImports: ["lucide-react", "react-icons"],
  },
  outputFileTracingRoot: process.cwd(),
};

export default nextConfig;
