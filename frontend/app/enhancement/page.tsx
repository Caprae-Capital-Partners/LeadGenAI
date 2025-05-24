// app/enhancement/page.tsx
"use client"

import { DataEnhancement } from "@/components/data-enhancement"
import { Header } from "@/components/header"

export default function EnhancementPage() {
    return (
        <>
            <Header />
            <main className="px-20 py-16">
                <DataEnhancement />
            </main>
        </>
    )
}
