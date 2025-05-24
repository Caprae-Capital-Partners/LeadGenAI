// app/userSetting/page.tsx
"use client"

import SettingsPage from "@/components/user-settings"
import { Header } from "@/components/header"

export default function UserSettingsPage() {
    return (
        <>
            <Header />
            <main className="px-20 py-16">
                <SettingsPage />
            </main>
        </>
    )
}
