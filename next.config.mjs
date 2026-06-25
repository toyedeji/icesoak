/** @type {import('next').NextConfig} */
const nextConfig = {
  // Fully static directory: crawlers and AI answer engines receive complete HTML.
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
  // Surface accidental "null" / data issues at build instead of shipping them.
  reactStrictMode: true,
};

export default nextConfig;
