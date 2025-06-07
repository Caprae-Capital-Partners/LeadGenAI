"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function useEmailVerificationGuard() {
  const router = useRouter();

  useEffect(() => {
    const userRaw = sessionStorage.getItem("user");
    if (!userRaw) {
      router.push("/auth");
      return;
    }

    try {
      const user = JSON.parse(userRaw);
      if (!user.is_email_verified) {
        router.push("/auth");
      }
    } catch (err) {
      console.error("Invalid session user data:", err);
      router.push("/auth");
    }
  }, [router]);
}
