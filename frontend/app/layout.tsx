import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Snowtrip Planner",
  description: "Simple ski resort recommendations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
