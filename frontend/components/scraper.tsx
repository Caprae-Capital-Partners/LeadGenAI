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
import { useRouter } from "next/navigation";


const SCRAPER_API = `${process.env.NEXT_PUBLIC_BACKEND_URL_P1}/scrape-stream`;
const FETCH_INDUSTRIES_API = `${process.env.NEXT_PUBLIC_DATABASE_URL}/industries`;
const FETCH_DB_API = `${process.env.NEXT_PUBLIC_DATABASE_URL}/lead_scrape`;

// Define interfaces for type safety
interface LeadData {
  lead_id?: string; // from backend
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
  business_phone?: string;
  id?: number;
  phone?: string;
  [key: string]: any; // For any other properties we might not know about
}

interface FormattedLead {
  id: number;             // local index
  lead_id: string;        // unique identifier from DB
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
  const [scrapedResults, setScrapedResults] = useState<FormattedLead[]>([])
  const controllerRef = useRef<{ abort: () => void } | null>(null)
  const router = useRouter();
  // Track companies we've already seen to prevent duplicates
  const seenCompaniesRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    
    const verifyLogin = async () => {
      try {
        const res = await fetch("https://data.capraeleadseekers.site/api/ping-auth", {
          method: "GET",
          credentials: "include",
        });

        if (!res.ok) {
          router.push("/auth");
        } else {
          console.log("✅ Authenticated user");
        }
      } catch (error) {
        console.error("❌ Error verifying login:", error);
        router.push("/auth");
      }
    };

    verifyLogin();

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

  // Format data consistently across all sources
  const formatLeadData = (item: LeadData, index: number): FormattedLead => ({
    id: index, // internal use for React keys or pagination
    lead_id: item.lead_id || "", // real DB identifier, passed to /leads/multiple
    company: item.Company || item.company || "",
    website: item.Website || item.website || "",
    industry: item.Industry || item.industry || "",
    street: item.Street || item.street || "",
    city: item.City || item.city || "",
    state: item.State || item.state || "",
    bbb_rating: item.BBB_rating || item.bbb_rating || "",
    business_phone: item.Business_phone || item.business_phone || item.phone || "",
  });

  // Add new leads while avoiding duplicates
  const addNewLeads = (existingLeads: FormattedLead[], newLeads: FormattedLead[]): FormattedLead[] => {
    const combinedResults = [...existingLeads];
    
    // Use our ref to track seen companies instead of recreating the set each time
    newLeads.forEach((item: FormattedLead) => {
      const companyLower = item.company.toLowerCase().trim();
      if (companyLower && !seenCompaniesRef.current.has(companyLower)) {
        seenCompaniesRef.current.add(companyLower);
        combinedResults.push(item);
      }
    });
    
    return combinedResults;
  };

  const handleStartScraping = async () => {
    setIsScrapingActive(true);
    setProgress(5);
    setScrapingSource('scraper');
    
    // Don't hide results if we're appending to existing results
    if (scrapedResults.length === 0) {
      setShowResults(true);
      // Reset our seen companies set if we're starting fresh
      seenCompaniesRef.current = new Set();
    } else {
      // Initialize our seen companies set with existing companies if we're appending
      scrapedResults.forEach(item => {
        seenCompaniesRef.current.add(item.company.toLowerCase().trim());
      });
    }

    interface Batch {
      batch: number;
      new_items: LeadItem[]; 
      total_scraped: number;
      elapsed_time: number;
      processed_count: number;
    }

    interface LeadItem {
      [key: string]: any; // For any properties with unknown structure
    }

    // Set up debugging variables to track data
    let totalProcessedItems = 0;
    let allBatches: Batch[] = [];
    let receivedBatchIds = new Set<number>(); // Track received batch IDs to prevent duplicates

    // Create query parameters
    const queryParams = new URLSearchParams({ 
      industry, 
      location 
    });
    
    // Create EventSource connection with explicit parameters
    const url = `${SCRAPER_API}?${queryParams.toString()}`;
    console.log("Connecting to stream URL:", url);
    
    const eventSource = new EventSource(url);

    controllerRef.current = {
      abort: () => {
        console.log("Manually closing EventSource connection");
        eventSource.close();
      }
    };

    // Track connection state
    eventSource.onopen = () => {
      console.log("EventSource connection opened successfully");
    };

    eventSource.addEventListener("init", (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Init event received:", data);
        setProgress(10);
      } catch (err) {
        console.error("Failed to parse init event:", event.data, err);
      }
    });

    eventSource.addEventListener("batch", (event) => {
      try {
        const parsed = JSON.parse(event.data);
        
        // Check if we've already processed this batch
        if (parsed.batch && receivedBatchIds.has(parsed.batch)) {
          console.log(`Skipping duplicate batch ${parsed.batch}`);
          return;
        }
        
        // Add batch ID to tracking set
        if (parsed.batch) {
          receivedBatchIds.add(parsed.batch);
        }
        
        allBatches.push(parsed); // Store all batches for debugging
        
        const newItems = parsed.new_items || [];
        totalProcessedItems += newItems.length;
        
        console.log(`Batch ${parsed.batch} received: ${newItems.length} new items, total batched: ${totalProcessedItems}`);
        console.log("Sample item:", newItems.length > 0 ? newItems[0] : "No items");
        
        if (!Array.isArray(newItems)) {
          console.warn("Expected new_items to be an array, got:", typeof newItems);
          return;
        }

        if (newItems.length === 0) {
          console.log("Received empty batch, skipping processing");
          return;
        }
        
        // Format the new items with proper IDs
        const formattedItems = newItems.map((item: LeadItem, index: number) => 
          formatLeadData(item, Date.now() + index)
        );
        
        // Add new items to results, avoiding duplicates
        setScrapedResults((prev) => {
          const updatedResults = addNewLeads(prev, formattedItems);
          console.log(`Current lead count: ${updatedResults.length}`);
          return updatedResults;
        });
        
        // Update progress based on actual data received
        // Calculate progress as a percentage of expected total (100 leads)
        setProgress((prev) => {
          // Calculate a dynamic progress that increases with each batch
          // but slows down as we approach 95% to avoid jumping too quickly
          const baseProgress = Math.min(10 + (totalProcessedItems / 10), 95);
          return Math.max(prev, baseProgress); // Never decrease progress
        });
      } catch (err) {
        console.error("Failed to parse batch event:", err);
        console.error("Raw event data:", event.data);
      }
    });

