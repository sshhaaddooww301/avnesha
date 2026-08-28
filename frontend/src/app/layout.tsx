import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "QDS·SIEM — Quantum Digital Signature Cyber Threat SOC",
  description:
    "Production-grade Security Information and Event Management (SIEM) dashboard for Quantum Digital Signature (QDS) architectures with real-time detection and blockchain audit ledger.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-background text-gray-100`}>
        {children}
      </body>
    </html>
  );
}
