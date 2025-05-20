import { Montserrat, Poppins } from "next/font/google"
import "./globals.css"

const montserrat = Montserrat({
  subsets: ["latin"],
  variable: "--font-montserrat",
})

const poppins = Poppins({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-poppins",
})

export const metadata = {
  title: "SaaSquatch Leads - B2B Lead Generation & Enrichment",
  description: "Find and enrich B2B sales leads from multiple sources",
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className={`${montserrat.variable} ${poppins.variable} font-sans bg-[#121826] text-gray-100`}>
        {children}
      </body>
    </html>
  )
}
