"use client";
/* eslint-disable @next/next/no-img-element */
import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardContent } from "@/components/ui/card";

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
    linkedin?: string;
};

export default function SettingsPage({ isEditing, setIsEditing }: SettingsPageProps) {
    const [user, setUser] = useState<User | null>(null);
    const [username, setUsername] = useState("");
    const [linkedin, setLinkedin] = useState("");
    const [email, setEmail] = useState("");


    useEffect(() => {
        const sessionUser = sessionStorage.getItem("user");
        if (sessionUser) {
            const parsedUser: User = JSON.parse(sessionUser);
            setUser(parsedUser);
            setUsername(parsedUser.username);
            setEmail(parsedUser.email);
            setLinkedin(parsedUser.linkedin ?? "");
        }
    }, []);

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
                    <Button
                        size="sm"
                        onClick={() => setIsEditing((prev: boolean) => !prev)}
                        className="text-sm"
                    >
                        {isEditing ? "Cancel" : "Edit Profile"}
                    </Button>
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
                                <Input id="oldPassword" type="password" placeholder="Enter your password" />
                            </div>

                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor="newPassword">New Password</Label>
                                <Input id="newPassword" type="password" placeholder="Enter your password" />
                            </div>

                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor="confirmPassword">New Password Again</Label>
                                <Input id="confirmPassword" type="password" placeholder="Enter your password" />
                            </div>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* SAVE BUTTON (Only in edit mode) */}
            {isEditing && (
                <Button className="md:col-span-3 w-full" type="submit">
                    Save Changes
                </Button>
            )}
        </div>
    );
}
