import type { Metadata } from "next";
import { Quicksand } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/AuthProvider";
import { QueryProvider } from "@/lib/providers/QueryProvider";

const quicksand = Quicksand({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const superLarky = localFont({
  src: "../public/fonts/SuperLarky.ttf",
  variable: "--font-playful",
});

const ringus = localFont({
  src: "../public/fonts/Ringus-Regular.ttf",
  variable: "--font-ringus",
});

export const metadata: Metadata = {
  title: "Closet Muse",
  description: "Plan outfits from the clothes you already own.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${quicksand.variable} ${superLarky.variable} ${ringus.variable} h-full`}>
      <body className="h-screen overflow-hidden flex flex-col bg-cream text-ink">
        <QueryProvider>
          <AuthProvider>{children}</AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
