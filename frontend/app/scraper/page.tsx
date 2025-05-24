// app/scraper/page.tsx
"use client"

import { Scraper } from "@/components/scraper"
import { Header } from "@/components/header"

export default function ScraperPage() {
    return (
        <>
            <Header />
            <main className="px-20 py-16">
                <Scraper />
            </main>
        </>
    )
}