import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Pin the trace root to this project. Without it Next walks up and can latch
  // onto an unrelated lockfile in a parent directory.
  outputFileTracingRoot: dirname(fileURLToPath(import.meta.url)),

  async rewrites() {
    return [
      {
        // Development: FastAPI runs beside Next on :8000.
        // Production: Vercel hands this to the Python function at api/index.py,
        // which is invoked with the original /api/py/* path still intact —
        // hence the matching prefix on the FastAPI routes.
        source: "/api/py/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/api/py/:path*"
            : "/api/",
      },
    ];
  },
};

export default nextConfig;
