"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { loadStripe } from "@stripe/stripe-js";

type Plan = {
    plan_name: string;
    monthly_price: number | string;
    annual_price: number | string;
    monthly_lead_quota: number | string;
    annual_lead_quota: number | string;
    features: string[] | string;
    id: string;
    description?: string;
    recommended?: boolean;
    style?: string;
    link?: string;
};

export default function SubscriptionPage() {
    const [plans, setPlans] = useState<Plan[]>([]);
    const [isAnnual, setIsAnnual] = useState(false);

    useEffect(() => {
        const fetchPlans = async () => {
            try {
                const res = await fetch("https://data.capraeleadseekers.site/api/plans/all", {
                    method: "GET",
                    credentials: "include",
                });
                const data = await res.json();

                const plansWithIds = data.plans.map((plan: any) => ({
                    ...plan,
                    id: plan.plan_name.toLowerCase(),
                    features: Array.isArray(plan.features)
                        ? plan.features
                        : JSON.parse(plan.features || "[]"),
                    style:
                        plan.plan_name === "Gold"
                            ? "default"
                            : plan.plan_name === "Free"
                                ? "secondary"
                                : "outline",
                    recommended: plan.plan_name === "Gold",
                    link:
                        plan.plan_name === "Enterprise"
                            ? "https://www.saasquatchleads.com/"
                            : undefined,
                }));

                setPlans(plansWithIds);
            } catch (err) {
                console.error("❌ Failed to fetch plans:", err);
            }
        };

        fetchPlans();
    }, []);

    const handleSelectPlan = async (planId: string) => {
        if (planId === "free") {
            window.location.href = "https://app.saasquatchleads.com/";
            return;
        }

        try {
            const res = await fetch("https://data.capraeleadseekers.site/create-checkout-session", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
                body: JSON.stringify({ plan_type: planId }),
            });

            const data = await res.json();
            if (res.ok && data.sessionId) {
                const stripe = await loadStripe(
                    "pk_test_51RNp9cFS9KhotLbMiJM95rAjhuxjTwgjPpRLObOd1ghpwZHwZHOLDIVuxbp4wfXCJBHSLtZhoL99CdaTpOpWAY1L00GcymT5Xj"
                );
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

    
    return (
        <div className="animate-fade-in-down min-h-screen pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-background text-foreground">
            <div className="max-w-7xl mx-auto space-y-16">
                {/* Header */}
                <div className="text-center">
                    <h2 className="text-5xl font-extrabold tracking-tight">Upgrade Your Plan</h2>
                    <p className="text-lg text-muted-foreground mt-4 max-w-2xl mx-auto">
                        Welcome to LeadGen! Choose a plan to unlock more leads and features, or continue with the Free plan.
                    </p>
                </div>

                {/* Toggle */}
                <div className="flex justify-center items-center gap-4">
                    <span className="text-sm font-medium">Monthly</span>
                    <label className="inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            className="sr-only"
                            checked={isAnnual}
                            onChange={() => setIsAnnual((prev) => !prev)}
                        />
                        <div className="w-11 h-6 bg-gray-200 rounded-full shadow-inner dark:bg-gray-700">
                            <div
                                className={`w-5 h-5 bg-primary rounded-full transform transition-transform ${isAnnual ? "translate-x-5" : "translate-x-1"
                                    }`}
                            />
                        </div>
                    </label>
                    <span className="text-sm font-medium">Annual</span>
                </div>

                {/* Plans */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                    {plans.map((plan) => {
                        const isComingSoon = plan.id === "silver" || plan.id === "gold" || plan.id === "platinum";

                        const hoverTextColor =
                            plan.id === "gold"
                                ? "group-hover:text-yellow-500"
                                : plan.id === "silver"
                                    ? "group-hover:text-gray-500"
                                    : plan.id === "platinum"
                                        ? "group-hover:text-purple-500"
                                        : plan.id === "bronze"
                                            ? "group-hover:text-amber-500"
                                            : plan.id === "enterprise"
                                                ? "group-hover:text-blue-500"
                                                : "group-hover:text-foreground";

                        const buttonHoverColor =
                            plan.id === "gold"
                                ? "bg-yellow-300 text-black"
                                : plan.id === "silver"
                                    ? "bg-gray-300 text-black"
                                    : plan.id === "platinum"
                                        ? "bg-purple-400 text-black"
                                        : plan.id === "bronze"
                                            ? "bg-amber-200 text-black"
                                            : plan.id === "enterprise"
                                                ? "bg-blue-200 text-black"
                                                : "bg-muted text-foreground";

                        const price =
                            isAnnual && typeof plan.annual_price === "number"
                                ? `$${plan.annual_price} /year`
                                : typeof plan.monthly_price === "number"
                                    ? `$${plan.monthly_price} /month`
                                    : plan.monthly_price;

                        const quota =
                            isAnnual && typeof plan.annual_lead_quota === "number"
                                ? `${plan.annual_lead_quota} leads/year`
                                : typeof plan.monthly_lead_quota === "number"
                                    ? `${plan.monthly_lead_quota} leads/month`
                                    : plan.monthly_lead_quota;

                        return (
                            <div
                                key={plan.id}
                                className="group relative rounded-[28px] overflow-hidden flex flex-col justify-between min-h-[300px] border-2 border-border bg-muted transition-all duration-300 hover:shadow-2xl hover:scale-[1.03]"
                            >
                                <div
                                    className={`text-center text-2xl font-bold py-4 border-y border-border bg-muted transition-all duration-300 group-hover:text-3xl group-hover:tracking-wide ${hoverTextColor}`}
                                >
                                    {price}
                                </div>

                                <div className="flex-1 p-6 flex flex-col justify-between">
                                    <div className="space-y-4">
                                        <p className="text-base font-semibold text-primary">• {quota}</p>
                                        {(Array.isArray(plan.features) ? plan.features : []).map((feat, i) => (
                                            <p
                                                key={i}
                                                className="text-base font-medium transition-colors duration-300 group-hover:text-foreground"
                                            >
                                                • {feat}
                                            </p>
                                        ))}
                                    </div>

                                    <div className="mt-8 text-center">
                                        {isComingSoon ? (
                                            <>
                                                <p className="text-xs text-muted-foreground mb-2 italic">Coming Soon</p>
                                                <Button
                                                    disabled
                                                    className={`w-full rounded-full font-semibold opacity-50 cursor-not-allowed ${buttonHoverColor}`}
                                                >
                                                    {plan.plan_name}
                                                </Button>
                                            </>
                                        ) : (
                                            <Button
                                                onClick={() =>
                                                    plan.id === "free"
                                                        ? (window.location.href = "https://app.saasquatchleads.com/")
                                                        : handleSelectPlan(plan.id)
                                                }
                                                className={`w-full rounded-full font-semibold transition-all duration-300 ${buttonHoverColor}`}
                                            >
                                                {plan.plan_name}
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Continue Link */}
                <div className="text-center">
                    <a href="https://app.saasquatchleads.com/">
                        <Button> Continue to Dashboard (Free Plan)</Button>
                    </a>
                </div>
            </div>
        </div>
    );
}      