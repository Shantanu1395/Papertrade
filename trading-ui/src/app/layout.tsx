import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { ApiProvider } from "@/components/providers/ApiProvider";
import { ToastProvider } from "@/components/Toast";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Paper Trading Dashboard",
  description: "Cryptocurrency paper trading dashboard with portfolio management and analytics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased`}>
        <QueryProvider>
          <ApiProvider>
            <ToastProvider>
              {children}
            </ToastProvider>
          </ApiProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
