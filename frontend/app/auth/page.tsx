"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import Notif from "@/components/ui/notif";


const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL!;

export default function AuthPage() {
    const [notif, setNotif] = useState({
        show: false,
        message: "",
        type: "success" as "success" | "error" | "info",
    });

    const showNotification = (message: string, type: "success" | "error" | "info" = "success") => {
        setNotif({ show: true, message, type });
        setTimeout(() => {
            setNotif(prev => ({ ...prev, show: false }));
        }, 3500);
      };
      
    const [isSignup, setIsSignup] = useState(false);
    const [formData, setFormData] = useState({
        username: "",
        email: "",
        linkedin: "",
        password: "",
        confirmPassword: "",
        gdpr: false,
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { id, value, type, checked } = e.target;
        setFormData((prev) => ({
            ...prev,
            [id]: type === "checkbox" ? checked : value,
        }));
    };

    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (isSignup) {
            if (!formData.username.trim()) {
                alert("Username is required.");
                return;
            }
            if (!formData.email.trim()) {
                alert("Email is required.");
                return;
            }
            if (formData.password !== formData.confirmPassword) {
                alert("Passwords do not match.");
                return;
            }
        }

        const endpoint = isSignup ? "/auth/register" : "/auth/login";

        const payload = isSignup
            ? {
                username: formData.username,
                email: formData.email,
                linkedin: formData.linkedin,
                password: formData.password,
                confirm_password: formData.confirmPassword,
                gdpr_accept: formData.gdpr,
            }
            : {
                email: formData.email,
                password: formData.password,
            };

        try {
            const res = await fetch(`${DATABASE_URL}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(payload),
            });

            const result = await res.json();
            if (!res.ok) throw new Error(result.message || "Something went wrong");

            if (result.user) {
                sessionStorage.setItem("user", JSON.stringify(result.user));

                if (isSignup) {
                    showNotification("Account successfully created!");
                    setTimeout(() => {
                        router.push("/subscription");
                    }, 100); // small delay to allow notification to render
                } else {
                    showNotification("Successfully signed in!");
                    setTimeout(() => {
                        if (window.location.hostname === "localhost") {
                            router.push("/");
                        } else {
                            window.location.href = "https://app.saasquatchleads.com/";
                        }
                    }, 100); // small delay to allow notification to render
                }
            }              
        } catch (err: any) {
            alert(err.message);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background text-foreground flex-col">
            <img
                src="/images/logo_horizontal.png"
                alt="SaaSquatch Leads Logo"
                className="w-96 mx-auto mb-6"
                />
            <div className="w-full max-w-md bg-card text-card-foreground rounded-xl shadow-md border-8 border-border">
                <div className="flex">
                    <button
                        className={`w-1/2 py-3 text-sm font-semibold transition-colors ${!isSignup
                                ? "bg-background text-foreground border-b-2 border-primary"
                                : "bg-muted text-muted-foreground"
                            }`}
                        onClick={() => setIsSignup(false)}
                    >
                        Sign In
                    </button>
                    <button
                        className={`w-1/2 py-3 text-sm font-semibold transition-colors ${isSignup
                                ? "bg-background text-foreground border-b-2 border-primary"
                                : "bg-muted text-muted-foreground"
                            }`}
                        onClick={() => setIsSignup(true)}
                    >
                        Sign Up
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    <form className="space-y-4" onSubmit={handleSubmit}>
                        {isSignup && (
                            <div>
                                <Label htmlFor="username">Username</Label>
                                <Input
                                    id="username"
                                    placeholder="Username"
                                    required
                                    value={formData.username}
                                    onChange={handleChange}
                                />
                            </div>
                        )}

                        <div>
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="Email"
                                required
                                value={formData.email}
                                onChange={handleChange}
                            />
                        </div>

                        {isSignup && (
                            <div>
                                <Label htmlFor="linkedin">LinkedIn Profile (Optional)</Label>
                                <Input
                                    id="linkedin"
                                    type="url"
                                    placeholder="https://linkedin.com/in/your-profile"
                                    value={formData.linkedin}
                                    onChange={handleChange}
                                />
                            </div>
                        )}

                        <div>
                            <Label htmlFor="password">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                placeholder="Password"
                                required
                                value={formData.password}
                                onChange={handleChange}
                            />
                        </div>

                        {isSignup && (
                            <div>
                                <Label htmlFor="confirmPassword">Confirm Password</Label>
                                <Input
                                    id="confirmPassword"
                                    type="password"
                                    placeholder="Repeat password"
                                    required
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                />
                            </div>
                        )}

                        {isSignup && (
                            <div className="flex items-start space-x-2 text-sm">
                                <input
                                    type="checkbox"
                                    id="gdpr"
                                    required
                                    checked={formData.gdpr}
                                    onChange={handleChange}
                                    className="mt-1"
                                />
                                <label htmlFor="gdpr" className="text-muted-foreground">
                                    I accept the{" "}
                                    <a href="#" className="text-primary underline">
                                        terms and conditions
                                    </a>{" "}
                                    and the{" "}
                                    <a href="#" className="text-primary underline">
                                        privacy policy
                                    </a>
                                    .
                                </label>
                            </div>
                        )}

                        <Button type="submit" className="w-full mt-2">
                            {isSignup ? "Sign Up" : "Sign In"}
                        </Button>
                    </form>
                </div>
            </div>
            <Notif
                show={notif.show}
                message={notif.message}
                type={notif.type}
                onClose={() => setNotif(prev => ({ ...prev, show: false }))}
            />
        </div>
    );
}
