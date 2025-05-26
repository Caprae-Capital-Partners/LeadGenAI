"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL!;

export default function AuthPage() {
    const [isSignup, setIsSignup] = useState(false);
    const [formData, setFormData] = useState({
        username: "",
        email: "",
        company: "",
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
        const endpoint = isSignup ? "/auth/register" : "/auth/login";

        const payload = isSignup
            ? {
                username: formData.username,
                email: formData.email,
                company: formData.company,
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
                credentials: "include", // ⬅️ Important for session cookie
                body: JSON.stringify(payload),
            });

            const result = await res.json();
            if (!res.ok) throw new Error(result.message || "Something went wrong");

            // ✅ Store user info in sessionStorage
            if (result.user) {
                sessionStorage.setItem("user", JSON.stringify(result.user));
            }

            if (isSignup) {
                router.push("/subscription");
            } else {
                // Determine environment
                if (window.location.hostname === "localhost") {
                    router.push("/");
                } else {
                    window.location.href = "https://app.saasquatchleads.com/";
                }
            }
        } catch (err: any) {
            alert(err.message);
        }
    };
    
      


    return (
        <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
            <div className="w-full max-w-md bg-card text-card-foreground rounded-xl shadow-md border border-border">
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
                                <Label htmlFor="company">Company</Label>
                                <Input
                                    id="company"
                                    placeholder="Company (optional)"
                                    value={formData.company}
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
        </div>
    );
      
}