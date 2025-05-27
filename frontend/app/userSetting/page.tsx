// app/userSetting/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import SettingsPage from "@/components/user-settings";
import { Header } from "@/components/header";

export default function UserSettingsPage() {
    const router = useRouter();
    const [isCheckingAuth, setIsCheckingAuth] = useState(true);

    useEffect(() => {
        const verifyLogin = async () => {
            try {
                const res = await fetch("https://data.capraeleadseekers.site/api/ping-auth", {
                    method: "GET",
                    credentials: "include",
                });

                if (res.status !== 204) {
                    router.replace("/auth");
                    return;
                  }

                setIsCheckingAuth(false);
            } catch (error) {
                console.error("❌ Auth error:", error);
                router.replace("/auth");
            }
        };

        verifyLogin();
    }, []);

    if (isCheckingAuth) {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm z-50 flex items-center justify-center pointer-events-none">
                <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-yellow-400"></div>
            </div>
        );
    }

    return (
        <>
            <Header />
            <main className="px-20 py-16">
                <SettingsPage />
            </main>
        </>
    );
}
