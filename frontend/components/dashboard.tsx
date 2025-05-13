"use client"

import { useState, useEffect } from "react"
import { Scraper } from "@/components/scraper"
import { DataEnhancement } from "@/components/data-enhancement"
import { Header } from "@/components/header"
import { Sidebar } from "@/components/sidebar"
import { useSearchParams, useRouter } from "next/navigation"

export function Dashboard() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const tabParam = searchParams.get("tab")
  const [activeTab, setActiveTab] = useState(tabParam || "scraper")

  useEffect(() => {
    if (tabParam) {
      setActiveTab(tabParam)
    }
  }, [tabParam])

  const handleTabChange = (value: string) => {
    setActiveTab(value)
    router.push(`?tab=${value}`)
  }

  return (
    <div className="min-h-screen bg-mint-50">
      <Header />
      <div className="flex bg-mint-50 min-h-screen">
        <Sidebar activeTab={activeTab} setActiveTab={handleTabChange} />
        <main className="flex-1 p-6 bg-mint-50">{activeTab === "scraper" ? <Scraper /> : <DataEnhancement />}</main>
      </div>
    </div>
  )
}
