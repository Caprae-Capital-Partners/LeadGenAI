"use client"

import { Header } from "@/components/header"
import { Sidebar } from "@/components/sidebar"

export default function CompaniesPage() {
    return (
        <div className="flex flex-col h-screen">
            {/* Top Header */}
            <Header />

            {/* Below: Sidebar + Main content */}
            <div className="flex flex-1 overflow-hidden">
                <Sidebar />
                <main className="flex-1 p-6 overflow-auto">
                    <h1 className="text-2xl font-bold text-foreground">Persons</h1>
                </main>
            </div>
        </div>
    )
}
