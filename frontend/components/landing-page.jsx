"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Play, CheckCircle } from "lucide-react"
import { submitLeadForm } from "@/lib/actions"
import { Card, CardContent } from "@/components/ui/card"

export function LandingPage() {
  const [formState, setFormState] = useState({
    name: "",
    email: "",
  })
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [visibleSections, setVisibleSections] = useState({
    logo: false,
    content: false,
  })

  useEffect(() => {
    // Trigger animations on load with slight delays for sequence
    const timer1 = setTimeout(() => setVisibleSections((prev) => ({ ...prev, logo: true })), 300)
    const timer2 = setTimeout(() => setVisibleSections((prev) => ({ ...prev, content: true })), 900)

    // Add ActiveCampaign form embed
    const existing = document.querySelector('script[src*="activehosted.com/f/embed.php"]');
    if (!existing) {
      const script = document.createElement("script");
      script.src = "https://capraecapital.activehosted.com/f/embed.php?id=1";
      script.charset = "utf-8";
      script.async = true;
      document.body.appendChild(script);

      // Add custom styles for the form
      const style = document.createElement('style');
      style.textContent = `
        #_form_1_ {
          background: transparent !important;
          border: none !important;
          padding: 0 !important;
          margin: 0 !important;
        }
        #_form_1_ ._form-title {
          font-size: 1.5rem !important;
          font-weight: 600 !important;
          color: #fff !important;
          margin-bottom: 1rem !important;
        }
        #_form_1_ input[type="text"],
        #_form_1_ input[type="email"] {
          background: #1A2438 !important;
          border: 1px solid #2A3A59 !important;
          color: #fff !important;
          padding: 0.75rem 1rem !important;
          border-radius: 0.5rem !important;
          transition: all 0.2s !important;
        }
        #_form_1_ input[type="text"]:focus,
        #_form_1_ input[type="email"]:focus {
          border-color: #4fd1c5 !important;
          box-shadow: 0 0 0 2px rgba(79, 209, 197, 0.2) !important;
        }
        #_form_1_ ._submit {
          background: linear-gradient(to right, #1bc290, #2ab58b) !important;
          border: none !important;
          padding: 0.75rem 1.5rem !important;
          border-radius: 0.5rem !important;
          font-weight: 600 !important;
          width: 100% !important;
          margin-top: 1rem !important;
          color: white !important;
          text-shadow: 0 0 3px rgba(0, 0, 0, 0.3) !important;
          box-shadow: 0 4px 8px rgba(27, 194, 144, 0.3) !important;
        }
        #_form_1_ ._submit:hover {
          transform: translateY(-1px) !important;
          box-shadow: 0 6px 12px rgba(27, 194, 144, 0.4) !important;
        }
        #_form_1_ label {
          color: #e2e8f0 !important;
          font-weight: 500 !important;
          margin-bottom: 0.5rem !important;
        }
      `;
      document.head.appendChild(style);
    }

    return () => {
      clearTimeout(timer1)
      clearTimeout(timer2)
      const form = document.querySelector("._form_1");
      if (form) form.innerHTML = "";
    }
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormState((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault(); // ← prevent default form behavior

    setIsSubmitting(true);

    const formData = new URLSearchParams();
    formData.append("entry.56744877", formState.name); // your name input field ID
    formData.append("entry.286187584", formState.email); // your email input field ID

    try {
      await fetch(
        "https://docs.google.com/forms/d/e/1FAIpQLSf85Jnq_BV87v-KslHd93JtHeUSdxA5JmNEXXZLin6F1Rni4g/formResponse",
        {
          method: "POST",
          mode: "no-cors",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: formData,
        }
      );

      setIsSuccess(true); // ✅ show the thank-you component
      setFormState({ name: "", email: "" }); // reset form
    } catch (err) {
      console.error("Submit error", err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  

  return (
    <div className="min-h-screen w-full overflow-auto relative flex flex-col justify-between">
      <div className="absolute top-8 right-10 z-50">
        <Button
          onClick={() =>
            (window.location.href = "https://app.saasquatchleads.com/auth")
          }
          className="px-7 py-3 text-base font-bold bg-yellow-400 text-black hover:bg-yellow-500 transition-all rounded-full shadow-lg leading-none flex items-center justify-center"
          style={{ height: "48px", minWidth: "120px" }}
        >
          Sign Up
        </Button>
      </div>

      {/* Enhanced gradient background */}
      <div className="fixed inset-0 z-0">
        {/* Main gradient background */}
        <div
          className="absolute inset-0 bg-[#030508]"
          style={{
            background: `
              radial-gradient(circle at 20% 20%, rgba(46, 139, 87, 0.08), transparent 40%),
              radial-gradient(circle at 80% 30%, rgba(99, 102, 241, 0.08), transparent 50%),
              radial-gradient(circle at 10% 60%, rgba(139, 92, 246, 0.05), transparent 40%),
              radial-gradient(circle at 90% 90%, rgba(46, 139, 87, 0.05), transparent 40%),
              linear-gradient(to bottom, #081528, #071020 30%, #050A14 60%, #030508 100%)
            `,
          }}
        />

        {/* Subtle animated glow */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background:
              "radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.2), transparent 70%)",
            animation: "pulse 15s infinite alternate",
          }}
        />

        {/* Subtle dot pattern overlay */}
        <div
          className="absolute inset-0 z-0 opacity-5"
          style={{
            backgroundImage: "radial-gradient(#ffffff 1px, transparent 1px)",
            backgroundSize: "33px 33px", // 10% larger
          }}
        />
      </div>

      <div className="relative z-10 flex flex-col h-full">
        {/* Top Section: Logo and Title */}
        <section className="pt-16 pb-8 flex flex-col items-center justify-center">
          {/* Logo + Tagline Section */}
          <div
            className={`w-full flex flex-col items-center justify-center transition-opacity duration-1000 ease-in-out ${
              visibleSections.logo ? "opacity-100" : "opacity-0"
            }`}
          >
            {/* Logo Container */}
            <div className="w-full max-w-[500px] px-4">
              <div className="relative w-full" style={{ aspectRatio: "1 / 1" }}>
                <Image
                  src="/images/logo_vertical.png"
                  alt="SaaSquatch Logo"
                  fill
                  className="object-contain"
                  sizes="(max-width: 768px) 70vw, 30vw"
                />
              </div>
            </div>

            {/* Tagline Text */}
            <div className="mt-3 text-center px-2">
              <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-gray-300 italic max-w-screen-md mx-auto">
                Powering 30+ Entrepreneurs, Searchers, and Operators generate
                1000s of leads weekly
              </p>
            </div>
          </div>

          {/* Divider */}
          <div className="w-full flex justify-center mt-12 mb-6">
            <div className="w-full max-w-7xl px-5 flex items-center">
              {/* Left line */}
              <div className="h-[2px] flex-grow bg-white/30 shadow-sm rounded-full opacity-45"></div>

              {/* Dot separator */}
              <div className="mx-5 w-6 h-6 flex items-center justify-center">
                <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center shadow-md">
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-400 shadow-inner"></div>
                </div>
              </div>

              {/* Right line */}
              <div className="h-[2px] flex-grow bg-white/30 shadow-sm rounded-full opacity-45"></div>
            </div>
          </div>
        </section>

        {/* Main Content Section: Video and Form side by side */}
        <section
          className={`w-full px-5 py-10 flex-grow transition-all duration-1000 ease-in-out ${
            visibleSections.content
              ? "opacity-100 transform-none"
              : "opacity-0 translate-y-10"
          }`}
        >
          <div className="w-full max-w-7xl mx-auto relative">
            <div className="flex flex-col lg:flex-row gap-8 lg:gap-24 items-center lg:items-stretch">
              {/* Coming Soon Text */}
              <div className="absolute -top-20 left-0 right-0 text-center">
                <div className="inline-block font-bold text-2xl md:text-4xl tracking-wide bg-gradient-to-r from-teal-400 to-teal-600 bg-clip-text text-transparent">
                  Transform Your Lead Generation
                </div>
              </div>

              {/* Video Section - Now 50% width */}
              <div className="w-full lg:w-1/2 relative">
                {/* Blurred logo background */}
                <div className="absolute inset-0 flex items-center justify-center overflow-hidden opacity-10 z-0">
                  <div className="w-[330px] h-[330px] relative transform rotate-12">
                    <Image
                      src="/images/saadquatch_logo.png"
                      alt=""
                      width={330}
                      height={330}
                      className="object-contain filter blur-xl"
                    />
                  </div>
                </div>

                {/* Features List */}
                <Card className="bg-[#1a1f2e]/50 backdrop-blur-sm border-gray-800 shadow-2xl relative z-10">
                  <CardContent className="p-8">
                    <ul className="space-y-8">
                      <li className="flex items-start">
                        <div className="flex-shrink-0 bg-teal-500/10 p-3 rounded-xl mr-4">
                          <svg className="h-6 w-6 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M8 17l4 4 4-4m0-5V3m-8 9a9 9 0 1118 0 9 9 0 01-18 0z" />
                          </svg>
                        </div>
                        <div>
                          <span className="font-semibold text-gray-100 text-lg">Scraping Leads</span>
                          <p className="text-gray-400 mt-1">
                            Instantly gather targeted company and contact data from public sources.
                          </p>
                        </div>
                      </li>

                      <li className="flex items-start">
                        <div className="flex-shrink-0 bg-teal-500/10 p-3 rounded-xl mr-4">
                          <svg className="h-6 w-6 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 1.343-3 3 0 1.657 1.343 3 3 3s3-1.343 3-3c0-1.657-1.343-3-3-3zm0 0V4m0 7v7m-7-7h14" />
                          </svg>
                        </div>
                        <div>
                          <span className="font-semibold text-gray-100 text-lg">Enrichment for Lead Details</span>
                          <p className="text-gray-400 mt-1">
                            Get enriched profiles: emails, phones, LinkedIn, industry, revenue, and more.
                          </p>
                        </div>
                      </li>

                      <li className="flex items-start">
                        <div className="flex-shrink-0 bg-teal-500/10 p-3 rounded-xl mr-4">
                          <svg className="h-6 w-6 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                        <div>
                          <span className="font-semibold text-gray-100 text-lg">Save & Export Leads</span>
                          <p className="text-gray-400 mt-1">
                            Save your leads to your dashboard and export to CSV or Excel for your workflow.
                          </p>
                        </div>
                      </li>

                      <li className="flex items-start">
                        <div className="flex-shrink-0 bg-teal-500/10 p-3 rounded-xl mr-4">
                          <svg className="h-6 w-6 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                          </svg>
                        </div>
                        <div>
                          <span className="font-semibold text-gray-100 text-lg">Enterprise Outreach Tools</span>
                          <p className="text-gray-400 mt-1">
                            Cold call or email directly from the platform (for enterprise members).
                          </p>
                        </div>
                      </li>
                    </ul>
                  </CardContent>
                </Card>
              </div>

              {/* Form Section - Now 50% width */}
              <div className="w-full lg:w-1/2 relative flex items-center">
                <div className="w-full relative z-10">
                  <Card className="bg-[#121A2A]/80 backdrop-blur-sm border-[#1E2A40]/40 shadow-2xl hover:shadow-teal-500/5 transition-all duration-300">
                    <CardContent className="p-8">
                      <div className="mb-6">
                        <h2 className="text-2xl font-bold text-yellow-400 mb-2">Get Early Access</h2>
                        <p className="text-gray-400">
                          Join the waitlist and be the first to experience our powerful B2B lead generation platform.
                        </p>
                      </div>
                      
                      <div className="_form_1"></div>
                      
                      <div className="mt-6 flex items-center space-x-3 text-sm text-gray-400">
                        <svg className="h-5 w-5 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        <span>Your information is secure and will never be shared.</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
      {/* Top-right blurry background image */}
      <div className="fixed top-0 right-0 z-0 w-[600px] h-[1200px] overflow-hidden pointer-events-none">
        <img
          className="w-full h-full object-contain opacity-10 scale-100"
          style={{ filter: "blur(5px)" }} // equivalent to ~1.9xl
          src="/images/bg_logo.png"
          alt="Blurry Background"
        />
      </div>
    </div>
  );
}
