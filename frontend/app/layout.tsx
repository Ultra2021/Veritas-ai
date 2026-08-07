import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Veritas AI | Evidence-Driven AI Interview Platform',
  description: "Don't just evaluate answers. Verify skills with evidence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090d16] text-gray-100 antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
        {children}
      </body>
    </html>
  );
}
