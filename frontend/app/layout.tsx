// ========================================
// Root Layout - With Toast Provider & Animations
// ========================================

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/toast-provider";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Scrappy - Google Maps Lead Scraper",
  description:
    "Professional-grade Google Maps lead scraper with deduplication, Google Sheets integration, and SMS outreach.",
  keywords: [
    "lead scraper",
    "google maps scraper",
    "business leads",
    "lead generation",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} antialiased`}>
        <ToastProvider />
        {children}
      </body>
    </html>
  );
}
