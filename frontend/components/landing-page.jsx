"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Play, CheckCircle } from "lucide-react"
import { submitLeadForm } from "@/lib/actions"

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

    return () => {
      clearTimeout(timer1)
      clearTimeout(timer2)
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
                <div
                  className="inline-block font-bold uppercase text-2xl md:text-4xl tracking-wide"
                  style={{ color: "rgba(240 , 210, 120, 1)" }}
                >
                  COMING SOON
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

                <div
                  className="w-full h-[400px] md:h-[500px] bg-[#070D1A]/90 overflow-hidden shadow-[0_17px_39px_rgba(0,0,0,0.7)] relative border border-[#1E2A40]/40 rounded-xl"
                  style={{ aspectRatio: "auto" }}
                >
                  {!isPlaying && (
                    <>
                      <div className="absolute inset-0 flex items-center justify-center z-10">
                        <Button
                          size="icon"
                          className="h-[70px] w-[70px] rounded-full bg-yellow-400 hover:bg-yellow-500 shadow-lg flex items-center justify-center"
                          onClick={() => setIsPlaying(true)}
                        >
                          <Play className="h-9 w-9 text-black" />
                        </Button>
                      </div>
                      <Image
                        src="/images/thumbnail_promo.png"
                        alt="SaaSquatch Leads Thumbnail"
                        width={1408}
                        height={792}
                        className="object-cover w-full h-full opacity-50 z-0"
                      />
                    </>
                  )}
                  {isPlaying && (
                    <iframe
                      className="absolute inset-0 w-full h-full rounded-xl"
                      src="https://www.youtube.com/embed/BanHjKMRRPE?autoplay=1"
                      title="SaaSquatch Leads Demo Video"
                      frameBorder="0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  )}
                </div>
              </div>

              {/* Form Section - Now 50% width */}
              <div className="w-full lg:w-1/2 relative flex items-center">
                {/* Blurred logo background
                <div className="absolute top-0 right-0 w-[300px] h-[300px] z-0">
                  <img
                    src="/images/bg_logo.png" // Replace with your image
                    alt="Decor"
                    className="w-full h-full object-contain blur-1.9xl opacity-90 scale-125"
                  />
                </div> */}

                <div className="w-full relative z-10">
                  {isSuccess ? (
                    <div className="text-center py-5 bg-[#121A2A]/80 rounded-xl border border-[#1E2A40]/40 shadow-xl p-5 backdrop-blur-sm">
                      <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-[#6366F1]/10">
                        <CheckCircle className="h-6 w-6 text-[#6366F1]" />
                      </div>
                      <h3 className="mt-2.5 text-xl font-medium text-white font-heading">
                        Thank you!
                      </h3>
                      <p className="mt-1.5 text-base text-gray-300">
                        We've received your information and will contact you
                        shortly.
                      </p>
                      <Button
                        className="mt-4 bg-primary hover:bg-primary-light shadow-lg shadow-primary/20 h-10 px-5 text-base text-white"
                        onClick={() => setIsSuccess(false)}
                      >
                        Submit another request
                      </Button>
                    </div>
                  ) : (
                    <form
                      onSubmit={handleSubmit}
                      className="space-y-12 bg-[#121A2A]/80 rounded-xl border border-[#1E2A40]/40 shadow-xl p-5 backdrop-blur-sm"
                    >
                      <div className="leading-none">
                        <h2 className="text-xl md:text-2xl font-bold tracking-tight text-yellow-400 text-center mb-1 font-heading">
                          Book a Demo
                        </h2>
                        <p
                          className="text-sm text-center mt-4 mb-2 italic"
                          style={{ color: "rgba(250, 240, 200, 0.85)" }}
                        >
                          Get Exclusive Early Access
                        </p>
                      </div>
                      <div className="space-y-1.5">
                        <Label
                          htmlFor="name"
                          className="text-sm font-medium text-yellow-400 font-heading"
                        >
                          Name *
                        </Label>
                        <Input
                          id="name"
                          name="name"
                          required
                          value={formState.name}
                          onChange={handleChange}
                          className="h-10 rounded-md bg-[#1A2438]/70 border-[#2A3A59]/50 focus:border-[#6366F1] focus:ring-[#6366F1] transition-all text-yellow-400 placeholder:text-yellow-400/50 pl-4"
                          placeholder="John Doe"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <Label
                          htmlFor="email"
                          className="text-sm font-medium text-yellow-400 font-heading"
                        >
                          Email *
                        </Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          required
                          value={formState.email}
                          onChange={handleChange}
                          className="h-10 rounded-md bg-[#1A2438]/70 border-[#2A3A59]/50 focus:border-[#6366F1] focus:ring-[#6366F1] transition-all text-yellow-400 placeholder:text-yellow-400/50 pl-4"
                          placeholder="john.doe@example.com"
                        />
                      </div>

                      <Button
                        type="submit"
                        className="w-full h-11 text-base font-medium transition-all mt-4 font-heading text-white"
                        style={{
                          background:
                            "linear-gradient(to right, #1bc290, #2ab58b)",
                          boxShadow: "0 4px 8px rgba(27, 194, 144, 0.3)",
                          textShadow: "0 0 3px rgba(0, 0, 0, 0.3)",
                        }}
                        disabled={isSubmitting}
                      >
                        {isSubmitting ? "Booking..." : "Book"}
                      </Button>
                      <p
                        className="text-sm text-center"
                        style={{ color: "rgba(250, 240, 200, 0.85)" }}
                      >
                        We will never share your information.
                      </p>
                    </form>
                  )}
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
