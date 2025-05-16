"use client"

import * as React from "react"
import { useState } from "react"
// Import UI components from shadcn/ui - use relative paths to avoid module resolution issues
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { EnrichmentResults } from "../components/enrichment-results"
import { Button } from "../components/ui/button"
import { Checkbox } from "../components/ui/checkbox"
import { Input } from "../components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
// Import icons individually to avoid errors with lucide-react
import { Search, Filter, Download, X } from "lucide-react"
import { useLeads } from "./LeadsProvider"
import type { ApolloCompany, GrowjoCompany, ApolloPerson } from "../types/enrichment"
import axios from "axios"

// Define interfaces for our data structures
interface Lead {
  id: number;
  company: string;
  website: string;
  industry: string;
  street: string;
  city: string;
  state: string;
  bbb_rating: string;
  business_phone: string;
  [key: string]: any; // Allow additional properties
}

interface EnrichedLead {
  id: number;
  company: string;
  website: string;
  industry: string;
  productCategory?: string;
  businessType?: string;
  employees?: number | null;
  revenue?: string | null;
  yearFounded?: string;
  bbbRating?: string;
  street?: string;
  city?: string;
  state?: string;
  companyPhone?: string;
  companyLinkedin?: string;
  ownerFirstName?: string;
  ownerLastName?: string;
  ownerTitle?: string;
  ownerLinkedin?: string;
  ownerPhoneNumber?: string;
  ownerEmail?: string;
  source?: string;
  [key: string]: any; // Allow additional properties
}

interface ApiResponse {
  leads: any[];
  total?: number;
  pages?: number;
  current_page?: number;
  per_page?: number;
}

// Use a string literal instead of process.env to avoid TypeScript errors
const BACKEND_URL = typeof window !== 'undefined' ? (window as any).__NEXT_PUBLIC_BACKEND_URL_P2 || "" : ""

