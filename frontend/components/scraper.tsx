"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { ScraperResults } from "@/components/scraper-results"
import axios from "axios"
import { AlertCircle, DatabaseIcon } from "lucide-react"

const SCRAPER_API = `${process.env.NEXT_PUBLIC_BACKEND_URL_P1}/scraper`;
const FETCH_INDUSTRIES_API = `${process.env.NEXT_PUBLIC_DATABASE_URL}/industries`;
const FETCH_DB_API = `${process.env.NEXT_PUBLIC_DATABASE_URL}/lead_scrape`;

// Define interfaces for type safety
interface LeadData {
  Company?: string;
  company?: string;
  Website?: string;
  website?: string;
  Industry?: string;
  industry?: string;
  Street?: string;
  street?: string;
  City?: string;
  city?: string;
  State?: string;
  state?: string;
  BBB_rating?: string;
  bbb_rating?: string;
  Business_phone?: string;
  lead_id: number;
  phone?: string;
  [key: string]: any; // For any other properties we might not know about
}

interface FormattedLead {
  lead_id: number;
  company: string;
  website: string;
  industry: string;
  street: string;
  city: string;
  state: string;
  bbb_rating: string;
  business_phone: string;
}

export function Scraper() {
  const [isScrapingActive, setIsScrapingActive] = useState(false)
  const [progress, setProgress] = useState(0)
  const [showResults, setShowResults] = useState(false)
  const [needMoreLeads, setNeedMoreLeads] = useState(false)
  const [scrapingSource, setScrapingSource] = useState<'database' | 'scraper'>('database')

  // Industry dropdown states
  const [industries, setIndustries] = useState<string[]>([]); // Full list from API
  const [filteredIndustries, setFilteredIndustries] = useState<string[]>([]); // Filtered list
  const [showDropdown, setShowDropdown] = useState(false);

  // Search criteria state
  const [industry, setIndustry] = useState("")
  const [location, setLocation] = useState("")
  const [scrapedResults, setScrapedResults] = useState<any[]>([])
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    const fetchIndustries = async () => {
      try {
        const response = await fetch(FETCH_INDUSTRIES_API);
        const data = await response.json();
        if (data && data.industries) {
          setIndustries(data.industries);
        } else {
          console.error("Invalid API response format:", data);
        }
      } catch (error) {
        console.error('Error fetching industries:', error);
      }
    };

  fetchIndustries();
}, []);

  const handleIndustryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setIndustry(value);

    if (value) {
      const filtered = industries.filter((ind) =>
        ind.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredIndustries(filtered);
      setShowDropdown(true);
    } else {
      setShowDropdown(false);
    }
  };

  const handleStartScraping = async () => {
    setIsScrapingActive(true)
    setProgress(0)
    setScrapingSource('scraper')
    // Don't hide results if we're appending to existing results
    if (scrapedResults.length === 0) {
      setShowResults(false)
    }

    const controller = new AbortController()
    controllerRef.current = controller

    try {
      const response = await axios.post(
        SCRAPER_API,
        { industry, location },
        { signal: controller.signal }
      )

      let data = response.data
      // Parse the data if it's a string
      if (typeof data === 'string') {
        try {
          // Replace NaN with null before parsing
          const sanitizedData = data.replace(/:NaN/g, ':null')
          data = JSON.parse(sanitizedData)
        } catch (e) {
          console.error("Failed to parse response data:", e)
          throw new Error("Invalid response format from server")
        }
      }
      
      // console.log("Raw API Response:", data)
      // console.log("Response type:", typeof data)
      // console.log("Is Array?", Array.isArray(data))
      
      // Format the new data in the same way as handleCollectData
      const formattedData = data.map((item: LeadData): FormattedLead => ({
        lead_id: item.lead_id, // Temporary ID that will be replaced by addUniqueIdsToLeads
        company: item.Company || item.company || "",
        website: item.Website || item.website || "",
        industry: item.Industry || item.industry || "",
        street: item.Street || item.street || "",
        city: item.City || item.city || "",
        state: item.State || item.state || "",
        bbb_rating: item.BBB_rating || item.bbb_rating || "",
        business_phone: item.Business_phone || item.phone || "",
      }));
      
      // Append new results to existing results if we're scraping more
      if (scrapedResults.length > 0 && needMoreLeads) {
        // Combine results and remove duplicates based on company name
        const combinedResults = [...scrapedResults]
        const existingCompanies = new Set(scrapedResults.map(r => r.company.toLowerCase()))
        
        formattedData.forEach((item: FormattedLead) => {
          if (!existingCompanies.has(item.company.toLowerCase())) {
            combinedResults.push(item)
          }
        })
        
        setScrapedResults(combinedResults)
        // Only need more leads if we're still under 250
        setNeedMoreLeads(combinedResults.length < 250)
      } else {
        setScrapedResults(formattedData)
        setNeedMoreLeads(formattedData.length < 250)
      }
      
      setShowResults(true)
    } catch (error: any) {
      if (axios.isCancel(error)) {
        console.warn("Scraping canceled")
      } else {
        console.error("Scraping failed:", error)
      }
    } finally {
      setIsScrapingActive(false)
      setProgress(100)
      controllerRef.current = null
    }
  }

  const handleCollectData = async () => {
    setIsScrapingActive(true)
    setProgress(0)
    setShowResults(false)
    setScrapingSource('database')

    const controller = new AbortController()
    controllerRef.current = controller

    try {
      const response = await axios.post(
        FETCH_DB_API,
        { industry, location },
        { signal: controller.signal }
      )

      const data = response.data
      const formattedData = data.map((item: LeadData): FormattedLead => ({
        lead_id: item.lead_id, // Temporary ID that will be replaced by addUniqueIdsToLeads
        company: item.Company || item.company || "",
        website: item.Website || item.website || "",
        industry: item.Industry || item.industry || "",
        street: item.Street || item.street || "",
        city: item.City || item.city || "",
        state: item.State || item.state || "",
        bbb_rating: item.BBB_rating || item.bbb_rating || "",
        business_phone: item.phone || item.phone || "",
      }));
      console.log("Scraped Results:", formattedData)
      setScrapedResults(formattedData)
      setShowResults(true)
      setNeedMoreLeads(formattedData.length < 250)
    } catch (error: any) {
      if (axios.isCancel(error)) {
        console.warn("Scraping canceled")
      } else {
        console.error("Scraping failed:", error)
      }
    } finally {
      setIsScrapingActive(false)
      setProgress(100)
      controllerRef.current = null
    }
  }


  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Company Finder</h2>
          <p className="text-muted-foreground">Find companies by industry and location</p>
        </div>
        
        {showResults && needMoreLeads && !isScrapingActive && (
          <Button 
            onClick={handleStartScraping}
            className="bg-amber-500 hover:bg-amber-600 text-white"
          >
            <AlertCircle className="mr-2 h-4 w-4" />
            Scrape More Leads
          </Button>
        )}
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
                onChange={handleIndustryChange}
                onFocus={() => {
                  if (industry.trim() !== "") {
                    setShowDropdown(true); // Show dropdown only if input is non-empty
                  }
                }}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)} // Hide dropdown on blur
              />
              {showDropdown && (
                <ul
                  className="absolute bg-white border border-gray-300 rounded max-h-52 overflow-y-auto w-[38%] z-[1000] shadow-lg mt-1"
                >
                  {filteredIndustries.map((ind, index) => (
                    <li
                      key={index}
                      className="px-3 py-2 cursor-pointer hover:bg-gray-100"
                      onClick={() => {
                        setIndustry(ind);
                        setShowDropdown(false);
                      }}
                    >
                      {ind}
                    </li>
                  ))}
                </ul>
              )}
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
          <Button variant="outline" onClick={() => {
            setIndustry('');
            setLocation('');
            setShowResults(false);
          }}>Clear</Button>
          <Button
            className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600"
            onClick={handleCollectData}
            disabled={isScrapingActive || !industry || !location}
          >
            <DatabaseIcon className="mr-2 h-4 w-4" />
            Find Companies
          </Button>
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
              {scrapingSource === 'database' ? 'Finding' : 'Scraping additional'} companies in {location} within the {industry} industry
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

      {showResults && (
        <>
          {needMoreLeads && !isScrapingActive && (
            <div className="bg-amber-50 border border-amber-200 rounded-md p-4 text-amber-800 flex items-center mb-4">
              <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
              <div>
                <p className="font-medium">Only {scrapedResults.length} leads found</p>
                <p className="text-sm">We recommend at least 250 leads for best results. Click "Scrape More Leads" above to find additional leads.</p>
              </div>
            </div>
          )}
          <ScraperResults data={scrapedResults} />
        </>
      )}
    </div>
  )
}
