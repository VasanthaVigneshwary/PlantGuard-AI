import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Plant Guard AI",
  description: "AI-powered plant disease detection system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        {children}
      </body>
    </html>
  );
}