import type { Metadata } from "next";
import "./globals.css";
import { StudioProvider } from "@/context/StudioContext";
import AppShell from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "AI YouTube Shorts Generator & Engagement Analyzer",
  description:
    "Transform long-form YouTube videos into high-engagement, quality-controlled Shorts with official YouTube publishing.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-zinc-950 text-zinc-100 min-h-screen antialiased flex flex-col">
        <StudioProvider>
          <AppShell>{children}</AppShell>
        </StudioProvider>
      </body>
    </html>
  );
}
