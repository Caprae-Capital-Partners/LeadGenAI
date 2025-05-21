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
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await submitLeadForm(formState)
      setIsSuccess(true)
      setFormState({
        name: "",
        email: "",
      })
    } catch (error) {
      console.error("Error submitting form:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen w-full overflow-auto relative flex flex-col justify-between">
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
            background: "radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.2), transparent 70%)",
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

        {/* Large blurred logo head popping from left side - BIGGER */}
        <div className="absolute left-[-500px] top-1/2 transform -translate-y-1/2 z-0">
          <div className="w-[1000px] h-[1000px] relative">
            <Image
              src="/images/saadquatch_logo.png"
              alt=""
              width={1000}
              height={1000}
              className="object-contain filter blur-[40px] opacity-15"
            />
          </div>
        </div>
      </div>

      <div className="relative z-10 flex flex-col h-full">
        {/* Top Section: Logo and Title */}
        <section className="pt-16 pb-8 flex flex-col items-center justify-center">
          {/* Logo */}
          <div
            className={`w-full flex flex-col items-center justify-center transition-opacity duration-1000 ease-in-out ${
              visibleSections.logo ? "opacity-100" : "opacity-0"
            }`}
          >
            <div className="h-[30vh] w-[30vw] max-w-[400px] max-h-[400px] relative flex items-center justify-center">
              <Image
                src="/images/saadquatch_logo.png"
                alt="SaaSquatch Logo"
                width={400}
                height={400}
                className="object-contain"
              />
            </div>

            {/* Title below logo - with increased spacing and better alignment */}
            <div className="text-center mt-10">
              <h2 className="text-4xl md:text-5xl font-bold text-white font-heading">
                SaaSquatch <span className="text-primary">Leads</span>
              </h2>
            </div>
          </div>

          {/* Divider */}
          <div
            className={`w-full flex justify-center mt-12 mb-6 transition-all duration-1000 ease-in-out ${
              visibleSections.logo ? "opacity-100 transform-none" : "opacity-0 -translate-y-10"
            }`}
          >
            <div className="w-full max-w-7xl px-5 flex items-center">
              <div className="h-px flex-grow bg-gradient-to-r from-transparent via-white to-transparent opacity-20"></div>
              <div className="mx-5 w-8 h-8 rounded-full bg-white/10 flex items-center justify-center shadow-lg">
                <div className="w-4 h-4 rounded-full bg-[#050A14] flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full bg-white/30"></div>
                </div>
              </div>
              <div className="h-px flex-grow bg-gradient-to-r from-transparent via-white to-transparent opacity-20"></div>
            </div>
          </div>
        </section>

        {/* Main Content Section: Video and Form side by side */}
        <section
          className={`w-full px-5 py-10 flex-grow transition-all duration-1000 ease-in-out ${
            visibleSections.content ? "opacity-100 transform-none" : "opacity-0 translate-y-10"
          }`}
        >
          <div className="w-full max-w-7xl mx-auto relative">
            <div className="flex flex-col lg:flex-row gap-8 lg:gap-24 items-center lg:items-stretch">
              {/* Coming Soon Text */}
              <div className="absolute -top-16 left-0 right-0 text-center">
                <div className="inline-block text-yellow-400 font-bold uppercase text-xl md:text-2xl tracking-wide">
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
                  <div className="absolute inset-0 flex items-center justify-center z-10">
                    <Button
                      size="icon"
                      className="h-[70px] w-[70px] rounded-full bg-yellow-400 hover:bg-yellow-500 shadow-lg flex items-center justify-center"
                    >
                      <Play className="h-9 w-9 text-black" />
                    </Button>
                  </div>
                  <Image
                    src="/placeholder.svg?height=990&width=1760"
                    alt="SaaSquatch Leads Demo Video"
                    width={1408}
                    height={792}
                    className="object-cover w-full h-full opacity-50"
                  />
                </div>
              </div>

              {/* Form Section - Now 50% width */}
              <div className="w-full lg:w-1/2 relative flex items-center">
                {/* Blurred logo background */}
                <div className="absolute inset-0 flex items-center justify-center overflow-hidden opacity-10 z-0">
                  <div className="w-[330px] h-[330px] relative transform -rotate-12">
                    <Image
                      src="/images/saadquatch_logo.png"
                      alt=""
                      width={330}
                      height={330}
                      className="object-contain filter blur-xl"
                    />
                  </div>
                </div>

                <div className="w-full relative z-10">
                  {isSuccess ? (
                    <div className="text-center py-5 bg-[#121A2A]/80 rounded-xl border border-[#1E2A40]/40 shadow-xl p-5 backdrop-blur-sm">
                      <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-[#6366F1]/10">
                        <CheckCircle className="h-6 w-6 text-[#6366F1]" />
                      </div>
                      <h3 className="mt-2.5 text-xl font-medium text-white font-heading">Thank you!</h3>
                      <p className="mt-1.5 text-base text-gray-300">
                        We've received your information and will contact you shortly.
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
                      className="space-y-10 bg-[#121A2A]/80 rounded-xl border border-[#1E2A40]/40 shadow-xl p-5 backdrop-blur-sm"
                    >
                      <h2 className="text-xl md:text-2xl font-bold tracking-tight text-yellow-400 text-center mb-1.5 font-heading">
                        Book a Demo
                      </h2>
                      <p className="text-sm text-yellow-400 text-center mb-2.5">Get Exclusive Early Access</p>

                      <div className="space-y-1.5">
                        <Label htmlFor="name" className="text-sm font-medium text-yellow-400 font-heading">
                          Name *
                        </Label>
                        <Input
                          id="name"
                          name="name"
                          required
                          value={formState.name}
                          onChange={handleChange}
                          className="h-10 rounded-md bg-[#1A2438]/70 border-[#2A3A59]/50 focus:border-[#6366F1] focus:ring-[#6366F1] transition-all text-yellow-400 placeholder:text-yellow-400/50"
                          placeholder="John Doe"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <Label htmlFor="email" className="text-sm font-medium text-yellow-400 font-heading">
                          Email *
                        </Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          required
                          value={formState.email}
                          onChange={handleChange}
                          className="h-10 rounded-md bg-[#1A2438]/70 border-[#2A3A59]/50 focus:border-[#6366F1] focus:ring-[#6366F1] transition-all text-yellow-400 placeholder:text-yellow-400/50"
                          placeholder="john.doe@example.com"
                        />
                      </div>

                      <Button
                        type="submit"
                        className="w-full h-11 text-base font-medium bg-primary hover:bg-primary-light transition-all shadow-[0_4px_8px_rgba(46,139,87,0.3)] hover:shadow-[0_4px_12px_rgba(46,139,87,0.4)] mt-4 font-heading text-white"
                        disabled={isSubmitting}
                      >
                        {isSubmitting ? "Booking..." : "Book"}
                      </Button>
                      <p className="text-sm text-gray-400 text-center">We will never share your information.</p>
                    </form>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
