/** @type {import('next').NextConfig} */
const nextConfig = {
  // Keep trailing slashes intact so FastAPI doesn't 307-redirect to :8000
  // (cross-origin redirects drop the Authorization header -> 401).
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*/',
        destination: 'http://localhost:8000/api/:path*/',
      },
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
