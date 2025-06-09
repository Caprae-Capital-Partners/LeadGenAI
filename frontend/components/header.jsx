import Link from "next/link";
import { User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Image from "next/image";
import { useEffect, useState } from "react";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL_P2;
export function Header() {
  const [userEmail, setUserEmail] = useState("");
  useEffect(() => {
    if (typeof window !== "undefined") {
      const user = JSON.parse(sessionStorage.getItem("user") || "{}");
      setUserEmail(user.email || "user@example.com");
    }
  }, []);
  return (
    <header className="w-full bg-[#1A2133] border-b border-[#2E3A59] overflow-x-auto">
      <div className="min-w-[1200px] flex h-24 items-center px-10">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="h-16 w-auto relative">
            <Link href="/">
              <Image
                src="/images/logo_horizontal.png"
                alt="SaaSquatch Logo"
                width={270}
                height={96}
                className="object-contain"
              />
            </Link>
          </div>
        </div>

        {/* Navigation */}
        <nav className="ml-auto flex items-center gap-12 text-base uppercase tracking-wider font-bold">
          <Link
            href="/"
            className="text-white hover:text-yellow-400 transition-colors"
          >
            Home
          </Link>
          <Link
            href="/scraper"
            className="text-white hover:text-yellow-400 transition-colors"
          >
            Scraper Tool
          </Link>
          <Link
            href="/documentation"
            className="text-white hover:text-yellow-400 transition-colors"
          >
            Documentation
          </Link>
          <Link
            href="/contact"
            className="text-white hover:text-yellow-400 transition-colors"
          >
            Contact Us
          </Link>

          {/* Avatar */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="relative h-10 w-10 rounded-full text-gray-300 hover:text-white hover:bg-dark-hover"
              >
                <Avatar className="h-10 w-10">
                  <AvatarImage src="/placeholder.svg" alt="User" />
                  <AvatarFallback className="bg-dark-hover text-gray-200">
                    U
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-56 bg-dark-tertiary border-dark-border text-gray-200"
              align="end"
              forceMount
            >
              <DropdownMenuLabel className="font-normal text-gray-400">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none text-gray-200">
                    User
                  </p>
                  <p className="text-xs leading-none text-gray-400">
                    {userEmail}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-dark-border" />
              <DropdownMenuItem
                asChild
                className="hover:bg-dark-hover focus:bg-dark-hover cursor-pointer"
              >
                <Link href="/userSetting" className="flex items-center w-full">
                  <User className="mr-2 h-4 w-4 text-teal-400" />
                  <span>Profile</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-dark-border" />
              <DropdownMenuItem
                onClick={async () => {
                  // 1) Close Growjo scraper tabs
                  try {
                    await axios.post(`${BACKEND_URL}/close-growjo-scraper`);
                    console.log("✅ Growjo scraper closed");
                  } catch (err) {
                    console.error("❌ Failed to close Growjo scraper:", err);
                    // proceed to logout even if closing fails
                  }

                  // 2) Perform logout
                  try {
                    const res = await fetch(
                      "https://data.capraeleadseekers.site/api/auth/logout",
                      {
                        method: "POST",
                        credentials: "include",
                      }
                    );

                    if (res.ok) {
                      sessionStorage.clear(); // ✅ Clear client-side session
                      window.location.href = "/auth"; // ⬅️ Redirect to login
                    } else {
                      const data = await res.json();
                      alert(
                        `Logout failed: ${data.message || "Unknown error"}`
                      );
                    }
                  } catch (error) {
                    console.error("❌ Logout error:", error);
                    alert("Network error during logout. Try again.");
                  }
                }}
                className="hover:bg-dark-hover focus:bg-dark-hover cursor-pointer"
              >
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </nav>
      </div>
    </header>
  );
}
