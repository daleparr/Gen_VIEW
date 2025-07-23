import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Navigation } from "@/components/layout/Navigation";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "GEN-VIEW-KSE | AI-Powered Fashion Generation",
  description: "Revolutionary AI platform for fashion generation, visualization, and curation with advanced neural rendering and intelligent memory systems.",
  keywords: ["AI", "Fashion", "Generation", "NeRF", "Machine Learning", "Style Transfer"],
  authors: [{ name: "GEN-VIEW-KSE Team" }],
  viewport: "width=device-width, initial-scale=1",
  themeColor: "#000000",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-black text-white antialiased`}>
        <Providers>
          <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
            <Navigation />
            <main className="relative">
              {children}
            </main>
            <Toaster />
          </div>
        </Providers>
      </body>
    </html>
  );
}
