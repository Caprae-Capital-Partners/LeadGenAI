"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2, Copy, Check, ChevronRight } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { Header } from "@/components/header"
import { Sidebar } from "@/components/sidebar"

const historyItems = [
  {
    id: 1,
    person: "person 1",
    company: "Company X",
    subject: "Regarding our connection",
    date: "12/05/2025",
  },
  {
    id: 2,
    person: "person 2",
    company: "Company Y",
    subject: "Following up",
    date: "12/04/2025",
  },
  {
    id: 3,
    person: "person 3",
    company: "company A",
    subject: "Subject: blabla...",
    date: "12/03/2025",
  },
  {
    id: 4,
    person: "person 4",
    company: "Company Z",
    subject: "Quick question",
    date: "12/02/2025",
  },
];

export default function EmailGenerator() {
  const [isLoading, setIsLoading] = useState(false)
  const [generatedEmail, setGeneratedEmail] = useState("")
  const [copied, setCopied] = useState(false)
  const { toast } = useToast()

  const [formData, setFormData] = useState({
    recipientName: "",
    recipientRole: "",
    companyName: "",
    companyWebsite: "",
    emailType: "cold-outreach",
    context: "",
    tone: "professional"
  })

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const generateEmail = async () => {
    if (!formData.recipientName || !formData.companyName) {
      toast({
        title: "Missing Information",
        description: "Please fill in the recipient name and company name.",
        variant: "destructive"
      })
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch("/api/generate-email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        throw new Error("Failed to generate email")
      }

      const data = await response.json()
      setGeneratedEmail(data.email)
      toast({
        title: "Email Generated",
        description: "Your email has been generated successfully!",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate email. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generatedEmail)
      setCopied(true)
      toast({
        title: "Copied!",
        description: "Email copied to clipboard.",
      })
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to copy to clipboard.",
        variant: "destructive"
      })
    }
  }

  return (
    <div className="flex flex-col h-screen bg-dark-primary text-gray-100">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 p-6 overflow-y-auto">
          <div className="flex flex-col space-y-2">
            <h1 className="text-3xl font-bold text-white">Email Generator</h1>
            <p className="text-gray-400">Generate personalized email messages for your leads</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            {/* Input Form */}
            <Card className="bg-dark-secondary border-dark-border">
              <CardHeader>
                <CardTitle className="text-white">Email Details</CardTitle>
                <CardDescription className="text-gray-400">
                  Fill in the details to generate a personalized email
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="recipientName" className="text-white">Recipient Name</Label>
                    <Input
                      id="recipientName"
                      placeholder="John Doe"
                      value={formData.recipientName}
                      onChange={(e) => handleInputChange("recipientName", e.target.value)}
                      className="bg-dark-primary border-dark-border text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="recipientRole" className="text-white">Recipient Role</Label>
                    <Input
                      id="recipientRole"
                      placeholder="CEO, Manager, etc."
                      value={formData.recipientRole}
                      onChange={(e) => handleInputChange("recipientRole", e.target.value)}
                      className="bg-dark-primary border-dark-border text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="companyName" className="text-white">Company Name</Label>
                    <Input
                      id="companyName"
                      placeholder="Acme Corporation"
                      value={formData.companyName}
                      onChange={(e) => handleInputChange("companyName", e.target.value)}
                      className="bg-dark-primary border-dark-border text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="companyWebsite" className="text-white">Company Website</Label>
                    <Input
                      id="companyWebsite"
                      placeholder="https://acme.com"
                      value={formData.companyWebsite}
                      onChange={(e) => handleInputChange("companyWebsite", e.target.value)}
                      className="bg-dark-primary border-dark-border text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="emailType" className="text-white">Email Type</Label>
                    <Select value={formData.emailType} onValueChange={(value) => handleInputChange("emailType", value)}>
                      <SelectTrigger className="bg-dark-primary border-dark-border text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-dark-primary border-dark-border">
                        <SelectItem value="cold-outreach">Cold Outreach</SelectItem>
                        <SelectItem value="follow-up">Follow-up</SelectItem>
                        <SelectItem value="meeting-request">Meeting Request</SelectItem>
                        <SelectItem value="partnership">Partnership</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tone" className="text-white">Tone</Label>
                    <Select value={formData.tone} onValueChange={(value) => handleInputChange("tone", value)}>
                      <SelectTrigger className="bg-dark-primary border-dark-border text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-dark-primary border-dark-border">
                        <SelectItem value="professional">Professional</SelectItem>
                        <SelectItem value="friendly">Friendly</SelectItem>
                        <SelectItem value="casual">Casual</SelectItem>
                        <SelectItem value="formal">Formal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="context" className="text-white">Additional Context</Label>
                  <Textarea
                    id="context"
                    placeholder="Any specific context, pain points, or value propositions to include..."
                    value={formData.context}
                    onChange={(e) => handleInputChange("context", e.target.value)}
                    className="bg-dark-primary border-dark-border text-white min-h-[100px]"
                  />
                </div>

                <Button
                  onClick={generateEmail}
                  disabled={isLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    "Generate Email"
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Generated Email */}
            <Card className="bg-dark-secondary border-dark-border">
              <CardHeader>
                <CardTitle className="text-white">Generated Email</CardTitle>
                <CardDescription className="text-gray-400">
                  Your personalized email will appear here
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {generatedEmail ? (
                  <>
                    <div className="bg-dark-primary border border-dark-border rounded-lg p-4 min-h-[300px]">
                      <pre className="text-white whitespace-pre-wrap font-sans text-sm">
                        {generatedEmail}
                      </pre>
                    </div>
                    <Button
                      onClick={copyToClipboard}
                      variant="outline"
                      className="w-full border-dark-border text-white hover:bg-dark-hover"
                    >
                      {copied ? (
                        <>
                          <Check className="mr-2 h-4 w-4" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="mr-2 h-4 w-4" />
                          Copy to Clipboard
                        </>
                      )}
                    </Button>
                  </>
                ) : (
                  <div className="bg-dark-primary border border-dark-border rounded-lg p-8 min-h-[300px] flex items-center justify-center">
                    <p className="text-gray-400 text-center">
                      Fill in the details and click "Generate Email" to create your personalized message
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* History Section */}
          <div className="mt-8">
            <h2 className="text-2xl font-bold text-white mb-4">History</h2>
            <div className="relative">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {historyItems.map((item) => (
                  <Card key={item.id} className="bg-orange-500 border-transparent text-white shadow-lg transform transition-transform hover:scale-105 cursor-pointer">
                    <CardContent className="p-4 flex flex-col justify-between h-full">
                      <div>
                        <p className="font-bold text-lg">{item.person}</p>
                        <p className="text-sm">{item.company}</p>
                        <p className="text-sm mt-2">{item.subject}</p>
                      </div>
                      <p className="text-xs text-right mt-4">{item.date}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <div className="absolute -right-12 top-1/2 -translate-y-1/2 hidden md:block">
                <Button variant="ghost" size="icon" className="rounded-full bg-dark-hover text-white hover:bg-dark-hover/80">
                  <ChevronRight className="h-6 w-6" />
                </Button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
} 