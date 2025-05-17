"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { ScraperResults } from "@/components/scraper-results"
import axios from "axios"

const SCRAPER_API = `${process.env.NEXT_PUBLIC_BACKEND_URL_P1}/api/lead-scrape`;
// const SCRAPER_API = `http://127.0.0.1:5050/api/lead-scrape`;


export function Scraper() {
  const [isScrapingActive, setIsScrapingActive] = useState(false)
  const [progress, setProgress] = useState(0)
  const [showResults, setShowResults] = useState(false)

  // Search criteria state
  const [industry, setIndustry] = useState("")
  const [location, setLocation] = useState("")
  const [scrapedResults, setScrapedResults] = useState<any[]>([])
  // const controllerRef = useRef<AbortController | null>(null)
  const controllerRef = useRef<{ abort: () => void } | null>(null)


  // const handleStartScraping = async () => {
  //   setIsScrapingActive(true)
  //   setProgress(0)
  //   setShowResults(false)

  //   const controller = new AbortController()
  //   controllerRef.current = controller

  //   try {
  //     const response = await axios.post(
  //       SCRAPER_API,
  //       { industry, location },
  //       { signal: controller.signal }
  //     )

  //     const data = response.data
  //     console.log("Scraped Results:", data)
  //     setScrapedResults(data)
  //     setShowResults(true)
  //   } catch (error: any) {
  //     if (axios.isCancel(error)) {
  //       console.warn("Scraping canceled")
  //     } else {
  //       console.error("Scraping failed:", error)
  //     }
  //   } finally {
  //     setIsScrapingActive(false)
  //     setProgress(100)
  //     controllerRef.current = null
  //   }
  // }
const handleStartScraping = async () => {
  setIsScrapingActive(true)
  setProgress(0)
  setShowResults(true)
  setScrapedResults([])

  const queryParams = new URLSearchParams({ industry, location })
  const url = `http://127.0.0.1:8000/scrape-stream?${queryParams.toString()}`
  const eventSource = new EventSource(url)

  controllerRef.current = {
    abort: () => eventSource.close()
  }

  eventSource.addEventListener("init", (event) => {
    console.log("Init:", event.data)
    setProgress(5)
  })

  eventSource.addEventListener("batch", (event) => {
    try {
      const parsed = JSON.parse(event.data)
      const newItems = parsed.new_items ?? []

      if (!Array.isArray(newItems)) {
        console.warn("Expected new_items to be an array, got:", newItems)
        return
      }

      console.log("Batch received:", parsed)
      setScrapedResults((prev) => [...prev, ...newItems])
      setProgress((prev) => Math.min(prev + 10, 95))
    } catch (err) {
      console.error("Failed to parse batch event:", err)
    }
  })

  eventSource.addEventListener("done", (event) => {
    console.log("Done:", event.data)
    setProgress(100)
    setIsScrapingActive(false)
    setShowResults(true)
    eventSource.close()
  })

  eventSource.onerror = (err) => {
    console.error("Streaming error:", err)
    setIsScrapingActive(false)
    setProgress(100)
    eventSource.close()
  }
}



  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Company Finder</h2>
          <p className="text-muted-foreground">Find companies by industry and location</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Criteria</CardTitle>
          <CardDescription>Enter industry and location to find companies</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Input
                id="industry"
                placeholder="Enter industry (e.g. Software, Healthcare)"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="Enter location (e.g. San Francisco, CA)"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline">Clear</Button>
          <Button
            className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600"
            onClick={handleStartScraping}
            disabled={isScrapingActive || !industry || !location}
          >
            Scrape Leads
          </Button>
           {/* <Button
            variant="destructive"
            disabled={!isScrapingActive}
            onClick={() => {
              if (controllerRef.current) {
                controllerRef.current.abort()
              }
              setIsScrapingActive(false)
              setProgress(0)
              setShowResults(false)
            }}
          >
            Cancel
          </Button> */}
          <Button
            variant="destructive"
            disabled={!isScrapingActive}
            onClick={() => {
              if (controllerRef.current) {
                controllerRef.current.abort()
              }
              setIsScrapingActive(false)
              setProgress(0)
              setShowResults(false)
              setScrapedResults([])
          }}
        >
          Cancel
        </Button>
        </CardFooter>
         

      </Card>

      {isScrapingActive && (
        <Card>
          <CardHeader>
            <CardTitle>Search in Progress</CardTitle>
            <CardDescription>
              Finding companies in {location} within the {industry} industry
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-muted-foreground mt-2">
                This may take a few minutes depending on the search criteria
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {showResults && <ScraperResults data={scrapedResults} />}
    </div>
  )
}
