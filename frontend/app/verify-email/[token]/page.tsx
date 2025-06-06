"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Notif from "@/components/ui/notif";

const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL!;
const VERIFY_ENDPOINT = `${DATABASE_URL}/auth/verify-email`;

export default function VerifyEmailPage() {
    const { token } = useParams<{ token: string }>();
    const router = useRouter();

    const [notif, setNotif] = useState({
        show: false,
        message: "",
        type: "info" as "success" | "error" | "info",
    });

    const showNotification = (
        message: string,
        type: "success" | "error" | "info" = "info"
    ) => {
        setNotif({ show: true, message, type });
        setTimeout(() => setNotif(prev => ({ ...prev, show: false })), 4000);
    };

    useEffect(() => {
        const verify = async () => {
            try {
                const res = await fetch(`${VERIFY_ENDPOINT}/${token}`, {
                    method: "GET",
                    credentials: "include",
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.message || "Verification failed.");

                showNotification("✅ Email verified successfully!", "success");
            } catch (err: any) {
                showNotification(err.message || "Something went wrong.", "error");
            } finally {
                setTimeout(() => {
                    router.push("/auth");
                }, 2000);
            }
        };

        if (token) verify();
    }, [token, router]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground px-4">
            <img
                src="/images/logo_horizontal.png"
                alt="SaaSquatch Leads Logo"
                className="w-[260px] mb-8"
            />
            <p className="text-4xl font-bold mb-6">Verifying your email…</p>
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary" />
            <Notif
                show={notif.show}
                message={notif.message}
                type={notif.type}
                onClose={() => setNotif(prev => ({ ...prev, show: false }))}
            />
        </div>
      );
}
