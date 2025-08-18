/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost'],
  },
  env: {
    ORCHESTRATOR_URL: process.env.ORCHESTRATOR_URL || 'http://localhost:10007',
  },
}

module.exports = nextConfig
