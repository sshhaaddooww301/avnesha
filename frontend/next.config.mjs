/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  async redirects() {
    return [
      {
        source: "/testlab",
        destination: "/test-lab",
        permanent: true,
      },
      {
        source: "/test_lab",
        destination: "/test-lab",
        permanent: true,
      },
      {
        source: "/lab",
        destination: "/test-lab",
        permanent: true,
      },
      {
        source: "/test",
        destination: "/test-lab",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
