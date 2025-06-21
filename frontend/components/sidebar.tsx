"use client"

import { Building, Users, Mail, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useRouter, usePathname } from "next/navigation"

export function Sidebar() {
  const router = useRouter()
  const pathname = usePathname()

  const isActive = (route: string) => pathname === route

  return (
    <div className="hidden lg:block w-64 border-r border-dark-border bg-dark-secondary h-screen sticky top-0">
      <div className="flex flex-col gap-2 p-4">
        <Button
          variant="ghost"
          className={cn(
            "justify-start gap-2 text-gray-400 hover:text-white hover:bg-dark-hover",
            isActive("/lead/companies") && "bg-dark-hover text-white"
          )}
          onClick={() => router.push("/lead/companies")}
        >
          <Building className="h-5 w-5" />
          Companies
        </Button>

        <Button
          variant="ghost"
          className={cn(
            "justify-start gap-2 text-gray-400 hover:text-white hover:bg-dark-hover",
            isActive("/lead/persons") && "bg-dark-hover text-white"
          )}
          onClick={() => router.push("/lead/persons")}
        >
          <Users className="h-5 w-5" />
          Persons
        </Button>

        <Button
          variant="ghost"
          className={cn(
            "justify-start gap-2 text-gray-400 hover:text-white hover:bg-dark-hover",
            isActive("/email-generator") && "bg-dark-hover text-white"
          )}
          onClick={() => router.push("/email-generator")}
        >
          <Mail className="h-5 w-5" />
          Email Generator
        </Button>

        <Button
          variant="ghost"
          className={cn(
            "justify-start gap-2 text-gray-400 hover:text-white hover:bg-dark-hover",
            isActive("/linkedin-generator") && "bg-dark-hover text-white"
          )}
          onClick={() => router.push("/linkedin-generator")}
        >
          <MessageSquare className="h-5 w-5" />
          LinkedIn Messenger
        </Button>
      </div>
    </div>
  )
}
