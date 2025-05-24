/* eslint-disable @next/next/no-img-element */
import React from "react";
import { Button } from "@/components/ui/button";   // shadcn/ui
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardContent } from "@/components/ui/card";

export default function SettingsPage() {
    return (
        <div className="mx-auto max-w-4xl space-y-8 px-4 py-10">
            {/* PERSONAL INFORMATION */}
            <Card>
                <CardHeader>
                    <h2 className="text-lg font-semibold">Personal Information</h2>
                </CardHeader>

                <CardContent className="space-y-6">
                    {/* Avatar + Change button */}
                    <div className="flex items-center gap-6">
                        <img
                            src="https://i.pravatar.cc/80?img=1"
                            alt="User avatar"
                            className="h-20 w-20 rounded-full object-cover"
                        />
                        <Button variant="outline" size="sm">
                            Change
                        </Button>
                    </div>

                    {/* Name + Email grid */}
                    <div className="grid gap-6 md:grid-cols-2">
                        <div className="flex flex-col gap-1.5">
                            <Label htmlFor="name">Name</Label>
                            <Input id="name" placeholder="Your name" defaultValue="Praveen Juge" />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="you@example.com"
                                defaultValue="hello@praveenjuge.com"
                            />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* CHANGE PASSWORD */}
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

                        {/* full-width Save button on a new row */}
                        <Button className="md:col-span-3 w-full" type="submit">
                            Save Changes
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
