import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import ClientRoot from "@/components/ClientRoot"

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "LeadGenAI - B2B Lead Generation & Enrichment",
  description: "Find and enrich B2B sales leads from multiple sources",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
          <ClientRoot>
            {children}
          </ClientRoot>
        </ThemeProvider>
      </body>
    </html>
  )
}
