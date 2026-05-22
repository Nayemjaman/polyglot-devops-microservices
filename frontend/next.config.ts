import type { NextConfig } from "next";

const apiProxyTarget = process.env.API_PROXY_TARGET ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080";
const transactionTarget = process.env.TRANSACTION_API_TARGET ?? "http://localhost:8002";
const reportTarget = process.env.REPORT_API_TARGET ?? "http://localhost:8003";
const budgetTarget = process.env.BUDGET_API_TARGET ?? "http://localhost:8001";

const nextConfig: NextConfig = {
  typedRoutes: true,
  async rewrites() {
    return [
      {
        source: "/auth/:path*",
        destination: `${apiProxyTarget}/auth/:path*`
      },
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/api/:path*`
      },
      {
        source: "/status/transaction/:path*",
        destination: `${transactionTarget}/:path*`
      },
      {
        source: "/status/report/:path*",
        destination: `${reportTarget}/:path*`
      },
      {
        source: "/status/budget/:path*",
        destination: `${budgetTarget}/:path*`
      }
    ];
  }
};

export default nextConfig;
