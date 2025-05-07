'use client';

import { ThemeProvider } from "@/components/shared/theme-provider";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
      {children}
    </ThemeProvider>
  );
}