// Export the component as default for easier imports
export default function DataEnhancement() {
  // State for managing UI and results
  const [showResults, setShowResults] = useState(false)
  const [loading, setLoading] = useState(false)
  const [enrichedResults, setEnrichedResults] = useState<EnrichedLead[]>([])
  const [showFilters, setShowFilters] = useState(false)
  
  // State for managing leads and selection
  const { leads } = useLeads()
  
  // Properly typed normalizeLeadValue function
  const normalizeLeadValue = (val: string | null | undefined): string => {
    return val === null || val === undefined || val === "" || val === "NA" || val === "N/A" ? "N/A" : val
  }
  
  // Type the normalized leads properly
  const normalizedLeads: Lead[] = leads.map((lead: any) => ({
    ...lead,
    id: lead.id || 0,
    company: normalizeLeadValue(lead.company),
    website: normalizeLeadValue(lead.website),
    industry: normalizeLeadValue(lead.industry),
    street: normalizeLeadValue(lead.street),
    city: normalizeLeadValue(lead.city),
    state: normalizeLeadValue(lead.state),
    bbb_rating: normalizeLeadValue(lead.bbb_rating),
    business_phone: normalizeLeadValue(lead.business_phone),
  }))

  // Additional state variables for filtering and selection
  const [selectedCompanies, setSelectedCompanies] = useState<number[]>([])
  const [selectAll, setSelectAll] = useState(false)
  const [industryFilter, setIndustryFilter] = useState("")
  const [cityFilter, setCityFilter] = useState("")
  const [stateFilter, setStateFilter] = useState("")
  const [bbbRatingFilter, setBbbRatingFilter] = useState("")

  // Properly typed downloadCSV function
  const downloadCSV = (data: Record<string, any>[], filename: string): void => {
    if (!data.length) return;
    
    const headers = Object.keys(data[0])
    const csvRows = [
      headers.join(","), // header row
      ...data.map(row =>
        headers.map(field => {
          const value = row[field] ?? ""
          return `"${value.toString().replace(/"/g, '""')}"`
        }).join(",")
      ),
    ]
    const csvContent = csvRows.join("\n")
    const blob = new Blob([csvContent], { type: "text/csv" })
    const url = URL.createObjectURL(blob)

    const a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }
  const filteredLeads = normalizedLeads.filter((company) => {
    return (
      company.industry.toLowerCase().includes(industryFilter.toLowerCase()) &&
      company.city.toLowerCase().includes(cityFilter.toLowerCase()) &&
      company.state.toLowerCase().includes(stateFilter.toLowerCase()) &&
      company.bbb_rating.toLowerCase().includes(bbbRatingFilter.toLowerCase())
    )
  })


//   const companies = [
//   {
//     id: "1",
//     name: "HubSpot",
//     website: "hubspot.com",
//     industry: "CRM Software",
//     street: "25 First Street",
//     city: "Cambridge",
//     state: "MA",
//     phone: "(888) 482-7768",
//     bbbRating: "A+",
//   }
// ]
  // Properly typed handleSelectAll function
  const handleSelectAll = (): void => {
    if (selectAll) {
      setSelectedCompanies([])
    } else {
      // Ensure all IDs are numbers
      setSelectedCompanies(normalizedLeads.map((company) => Number(company.id) || 0))
    }
    setSelectAll(!selectAll)
  }

  // Properly typed handleSelectCompany function
  const handleSelectCompany = (id: number): void => {
    if (selectedCompanies.includes(id)) {
      // Rename companyId to itemId to avoid shadowing and add type annotation
      setSelectedCompanies(selectedCompanies.filter((itemId: number) => itemId !== id))
      setSelectAll(false)
    } else {
      const updated = [...selectedCompanies, id]
      setSelectedCompanies(updated)
      if (updated.length === normalizedLeads.length) {
        setSelectAll(true)
      }
    }
  }

  // Properly typed normalizeWebsite function
  const normalizeWebsite = (url: string | null | undefined): string => {
    if (!url) return "";
    return url.replace(/^https?:\/\//, "").replace(/\/$/, "").toLowerCase()
  }

  // Properly typed getSource function
  const getSource = (growjo: Record<string, any>, apollo: Record<string, any>, person: Record<string, any>): string => {
    const g = growjo && Object.keys(growjo).some((k) => Boolean(growjo[k]))
    const a = apollo && Object.keys(apollo).some((k) => Boolean(apollo[k]))
    const p = person && Object.keys(person).some((k) => Boolean(person[k]))
    if (g && a) return "Growjo + Apollo"
    if (g) return "Growjo"
    if (a) return "Apollo"
    return "N/A"
  }
// Loading state for the enrichment process
// Main function to handle the enrichment process
const handleStartEnrichment = async (): Promise<void> => {
  setLoading(true)

  try {
    // Get selected leads from the normalized leads array
    let selected = normalizedLeads.filter((c) => selectedCompanies.includes(c.id))
    
    // Set up headers with authentication token
    const token = localStorage.getItem('token') || ""
    const headers = { 
      headers: { 
        "Content-Type": "application/json", 
        "Authorization": `Bearer ${token}` 
      } 
    }
    
    // Check if leads are already available in the database
    const selectedWebsites = selected.map(c => c.website).filter((website): website is string => 
      typeof website === 'string' && website !== '' && website !== 'N/A'
    )
    
    if (selectedWebsites.length > 0) {
      try {
        // Query the API to check if these leads already exist
        const leadsResponse = await axios.get<ApiResponse>(
          `https://data.capraeleadseekers.site/api/leads`,
          headers
        )
        
        // Filter out leads that already exist in the database
        const existingWebsites = (leadsResponse.data.leads || []).map((lead: any) => 
          normalizeWebsite(lead.website)
        )
        
        const leadsToEnrich = selected.filter(c => {
          const normalizedWebsite = normalizeWebsite(c.website)
          return normalizedWebsite && !existingWebsites.includes(normalizedWebsite)
        })
      
      // If all leads already exist, just return them without enrichment
      if (leadsToEnrich.length === 0) {
        console.log('All selected leads already exist in the database')
        const existingLeads = leadsResponse.data.leads.filter((lead: any) => 
          selected.some(s => normalizeWebsite(s.website) === normalizeWebsite(lead.website))
        )
        setEnrichedResults(existingLeads as EnrichedLead[])
        setShowResults(true)
        setLoading(false)
        return
      }
      
      // Update selected to only include leads that need enrichment
      selected = leadsToEnrich
      } catch (apiError) {
        console.error('Error checking leads in database:', apiError)
        // Continue with enrichment if API call fails
      }
    }
  
    // Step 1: Run Growjo enrichment for companies that need it
    // Initialize growjoMapData at the top level to avoid scope issues
    let growjoMapData: Record<string, GrowjoCompany> = {}
    
    try {
      const growjoRes = await axios.post<GrowjoCompany[]>(
        `${BACKEND_URL}/scrape-growjo-batch`,
        selected.map((c) => ({ company: c.company || "" })),
        headers
      )
    
      // Create a map of company names to Growjo data
      growjoMapData = Object.fromEntries(
        (growjoRes.data || []).map((item: GrowjoCompany) => [
          (item.company_name?.toLowerCase() || item.input_name?.toLowerCase() || ""),
          item
        ])
      )
  
      // Step 2: Update websites from Growjo result
      selected = selected.map((company) => {
        // Use growjoMapData instead of growjoMap
        const growjo = growjoMapData[company.company.toLowerCase()] || {}
        return {
          ...company,
          website:
            growjo.company_website && growjo.company_website.toLowerCase() !== "not found"
              ? growjo.company_website
              : company.website,
        }
      })
  
      // Step 3: Get valid domains from updated companies
      const selectedWithWebsites = selected.filter((c) => {
        const domain = normalizeWebsite(c.website)
        return domain !== "" && domain.toLowerCase() !== "n/a"
      })
      
      const updatedDomains = [...new Set(selectedWithWebsites.map((c) => normalizeWebsite(c.website)))]
    
      // Step 4: Conditionally run Apollo + Person enrichments
      let apolloResData: ApolloCompany[] = []
      let personResData: ApolloPerson[] = []
    
      if (updatedDomains.length > 0) {
        try {
          // Fetch data and extract it within the same try block
          const [apolloResponse, personResponse] = await Promise.all([
            axios.post<ApolloCompany[]>(`${BACKEND_URL}/apollo-scrape-batch`, { domains: updatedDomains }, headers),
            axios.post<ApolloPerson[]>(`${BACKEND_URL}/find-best-person-batch`, { domains: updatedDomains }, headers),
          ])
          
          // Extract data safely
          apolloResData = apolloResponse.data || []
          personResData = personResponse.data || []
          
        } catch (apiError) {
          console.error("Error fetching Apollo or Person data:", apiError)
          // Continue with empty arrays if API calls fail
        }
      } else {
        console.log("No valid domains to enrich")
      }
    } catch (growjoError) {
      console.error("Error fetching Growjo data:", growjoError)
      // Continue with empty Growjo data if API call fails
    }
    
    // Create maps for Apollo and Person data for easier lookup
    const apolloMap: Record<string, ApolloCompany> = Object.fromEntries(
      // Use explicit type checking to avoid TypeScript errors
      apolloResData.filter((item): item is ApolloCompany => 
        !!item && typeof item.domain === 'string' && item.domain !== ""
      ).map((item) => [item.domain || "", item])
    )

    const personMap: Record<string, ApolloPerson> = Object.fromEntries(
      // Use explicit type checking to avoid TypeScript errors
      personResData.filter((item): item is ApolloPerson => 
        !!item && typeof item.domain === 'string' && item.domain !== ""
      ).map((item) => [item.domain || "", item])
    )

    // Step 5: Merge enriched results
    const enriched: EnrichedLead[] = selected.map((company) => {
        const companyLower = (company.company || "").toLowerCase()
        const domain = normalizeWebsite(company.website)

        // Use growjoMapData instead of growjoMap
        const growjo: GrowjoCompany = growjoMapData[companyLower] || {}
        const apollo: ApolloCompany = apolloMap[domain] || {}
        const person: ApolloPerson = personMap[domain] || {}

        // Calculate scores to determine which data source has more complete information
        const growjoScore = [
          growjo.decider_email, growjo.decider_name, growjo.decider_phone,
          growjo.decider_title, growjo.decider_linkedin
        ].filter(Boolean).length

        const apolloScore = [
          person.email, person.first_name, person.last_name,
          person.title, person.linkedin_url
        ].filter(Boolean).length

        const useApollo = apolloScore > growjoScore

        // Create a decider object with contact information from the best source
        interface Decider {
          firstName: string;
          lastName: string;
          email: string;
          phone: string;
          linkedin: string;
          title: string;
        }

        const decider: Decider = useApollo ? {
          firstName: person.first_name || "",
          lastName: person.last_name || "",
          email: person.email === "email_not_unlocked@domain.com" ? "N/A" : (person.email || ""),
          phone: person.phone_number || "",
          linkedin: person.linkedin_url || "",
          title: person.title || "",
        } : {
          firstName: growjo.decider_name?.split(" ")[0] || "",
          lastName: growjo.decider_name?.split(" ").slice(1).join(" ") || "",
          email: growjo.decider_email === "email_not_unlocked@domain.com" ? "N/A" : (growjo.decider_email || ""),
          phone: growjo.decider_phone || "",
          linkedin: growjo.decider_linkedin || "",
          title: growjo.decider_title || "",
        }

        // Create the enriched lead object with data from all sources
        return {
          id: company.id,
          company: growjo.company_name || company.company || "",
          website: growjo.company_website || apollo.company_website || company.website || "",
          industry: growjo.industry || apollo.industry || company.industry || "",
          productCategory: (growjo.interests && growjo.interests !== "N/A")
            ? growjo.interests
            : Array.isArray(apollo.keywords) ? apollo.keywords.join(", ") : (apollo.keywords || ""),
          businessType: apollo.business_type || "",
          employees: growjo.employee_count || apollo.employee_count || null,
          revenue: growjo.revenue || apollo.annual_revenue_printed || null,
          yearFounded: apollo.founded_year || "",
          bbbRating: company.bbb_rating || "",
          street: company.street || "",
          city: growjo.location?.split(", ")[0] || company.city || "",
          state: growjo.location?.split(", ")[1] || company.state || "",
          companyPhone: company.business_phone || "",
          companyLinkedin: apollo.linkedin_url || "",
          ownerFirstName: decider.firstName || "",
          ownerLastName: decider.lastName || "",
          ownerTitle: decider.title || "",
          ownerLinkedin: decider.linkedin || "",
          ownerPhoneNumber: decider.phone || "",
          ownerEmail: decider.email || "",
          source: getSource(growjo, apollo, person),
        } as EnrichedLead
      }
  )

    // Upload the newly enriched leads to the database if they don't already exist
    try {
      // Format the enriched data to match the API requirements
      interface LeadUpload {
        company: string;
        website: string;
        owner_phone_number: string;
        owner_linkedin: string;
        industry: string;
        product_category?: string;
        business_type?: string;
        employees?: number | null;
        revenue?: string | null;
        year_founded?: string;
        bbb_rating?: string;
        street?: string;
        city?: string;
        state?: string;
        company_phone?: string;
        company_linkedin?: string;
        owner_first_name?: string;
        owner_last_name?: string;
        owner_title?: string;
        owner_email?: string;
        source?: string;
      }

      const leadsToUpload: LeadUpload[] = enriched.map((lead) => ({
        company: lead.company || "",
        website: lead.website || "",
        owner_phone_number: lead.ownerPhoneNumber || "",
        owner_linkedin: lead.ownerLinkedin || "",
        industry: lead.industry || "",
        product_category: lead.productCategory,
        business_type: lead.businessType,
        employees: lead.employees,
        revenue: lead.revenue,
        year_founded: lead.yearFounded,
        bbb_rating: lead.bbbRating,
        street: lead.street,
        city: lead.city,
        state: lead.state,
        company_phone: lead.companyPhone,
        company_linkedin: lead.companyLinkedin,
        owner_first_name: lead.ownerFirstName,
        owner_last_name: lead.ownerLastName,
        owner_title: lead.ownerTitle,
        owner_email: lead.ownerEmail,
        source: lead.source
      }))
      
      // Only upload if there are leads to upload
      if (leadsToUpload.length > 0) {
        try {
          const uploadResponse = await axios.post(
            `https://data.capraeleadseekers.site/api/upload_leads`,
            leadsToUpload,
            headers
          )
          console.log('Upload response:', uploadResponse.data)
        } catch (apiError) {
          console.error('API error uploading leads:', apiError)
        }
      }
    } catch (uploadError) {
      console.error('Failed to prepare leads for upload:', uploadError)
    }
    
    setEnrichedResults(enriched)
    setShowResults(true)
  } catch (error) {
    console.error("Enrichment failed:", error)
  } finally {
    setLoading(false)
  }
}



  // Render the enrichment results if processing is complete
  if (showResults) {
    // Pass enrichedResults as the expected prop for EnrichmentResults component
    return <EnrichmentResults enrichedCompanies={enrichedResults as any} />
  }

  // Otherwise render the company selection interface
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Data Enhancement</h1>
        <p className="text-muted-foreground">Enrich company data with additional information</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Companies</CardTitle>
          <CardDescription>Select companies to enrich with additional data</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input type="search" placeholder="Search companies..." className="pl-8" />
              </div>
              <Button
                variant="outline"
                size="sm"
                className="gap-1"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter className="h-4 w-4" />
                {showFilters ? "Hide Filters" : "Show Filters"}
              </Button>
            </div>
            {showFilters && (
                <div className="flex flex-wrap gap-4 my-4">
                  <Input
                    placeholder="Industry (e.g. Software)"
                    value={industryFilter}
                    onChange={(e) => setIndustryFilter(e.target.value)}
                    className="w-[240px]"
                  />
                  <Input
                    placeholder="City (e.g. Los Angeles)"
                    value={cityFilter}
                    onChange={(e) => setCityFilter(e.target.value)}
                    className="w-[240px]"
                  />
                  <Input
                    placeholder="State (e.g. CA)"
                    value={stateFilter}
                    onChange={(e) => setStateFilter(e.target.value)}
                    className="w-[240px]"
                  />
                  <Input
                    placeholder="BBB Rating (e.g. A+)"
                    value={bbbRatingFilter}
                    onChange={(e) => setBbbRatingFilter(e.target.value)}
                    className="w-[240px]"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setIndustryFilter("")
                      setCityFilter("")
                      setStateFilter("")
                      setBbbRatingFilter("")
                    }}
                  >
                    <X className="h-4 w-4 mr-1" />
                    Clear Filters
                  </Button>
                </div>
              )}

            
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectAll}
                        onCheckedChange={handleSelectAll}
                        aria-label="Select all"
                      />
                    </TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Street</TableHead>
                    <TableHead>City</TableHead>
                    <TableHead>State</TableHead>
                    <TableHead>BBB Rating</TableHead>
                    <TableHead>Company Phone</TableHead>
                    <TableHead>Website</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLeads.map((company) => (
                    <TableRow key={company.id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedCompanies.includes(company.id)}
                          onCheckedChange={() => handleSelectCompany(company.id)}
                          aria-label={`Select ${company.company}`}
                        />
                      </TableCell>
                      <TableCell className="font-medium">{company.company}</TableCell>
                      <TableCell>{company.industry}</TableCell>
                      <TableCell>{company.street}</TableCell>
                      <TableCell>{company.city}</TableCell>
                      <TableCell>{company.state}</TableCell>
                      <TableCell>{company.bbb_rating}</TableCell>
                      <TableCell>{company.business_phone}</TableCell>
                      <TableCell>{company.website}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="flex justify-between items-center">
              <p className="text-sm text-muted-foreground">
                {selectedCompanies.length} of {filteredLeads.length} selected
              </p>
              <Button 
                onClick={handleStartEnrichment} 
                disabled={selectedCompanies.length === 0 || loading}
                type="button"
              >
                {loading ? "Enriching..." : "Start Enrichment"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}