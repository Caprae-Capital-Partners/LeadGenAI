// app/subscription/page.tsx
"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { loadStripe } from '@stripe/stripe-js';

const plans = [
    {
        name: "Free",
        price: "$0/month",
        annualPrice: "$0/year",
        features: [
            "60 Credits/Year (5/month)",
            "$0 Cost/Credit",
            "Phase 1 Scraper Only",
            "(No enrichment, no contact details)"
        ],
        style: "secondary",
        id: "free"
    },
    {
        name: "Bronze",
        price: "$19/month",
        annualPrice: "$199/year",
        features: [
            "600 Credits/Year (50/month)",
            "$0.333 Cost/Credit",
            "Basic Filters",
            "CSV Export"
        ],
        style: "outline",
        id: "bronze"
    },
    {
        name: "Silver",
        price: "$49/month",
        annualPrice: "$499/year",
        features: [
            "1,500 Credits/Year (125/month)",
            "$0.333 Cost/Credit",
            "Phone Numbers",
            "Advanced Features"
        ],
        style: "outline",
        id: "silver"
    },
    {
        name: "Gold",
        price: "$99/month",
        annualPrice: "$999/year",
        features: [
            "3,500 Credits/Year (292/month)",
            "$0.285 Cost/Credit",
            "Email Writing AI",
            "Priority Support"
        ],
        style: "default",
        id: "gold",
        recommended: true
    },
    {
        name: "Platinum",
        price: "$199/month",
        annualPrice: "$1,999/year",
        features: [
            "Unlimited Credits",
            "~ Cost/Credit",
            "Custom Workflows",
            "Priority Support"
        ],
        style: "outline",
        id: "platinum"
    },
    {
        name: "Enterprise",
        price: "Custom Pricing",
        annualPrice: "Custom",
        features: [
            "Custom Credits/Year",
            "Custom Cost/Credit",
            "Tailored Features"
        ],
        style: "outline",
        id: "enterprise",
        link: "https://www.saasquatchleads.com/"
    }
]
  

export default function SubscriptionPage() {
    const handleSelectPlan = async (planId: string) => {
        if (planId === "free") {
            window.location.href = "https://app.saasquatchleads.com/";
            return;
        }

        try {
            const res = await fetch("https://data.capraeleadseekers.site/create-checkout-session", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "include",
                body: JSON.stringify({ plan_type: planId }),
            });

            const data = await res.json();
            if (res.ok && data.sessionId) {
                const stripe = await loadStripe("pk_test_51RNp9cFS9KhotLbMiJM95rAjhuxjTwgjPpRLObOd1ghpwZHwZHOLDIVuxbp4wfXCJBHSLtZhoL99CdaTpOpWAY1L00GcymT5Xj");
                if (stripe) {
                    await stripe.redirectToCheckout({ sessionId: data.sessionId });
                } else {
                    alert("Stripe.js failed to load.");
                }
            } else {
                alert(data.error || "Failed to create checkout session");
            }
        } catch (err) {
            console.error("Error creating checkout session:", err);
            alert("Could not initiate payment. Try again later.");
        }
    };

    useEffect(() => {
        const timeout = setTimeout(() => {
            document.querySelectorAll(".success-message").forEach((msg) => {
                (msg as HTMLElement).style.opacity = "0";
                setTimeout(() => {
                    (msg as HTMLElement).style.display = "none";
                }, 500);
            });
        }, 5000);
        return () => clearTimeout(timeout);
    }, []);

    return (
        <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 bg-background text-foreground">
            <div className="max-w-5xl mx-auto space-y-6">
                <div className="text-center">
                    <h2 className="text-2xl font-bold">Upgrade Your Plan</h2>
                    <p className="text-muted-foreground">
                        Welcome to LeadGen! Choose a plan to unlock more leads and features,
                        or continue with the Free plan.
                    </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {plans.map((plan) => (
                        <div
                            key={plan.id}
                            className={`rounded-xl border p-6 shadow-sm relative ${plan.recommended ? "border-primary" : ""
                                }`}
                        >
                            {plan.recommended && (
                                <div className="absolute top-0 left-0 right-0 text-white bg-primary text-center text-xs py-1 rounded-t-xl">
                                    Recommended
                                </div>
                            )}
                            <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
                                {plan.name}
                                {(plan.id === "silver" || plan.id === "gold" || plan.id === "platinum") && (
                                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full">
                                        Coming Soon
                                    </span>
                                )}
                            </h3>
                            <p className="text-sm text-muted-foreground mb-4">{plan.price}</p>
                            <div className="space-y-1 text-sm mb-4">
                                {plan.features.map((feat, i) => (
                                    <p key={i}>{feat}</p>
                                ))}
                            </div>
                            {plan.link ? (
                                <a href={plan.link} target="_blank" rel="noopener noreferrer">
                                    <Button
                                        variant={plan.style as any}
                                        className="w-full"
                                        onClick={() => handleSelectPlan(plan.id)}
                                    >
                                        {plan.id === "free" ? "Continue with Free" : `Choose ${plan.name}`}
                                    </Button>
                                </a>
                            ) : (
                                <Button
                                    variant={plan.style as any}
                                    className="w-full"
                                    onClick={() =>
                                        plan.id === "free"
                                            ? (window.location.href = "https://app.saasquatchleads.com/")
                                            : handleSelectPlan(plan.id)
                                    }
                                >
                                    {plan.id === "free" ? "Continue with Free" : `Choose ${plan.name}`}
                                </Button>
                            )}

                        </div>
                    ))}
                </div>

                <div className="text-center mt-6">
                    <a href="https://app.saasquatchleads.com/">
                        <Button variant="secondary">Continue to Dashboard (Free Plan)</Button>
                    </a>
                </div>
            </div>
        </div>
    );
}