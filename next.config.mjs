import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

// Render (and any Docker host) builds with STATIC_EXPORT=1: the interface is
// emitted to out/ and FastAPI serves it alongside the API from one origin, so
// no rewrite is involved. Vercel leaves this unset and uses the rewrite below
// to reach the Python serverless function.
const staticExport = process.env.STATIC_EXPORT === "1";

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Pin the trace root to this project. Without it Next walks up and can latch
  // onto an unrelated lockfile in a parent directory.
  outputFileTracingRoot: dirname(fileURLToPath(import.meta.url)),

  ...(staticExport
    ? {
        output: "export",
        // No Next server in front of the export to optimise on the fly.
        images: { unoptimized: true },
      }
    : {
        async rewrites() {
          return [
            {
              // Development: FastAPI runs beside Next on :8000.
              // Production on Vercel: routed to the Python function at
              // api/index.py, which is invoked with the original /api/py/*
              // path intact — hence the matching prefix on the FastAPI routes.
              source: "/api/py/:path*",
              destination:
                process.env.NODE_ENV === "development"
                  ? "http://127.0.0.1:8000/api/py/:path*"
                  : "/api/",
            },
          ];
        },
      }),
};

export default nextConfig;
