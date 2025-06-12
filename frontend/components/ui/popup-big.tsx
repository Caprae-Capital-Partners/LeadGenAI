"use client";

import { ReactNode } from "react";

interface PopupProps {
    show: boolean;
    onClose: () => void;
    children: ReactNode;
}

export default function PopupBig({ show, onClose, children }: PopupProps) {
    if (!show) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card text-card-foreground rounded-2xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl relative">
                <button
                    onClick={onClose}
                    className="absolute top-3 right-4 text-2xl text-muted-foreground hover:text-foreground"
                >
                    &times;
                </button>
                {children}
            </div>
        </div>
    );
}