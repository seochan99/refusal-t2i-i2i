import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Evaluating Demographic Misrepresentation in I2I Portrait Editing | IJCAI 2026",
  description: "We systematically study demographic-conditioned failures in instruction-guided image-to-image editing, revealing pervasive skin lightening (62-71%) and stereotype replacement across open-weight models. Indian and Black subjects experience 72-75% skin lightening vs 44% for White subjects.",
  keywords: [
    "I2I editing",
    "image-to-image",
    "demographic bias",
    "AI fairness",
    "image generation",
    "IJCAI 2026",
    "skin lightening",
    "stereotype replacement",
    "diffusion models",
    "FLUX",
    "Qwen",
    "FairFace"
  ],
  authors: [{ name: "Anonymous" }],
  openGraph: {
    title: "Evaluating Demographic Misrepresentation in I2I Portrait Editing",
    description: "Systematic analysis of demographic-conditioned failures in instruction-guided image-to-image editing. We reveal pervasive skin lightening and stereotype replacement across open-weight models.",
    type: "website",
    images: [
      {
        url: "/assets/figure0.png",
        width: 1200,
        height: 400,
        alt: "Qualitative examples of demographic-conditioned failures in I2I editing",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Evaluating Demographic Misrepresentation in I2I Portrait Editing",
    description: "We reveal pervasive skin lightening (62-71%) and stereotype replacement in I2I editing models.",
    images: ["/assets/figure0.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <meta name="theme-color" content="#0f172a" media="(prefers-color-scheme: dark)" />
        <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)" />
      </head>
      <body className={`${inter.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