    // Add handler for the 'complete' event that backend sends
    eventSource.addEventListener("complete", (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Complete event received:", data);
      } catch (err) {
        console.error("Failed to parse complete event:", err);
      }
    });

    eventSource.addEventListener("ping", (event) => {
      console.log("Heartbeat:", JSON.parse(event.data));
    });

    eventSource.addEventListener("done", (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Done event received:", data);
        console.log("Total items received across all batches:", totalProcessedItems);
        console.log("All batches summary:", allBatches.map((b: Batch) => b.new_items?.length || 0));
        
        setProgress(100);
        setIsScrapingActive(false);
        setScrapedResults((currentResults) => {
          console.log(`Final lead count: ${currentResults.length}`);
          return currentResults;
        });
      } catch (err) {
        console.error("Failed to parse done event:", err);
      } finally {
        console.log("Closing EventSource connection");
        eventSource.close();
      }
    });

    // Error handler 
    eventSource.onerror = (err) => {
      console.error("EventSource error:", err);
      setIsScrapingActive(false);
      setProgress(100);
      console.log("Closing EventSource connection due to error");
      eventSource.close();
    };
  };

  const handleCollectData = async () => {
    setIsScrapingActive(true)
    setProgress(0)
    setShowResults(false)
    setScrapingSource('database')
    
    // Reset our seen companies set
    seenCompaniesRef.current = new Set();

    const controller = new AbortController()
    controllerRef.current = {
      abort: () => controller.abort()
    };

    try {
      const response = await axios.post(
        FETCH_DB_API,
        { industry, location },
        { signal: controller.signal }
      )

      const data = response.data
      const formattedData = data.map((item: LeadData, index: number) => formatLeadData(item, index));
      
      // Initialize our seen companies with these results
      formattedData.forEach((item: FormattedLead) => {
        if (item.company.trim()) {
          seenCompaniesRef.current.add(item.company.toLowerCase().trim());
        }
      });
      
      setScrapedResults(formattedData)
      setShowResults(true)
      setNeedMoreLeads(formattedData.length < 100)
    } catch (error: any) {
      if (axios.isCancel(error)) {
        console.warn("Database fetch canceled")
      } else {
        console.error("Database fetch failed:", error)
      }
    } finally {
      setIsScrapingActive(false)
      setProgress(100)
      controllerRef.current = null
    }
  }

  const handleClearSearch = () => {
    setIndustry('');
    setLocation('');
    setShowResults(false);
    setScrapedResults([]);
    setNeedMoreLeads(false);
    seenCompaniesRef.current = new Set();
  };

  const handleCancelScraping = () => {
    if (controllerRef.current) {
      controllerRef.current.abort();
    }
    setIsScrapingActive(false);
    setProgress(0);
  };

  // Add this useEffect after your other useEffects
  useEffect(() => {
    const deduped = new Set(scrapedResults.map(l => l.company.toLowerCase().trim()));
    setNeedMoreLeads(deduped.size < 100);
  }, [scrapedResults]);

  useEffect(() => {
    const saved = localStorage.getItem("scrapedResults");
    if (saved) {
      try {
        const parsed: FormattedLead[] = JSON.parse(saved);
        if (parsed.length > 0) {
          setScrapedResults(parsed);
          setShowResults(true);
          seenCompaniesRef.current = new Set(parsed.map(l => l.company.toLowerCase().trim()));
        }
      } catch (err) {
        console.error("Failed to parse saved scraped results:", err);
      }
    }
  }, []);

  useEffect(() => {
    if (scrapedResults.length > 0) {
      sessionStorage.setItem("leads", JSON.stringify(scrapedResults));
    }
  }, [scrapedResults]);
  

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
                    setShowDropdown(true);
                  }
                }}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
              />
              {showDropdown && (
                <ul
                  className="absolute border border-border rounded max-h-52 overflow-y-auto w-[38%] z-[1000] shadow-lg mt-1 bg-background text-foreground transition-colors duration-150"
                >
                  {filteredIndustries.map((ind, index) => (
                    <li
                      key={index}
                      className="px-3 py-2 cursor-pointer hover:bg-accent hover:text-accent-foreground transition-colors duration-100"
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
          <Button variant="outline" onClick={handleClearSearch}>
            Clear
          </Button>
          <div className="flex gap-2">
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
              onClick={handleCancelScraping}
            >
              Cancel
            </Button>
          </div>
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
                <p className="text-sm">We recommend at least 100 leads for best results. Click "Scrape More Leads" above to find additional leads.</p>
              </div>
            </div>
          )}
          <ScraperResults 
            data={scrapedResults} 
            industry={industry}
            location={location}
          />
        </>
      )}
    </div>
  )
}