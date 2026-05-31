import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LinguaVoice — Spanish Tutor",
  description: "Real-time voice-first Spanish tutor",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@2.44.0/tabler-icons.min.css"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
