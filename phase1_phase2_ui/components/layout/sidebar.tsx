"use client"

import { Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface SidebarProps {
  activeTab: string
  setActiveTab: (tab: string) => void
}

export function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  return (
    <div className="hidden lg:block w-64 border-r bg-white h-screen sticky top-0">
      <div className="flex flex-col gap-2 p-4">
        <Button
          variant="ghost"
          className={cn("justify-start gap-2", activeTab === "scraper" && "bg-mint-100 text-teal-700")}
          onClick={() => setActiveTab("scraper")}
        >
          <Search className="h-5 w-5" />
          Company Finder
        </Button>
      </div>
    </div>
  )
}
