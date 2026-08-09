import type { Metadata, Viewport } from 'next';
import { Archivo_Black, Space_Grotesk, Space_Mono } from 'next/font/google';
import Cursor from '@/components/ui/Cursor';
import './globals.css';

const display = Archivo_Black({
  subsets: ['latin'],
  weight: '400',
  variable: '--font-display',
  display: 'swap',
});

const sans = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const mono = Space_Mono({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'VERITAS — Prove It.',
    template: '%s | VERITAS',
  },
  description:
    "Résumés lie. Evidence doesn't. VERITAS runs adaptive interviews that chase proof, not buzzwords.",
  keywords: ['AI interview', 'skill verification', 'evidence-based hiring'],
  openGraph: {
    title: 'VERITAS — Prove It.',
    description: "Résumés lie. Evidence doesn't.",
    type: 'website',
  },
};

export const viewport: Viewport = {
  themeColor: '#F2EEE3',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${mono.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen bg-bone font-sans text-ink antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:border-3 focus:border-ink focus:bg-acid focus:px-4 focus:py-2 focus:font-black focus:uppercase"
        >
          Skip to content
        </a>
        <Cursor />
        {children}
      </body>
    </html>
  );
}
