"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface NotifProps {
    show: boolean;
    message: string;
    type?: "success" | "error" | "info";
    duration?: number;
    onClose: () => void;
}

export default function Notif({
    show,
    message,
    type = "success",
    duration = 3000,
    onClose,
}: NotifProps) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        let showTimer: NodeJS.Timeout;
        let hideTimer: NodeJS.Timeout;
        let clearTimer: NodeJS.Timeout;

        if (show) {
            setVisible(false); // reset before enter
            showTimer = setTimeout(() => setVisible(true), 10); // small delay for transition

            hideTimer = setTimeout(() => {
                setVisible(false); // start exit
                clearTimer = setTimeout(onClose, 300); // give time for animation to complete
            }, duration);
        }

        return () => {
            clearTimeout(showTimer);
            clearTimeout(hideTimer);
            clearTimeout(clearTimer);
        };
    }, [show, duration, onClose]);

    const baseStyle =
        "fixed top-6 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded-lg shadow-lg text-base font-semibold transition-all duration-300 ease-in-out";

    const typeStyle = {
        success: "bg-[#72cc50] text-white",
        error: "bg-red-600 text-white",
        info: "bg-blue-600 text-white",
    };

    return (
        <div
            className={cn(
                baseStyle,
                typeStyle[type],
                visible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-6"
            )}
        >
            {message}
        </div>
    );
}

