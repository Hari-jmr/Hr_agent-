import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HR Agent Bot",
  description: "HR Policy Agent Chat Interface powered by OpenRouter + pgvector RAG",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
