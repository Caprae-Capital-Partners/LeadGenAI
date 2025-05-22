import { User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import Image from "next/image"

export function Header() {
  return (
    <header className="border-b border-[#2E3A59] bg-[#1A2133]">
      <div className="flex h-16 items-center px-6">
        <div className="flex items-center gap-2">
          <div className="h-10 w-10 relative">
            <Image
              src="/images/saasquatch-logo.png"
              alt="SaaSquatch Logo"
              width={40}
              height={40}
              className="object-contain"
            />
          </div>
          <span className="text-xl font-bold font-heading text-white">
            SaaSquatch <span className="text-primary">Leads</span>
          </span>
        </div>
        <div className="ml-auto flex items-center gap-4">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="relative h-8 w-8 rounded-full text-gray-300 hover:text-white hover:bg-dark-hover"
              >
                <Avatar className="h-8 w-8">
                  <AvatarImage src="/placeholder.svg" alt="User" />
                  <AvatarFallback className="bg-dark-hover text-gray-200">U</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56 bg-dark-tertiary border-dark-border text-gray-200" align="end" forceMount>
              <DropdownMenuLabel className="font-normal text-gray-400">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none text-gray-200">User</p>
                  <p className="text-xs leading-none text-gray-400">user@example.com</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-dark-border" />
              <DropdownMenuItem className="hover:bg-dark-hover focus:bg-dark-hover cursor-pointer">
                <User className="mr-2 h-4 w-4 text-teal-400" />
                <span>Profile</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-dark-border" />
              <DropdownMenuItem className="hover:bg-dark-hover focus:bg-dark-hover cursor-pointer">
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
