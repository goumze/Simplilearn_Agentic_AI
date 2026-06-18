import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Digital Twin',
  description: 'Your AI Digital Twin — Week 2 of AI in Production',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
