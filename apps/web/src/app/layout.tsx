import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "InvestPro",
  description: "Indian equity factor research lab"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
