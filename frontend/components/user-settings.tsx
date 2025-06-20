"use client";
/* eslint-disable @next/next/no-img-element */
import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import Notif from "@/components/ui/notif"; // adjust path if needed
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL;
const DATABASE_URL_NOAPI = DATABASE_URL?.replace(/\/api\/?$/, "");
type SettingsPageProps = {
    isEditing: boolean;
    setIsEditing: React.Dispatch<React.SetStateAction<boolean>>;
};

type User = {
    created_at: string;
    email: string;
    is_active: boolean;
    role: string;
    tier: string;
    user_id: string;
    username: string;
    linkedin_url?: string;
};

export default function SettingsPage({ isEditing, setIsEditing }: SettingsPageProps) {
    const [user, setUser] = useState<User | null>(null);
    const [username, setUsername] = useState("");
    const [linkedin, setLinkedin] = useState("");
    const [email, setEmail] = useState("");
    const [oldPassword, setOldPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [notif, setNotif] = useState<{
        show: boolean;
        message: string;
        type: "success" | "error";
    }>({ show: false, message: "", type: "success" });
    const [showPausePopup, setShowPausePopup] = useState(false);
    const [showCancelPopup, setShowCancelPopup] = useState(false);
    const [pauseDuration, setPauseDuration] = useState<30 | 60 | 90>(30);

    useEffect(() => {
        const sessionUser = sessionStorage.getItem("user");
        if (sessionUser) {
            const parsedUser: User = JSON.parse(sessionUser);
            setUser(parsedUser);
            setUsername(parsedUser.username);
            setEmail(parsedUser.email);
            setLinkedin(parsedUser.linkedin_url ?? "");
        }
    }, []);

    const getBillingAmount = (tier: string) => {
        switch (tier) {
            case "bronze": return 19;
            case "silver": return 49;
            case "gold": return 99;
            case "platinum": return 199;
            default: return null;
        }
    };

    if (!user) return null;

    return (
        <div className="mx-auto max-w-4xl space-y-8 px-4 py-10">
            <div>
                <h1 className="text-4xl font-bold">User Settings</h1>
            </div>

            {/* PERSONAL INFORMATION */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <h2 className="text-lg font-semibold">Your Profile</h2>
                    <div className="flex gap-2">
                        {isEditing && user.tier && user.tier.toLowerCase() !== "free" && (
                            <>
                                <Button
                                    size="sm"
                                    variant="destructive"
                                    className="text-sm"
                                    onClick={() => setShowCancelPopup(true)}
                                >
                                    Cancel Subscription
                                </Button>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    className="text-sm"
                                    onClick={() => setShowPausePopup(true)}
                                >
                                    Pause Subscription
                                </Button>
                            </>
                        )}
                        <Button
                            size="sm"
                            onClick={() => setIsEditing((prev: boolean) => !prev)}
                            className="text-sm"
                        >
                            {isEditing ? "Cancel" : "Edit Profile"}
                        </Button>
                    </div>
                </CardHeader>

                <CardContent className="space-y-6">
                    {/* Avatar + Change button */}
                    <div className="flex items-center gap-6">
                        <img
                            src="https://i.pravatar.cc/80?img=1"
                            alt="User avatar"
                            className="h-20 w-20 rounded-full object-cover"
                        />
                        {isEditing && (
                            <Button variant="outline" size="sm">
                                Change
                            </Button>
                        )}
                    </div>

                    {/* Name + Email grid */}
                    <div className="grid gap-6 md:grid-cols-2">
                        <div className="flex flex-col gap-1.5">
                            <Label htmlFor="name">Name</Label>
                            <Input
                                id="name"
                                value={username}
                                readOnly={!isEditing}
                                onChange={(e) => setUsername(e.target.value)}
                                className={!isEditing ? "border-transparent bg-muted cursor-default" : ""}
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                readOnly={!isEditing}
                                className={!isEditing ? "border-transparent bg-muted cursor-default" : ""}
                            />
                        </div>
                    </div>

                    {/* LinkedIn Profile Input */}
                    <div className="flex flex-col gap-1.5">
                        <Label htmlFor="linkedin">LinkedIn Profile</Label>
                        <Input
                            id="linkedin"
                            placeholder="https://linkedin.com/in/..."
                            value={linkedin}
                            onChange={(e) => setLinkedin(e.target.value)}
                            readOnly={!isEditing}
                            className={!isEditing ? "border-transparent bg-muted cursor-default" : ""}
                        />
                        <p className="text-sm text-muted-foreground">
                            Add your LinkedIn profile URL to help others connect with you
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* CHANGE PASSWORD SECTION (Only visible in edit mode) */}
            {isEditing && (
                <Card>
                    <CardHeader>
                        <h2 className="text-lg font-semibold">Change Password</h2>
                    </CardHeader>

                    <CardContent>
                        <form className="grid gap-6 md:grid-cols-3">
                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor="oldPassword">Old Password</Label>
                                <Input
                                    id="oldPassword"
                                    type="password"
                                    placeholder="Enter your old password"
                                    value={oldPassword}
                                    onChange={(e) => setOldPassword(e.target.value)}
                                />
                            </div>

                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor="newPassword">New Password</Label>
                                <Input
                                    id="newPassword"
                                    type="password"
                                    placeholder="Enter new password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                />
                            </div>

                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                                <Input
                                    id="confirmPassword"
                                    type="password"
                                    placeholder="Re-enter new password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                />
                            </div>
                        </form>
                    </CardContent>

                </Card>
            )}

            {/* SAVE BUTTON (Only in edit mode) */}
            {isEditing && (
                <Button
                    className="md:col-span-3 w-full"
                    type="button"
                    onClick={async () => {
                        if (newPassword && newPassword !== confirmPassword) {
                            setNotif({
                                show: true,
                                message: "New passwords do not match.",
                                type: "error",
                            });
                            return;
                        }

                        const payload: any = {
                            username,
                            email,
                            linkedin_url: linkedin,
                        };

                        if (newPassword) {
                            payload.password = newPassword;
                        }

                        try {
                            const res = await fetch(`${DATABASE_URL}/auth/update_user`, {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                credentials: "include",
                                body: JSON.stringify(payload),
                            });

                            const data = await res.json();

                            if (res.ok) {
                                setNotif({
                                    show: true,
                                    message: "Profile updated successfully!",
                                    type: "success",
                                });
                                sessionStorage.setItem("user", JSON.stringify(data.user));
                                setUser(data.user);
                                setIsEditing(false);
                            } else {
                                setNotif({
                                    show: true,
                                    message: "Update failed: " + (data.error || "Unknown error"),
                                    type: "error",
                                });
                            }
                        } catch (error) {
                            console.error("Update error:", error);
                            setNotif({
                                show: true,
                                message: "An error occurred while updating.",
                                type: "error",
                            });
                        }
                    }}
                >
                    Save Changes
                </Button>
              
            )}
            <Notif
                show={notif.show}
                message={notif.message}
                type={notif.type}
                onClose={() => setNotif((prev) => ({ ...prev, show: false }))}
            />

            {/* CANCEL SUBSCRIPTION POPUP */}
            {showCancelPopup && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
                    <div className="bg-white dark:bg-[#181c29] rounded-xl shadow-2xl p-8 w-full max-w-sm relative">
                        <button
                            className="absolute top-3 right-3 text-gray-400 hover:text-gray-700"
                            onClick={() => setShowCancelPopup(false)}
                            aria-label="Close"
                        >
                            ×
                        </button>
                        <h3 className="text-xl font-bold mb-4">Cancel Subscription</h3>
                        <p className="mb-6 text-gray-600 dark:text-gray-300">
                            Are you sure you want to cancel your subscription? All of your saved data will be deleted.
                        </p>
                        <div className="flex gap-3">
                            <Button
                                variant="outline"
                                className="flex-1"
                                onClick={() => setShowCancelPopup(false)}
                            >
                                No
                            </Button>
                            <Button
                                variant="destructive"
                                className="flex-1"
                                onClick={() => {
                                    setShowCancelPopup(false);
                                    setNotif({
                                        show: true,
                                        message: "Subscription cancelled successfully.",
                                        type: "success",
                                    });
                                }}
                            >
                                Yes
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            {/* PAUSE SUBSCRIPTION POPUP */}
            {showPausePopup && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
                    <div className="bg-white dark:bg-[#181c29] rounded-xl shadow-2xl p-8 w-full max-w-sm relative">
                    <button
                        className="absolute top-3 right-3 text-gray-400 hover:text-gray-700"
                        onClick={() => setShowPausePopup(false)}
                        aria-label="Close"
                    >
                        ×
                    </button>
                    <h3 className="text-xl font-bold mb-4">Pause Subscription</h3>
                    <div className="flex gap-3 mb-4">
                        {[30, 60, 90].map((d) => (
                        <Button
                            key={d}
                            variant={pauseDuration === d ? "default" : "outline"}
                            className="flex-1"
                            onClick={() => setPauseDuration(d as 30 | 60 | 90)}
                        >
                            {d} days
                        </Button>
                        ))}
                    </div>
                    {getBillingAmount(user.tier) && (
                        <p className="mb-2 text-gray-700 dark:text-gray-200">
                        Monthly billing will keep going on <span className="font-semibold">${getBillingAmount(user.tier)}</span> per month.
                        </p>
                    )}
                    <p className="mb-2 text-gray-500 dark:text-gray-400">
                        No credits will be taken during the pause period.
                    </p>
                    <Button
                        className="w-full mt-4"
                        onClick={() => {
                        // TODO: Implement pause logic here
                        setShowPausePopup(false);
                        setNotif({
                            show: true,
                            message: `Subscription paused for ${pauseDuration} days.`,
                            type: "success",
                        });
                        }}
                    >
                        Confirm Pause
                    </Button>
                    </div>
                </div>
                )}
        </div>
        
    );
}