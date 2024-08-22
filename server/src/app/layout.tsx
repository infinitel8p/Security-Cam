import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Security-Cam Dashboard",
  description: "A dashboard for your security camera.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navbar />
        <div className="ml-40 bg-[#121019] min-h-dvh text-white"> {/*changed do a darker color to disabled this flashbang*/}
          {children}
        </div>
      </body>
    </html>
  );
}