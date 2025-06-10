"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { loadStripe } from "@stripe/stripe-js";

type Plan = {
    id: string;
    plan_name: string;
    price: number | string;
    lead_quota: number | string;
    cost_per_lead?: number | string;
    description?: string;
    has_ai_features?: boolean;
    features: string[] | string;
    initial_credits?: number | string;
    style?: string;
    recommended?: boolean;
    link?: string;
    isAnnual: boolean;
};

const STRIPE = process.env.NEXT_PUBLIC_STRIPE_CODE!;
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL;
const DATABASE_URL_NOAPI = DATABASE_URL?.replace(/\/api\/?$/, "");

export default function SubscriptionPage() {
    const [plans, setPlans] = useState<Plan[]>([]);
    const [isAnnual, setIsAnnual] = useState(false);
    const [outreachPlan, setOutreachPlan] = useState<Plan | null>(null);
    const planOrder = [
        "bronze",
        "silver",
        "gold",
        "platinum",
        "enterprise",         // monthly
        "bronze_annual",
        "silver_annual",
        "gold_annual",
        "platinum_annual",
        "enterprise_annual"   // annual
    ];

    useEffect(() => {
        const fetchUpgradePlans = async () => {
            try {
                const outreachId = "pro_call_outreach";

                const cached = localStorage.getItem("upgradePlans");
                if (cached) {
                    const parsed = JSON.parse(cached);
                    setPlans(parsed);

                    const outreachRaw = localStorage.getItem("outreachPlan");
                    if (outreachRaw) {
                        setOutreachPlan(JSON.parse(outreachRaw));
                    }
                    return;
                }

                const res = await fetch(`${DATABASE_URL}/plans/upgrade`, {
                    method: "GET",
                    credentials: "include",
                });

                const data = await res.json();
                const userRole = data.user_role?.toLowerCase() || "";
                const isStudent = userRole === "student";

                // Extract student plans
                const studentPlans = isStudent
                    ? (data.plans || [])
                        .filter((plan: any) =>
                            plan.plan_name.toLowerCase().includes("student")
                        )
                        .map((plan: any) => ({
                            id: plan.plan_name.toLowerCase().replace(/\s+/g, "_"),
                            plan_name: plan.plan_name,
                            price: plan.monthly_price,
                            lead_quota: plan.monthly_lead_quota,
                            features: Array.isArray(plan.features)
                                ? plan.features
                                : JSON.parse(plan.features || "[]"),
                            isAnnual: false,
                        }))
                    : [];

                const allPlans: Plan[] = [];
                (data.plans || []).forEach((plan: any) => {
                    const rawPlanName = plan.plan_name.toLowerCase();
                    const planId = rawPlanName.replace(/\s+/g, "_");
                    const isEnterprise = rawPlanName.includes("enterprise");
                    const isAnnualPlan = planId.includes("annual");

                    const baseParsedPlan = {
                        id: planId,
                        plan_name: plan.plan_name,
                        cost_per_lead: plan.cost_per_lead,
                        description: plan.description,
                        has_ai_features: plan.has_ai_features,
                        features: Array.isArray(plan.features)
                            ? plan.features
                            : JSON.parse(plan.features || "[]"),
                        initial_credits: plan.initial_credits,
                        style: rawPlanName.includes("gold")
                            ? "default"
                            : rawPlanName.includes("free")
                                ? "secondary"
                                : "outline",
                        recommended: plan.recommended ?? rawPlanName.includes("gold"),
                        link: plan.link || (isEnterprise ? "https://www.saasquatchleads.com/" : undefined),
                    };

                    if (planId === outreachId) {
                        const outreachPlanParsed = {
                            ...baseParsedPlan,
                            id: planId,
                            price: plan.monthly_price,
                            lead_quota: plan.monthly_lead_quota,
                            isAnnual: false,
                        };

                        setOutreachPlan(outreachPlanParsed);
                        localStorage.setItem("outreachPlan", JSON.stringify(outreachPlanParsed));
                    } else if (isEnterprise) {
                        allPlans.push({
                            ...baseParsedPlan,
                            id: "enterprise",
                            price: plan.monthly_price,
                            lead_quota: plan.monthly_lead_quota,
                            isAnnual: false,
                        });

                        allPlans.push({
                            ...baseParsedPlan,
                            id: "enterprise_annual",
                            price: plan.annual_price,
                            lead_quota: plan.annual_lead_quota,
                            isAnnual: true,
                        });
                    } else {
                        allPlans.push({
                            ...baseParsedPlan,
                            id: planId,
                            price: isAnnualPlan ? plan.annual_price : plan.monthly_price,
                            lead_quota: isAnnualPlan ? plan.annual_lead_quota : plan.monthly_lead_quota,
                            isAnnual: isAnnualPlan,
                        });
                    }
                });

                const sortedPlans = allPlans.sort(
                    (a, b) =>
                        planOrder.indexOf(a.id.toLowerCase()) -
                        planOrder.indexOf(b.id.toLowerCase())
                );

                const combined = [...sortedPlans, ...studentPlans];
                setPlans(combined);
                localStorage.setItem("upgradePlans", JSON.stringify(combined));
            } catch (err) {
                console.error("❌ Failed to fetch upgrade plans:", err);
            }
        };

        fetchUpgradePlans();
    }, []);




    const handleSelectPlan = async (planId: string) => {
        if (planId === "free") {
            window.location.href = "/";
            return;
        }

        try {
            const res = await fetch(`${DATABASE_URL_NOAPI}/create-checkout-session`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
                body: JSON.stringify({ plan_type: planId }),
            });

            const data = await res.json();
            if (res.ok && data.sessionId) {
                const stripe = await loadStripe(STRIPE);
                if (stripe) {
                    console.log("Stripe Mode:", process.env.STRIPE_MODE);
                    console.log("Session ID:", data.sessionId);
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


                {/* Subscription Plans Section */}

                {/* Top row: First 3 plans */}
                <div className="flex flex-wrap justify-center gap-8 mb-8">
                    {plans
                        .filter((plan) => plan.isAnnual === isAnnual)
                        .slice(0, 3)
                        .map((plan) => {
                            const isComingSoon = ["gold", "gold_annual", "platinum", "platinum_annual"].includes(plan.id);

                            const hoverTextColor =
                                plan.id.includes("gold")
                                    ? "group-hover:text-yellow-500"
                                    : plan.id.includes("silver")
                                        ? "group-hover:text-gray-500"
                                        : plan.id.includes("platinum")
                                            ? "group-hover:text-purple-500"
                                            : plan.id.includes("bronze")
                                                ? "group-hover:text-amber-500"
                                                : plan.id.includes("enterprise")
                                                    ? "group-hover:text-blue-500"
                                                    : "group-hover:text-foreground";

                            const buttonHoverColor =
                                plan.id.includes("gold")
                                    ? "bg-yellow-300 text-black"
                                    : plan.id.includes("silver")
                                        ? "bg-gray-300 text-black"
                                        : plan.id.includes("platinum")
                                            ? "bg-purple-400 text-black"
                                            : plan.id.includes("bronze")
                                                ? "bg-amber-200 text-black"
                                                : plan.id.includes("enterprise")
                                                    ? "bg-blue-200 text-black"
                                                    : "bg-muted text-foreground";

                            const price = typeof plan.price === "number"
                                ? `$${plan.price} /${isAnnual ? "year" : "month"}`
                                : plan.price;

                            const quota = typeof plan.lead_quota === "number"
                                ? `${plan.lead_quota} leads/${isAnnual ? "year" : "month"}`
                                : plan.lead_quota;

                            return (
                                <div
                                    key={plan.id}
                                    className="w-full max-w-sm group relative rounded-[28px] overflow-hidden flex flex-col justify-between min-h-[300px] border-2 border-border bg-muted transition-all duration-300 hover:shadow-2xl hover:scale-[1.03]"
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
                                                        {plan.plan_name.replace(/_Annual/i, "")}
                                                    </Button>
                                                </>
                                            ) : (
                                                <Button
                                                    onClick={() => {
                                                        if (plan.id === "free") {
                                                            window.location.href = "/";
                                                        } else if (plan.id === "enterprise") {
                                                            window.location.href = "/contact";
                                                        } else {
                                                            handleSelectPlan(plan.id);
                                                        }
                                                    }}
                                                    className={`w-full rounded-full font-semibold transition-all duration-300 ${buttonHoverColor}`}
                                                >
                                                    {plan.plan_name.replace(/_Annual/i, "")}
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                </div>

                {/* Bottom row: Last 2 plans (centered) */}
                <div className="flex flex-col sm:flex-row justify-center gap-8">
                    {plans
                        .filter((plan) => plan.isAnnual === isAnnual)
                        .slice(3)
                        .map((plan) => {
                            const isComingSoon = ["gold", "gold_annual", "platinum", "platinum_annual"].includes(plan.id);

                            const hoverTextColor =
                                plan.id.includes("gold")
                                    ? "group-hover:text-yellow-500"
                                    : plan.id.includes("silver")
                                        ? "group-hover:text-gray-500"
                                        : plan.id.includes("platinum")
                                            ? "group-hover:text-purple-500"
                                            : plan.id.includes("bronze")
                                                ? "group-hover:text-amber-500"
                                                : plan.id.includes("enterprise")
                                                    ? "group-hover:text-blue-500"
                                                    : "group-hover:text-foreground";

                            const buttonHoverColor =
                                plan.id.includes("gold")
                                    ? "bg-yellow-300 text-black"
                                    : plan.id.includes("silver")
                                        ? "bg-gray-300 text-black"
                                        : plan.id.includes("platinum")
                                            ? "bg-purple-400 text-black"
                                            : plan.id.includes("bronze")
                                                ? "bg-amber-200 text-black"
                                                : plan.id.includes("enterprise")
                                                    ? "bg-blue-200 text-black"
                                                    : "bg-muted text-foreground";

                            const price = typeof plan.price === "number"
                                ? `$${plan.price} /${isAnnual ? "year" : "month"}`
                                : plan.price;

                            const quota = typeof plan.lead_quota === "number"
                                ? `${plan.lead_quota} leads/${isAnnual ? "year" : "month"}`
                                : plan.lead_quota;

                            return (
                                <div
                                    key={plan.id}
                                    className="w-full max-w-sm group relative rounded-[28px] overflow-hidden flex flex-col justify-between min-h-[300px] border-2 border-border bg-muted transition-all duration-300 hover:shadow-2xl hover:scale-[1.03]"
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
                                                        {plan.plan_name.replace(/_Annual/i, "")}
                                                    </Button>
                                                </>
                                            ) : (
                                                <Button
                                                    onClick={() => {
                                                        if (plan.id === "free") {
                                                            window.location.href = "/";
                                                        } else if (plan.id === "enterprise") {
                                                            window.location.href = "/contact";
                                                        } else {
                                                            handleSelectPlan(plan.id);
                                                        }
                                                    }}
                                                    className={`w-full rounded-full font-semibold transition-all duration-300 ${buttonHoverColor}`}
                                                >
                                                    {plan.plan_name.replace(/_Annual/i, "")}
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                </div>


                {/* Outreach Plan Section */}
                {outreachPlan && (
                    <div className="group mx-auto w-full max-w-2xl border-2 border-border rounded-[28px] bg-muted px-8 py-10 shadow-md text-center space-y-6 mb-16 transition-all duration-300 hover:shadow-2xl hover:scale-[1.03]">
                        <h3 className="text-3xl font-extrabold group-hover:tracking-wide transition-all duration-300">
                            ${outreachPlan.price} for 25 hours
                        </h3>

                        <ul className="list-disc list-inside text-base text-foreground text-left max-w-md mx-auto space-y-1">
                            {(Array.isArray(outreachPlan.features) ? outreachPlan.features : []).map((feat, i) => (
                                <li key={i}>{feat}</li>
                            ))}
                        </ul>

                        <Button
                            className="rounded-full px-6 py-2 text-base font-semibold"
                            onClick={() => window.location.href = "/contact"}
                        >
                            {outreachPlan.plan_name}
                        </Button>
                    </div>
                )}






                {/* Continue Link */}
                <div className="text-center">
                    <a href="/">
                        <Button> Continue to Dashboard</Button>
                    </a>
                </div>
            </div>
        </div>
    );
}      