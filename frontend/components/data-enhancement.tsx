"use client"
import React from "react"
import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { EnrichmentResults } from "../components/enrichment-results"
import { Button } from "../components/ui/button"
import { Checkbox } from "../components/ui/checkbox"
import { Input } from "../components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
import { Search, Filter, Download, X, ExternalLink } from "lucide-react"
import { useLeads } from "./LeadsProvider"
import type { ApolloCompany, GrowjoCompany, ApolloPerson } from "../types/enrichment"
import axios from "axios"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"


const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL_P2!
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL!

export function DataEnhancement() {
  const [showResults, setShowResults] = useState(false)
  const { leads } = useLeads()
  const normalizeLeadValue = (val: any) => {
    return val === null || val === undefined || val === "" || val === "NA" || val === "N/A" ? "N/A" : val
  }
  
  // Function to clean URLs for display (remove http://, https://, www. and anything after the TLD)
  const cleanUrlForDisplay = (url: string): string => {
    if (!url || url === "N/A" || url === "NA") return url;
    
    // First remove http://, https://, and www.
    let cleanUrl = url.toString().replace(/^(https?:\/\/)?(www\.)?/i, "");
    
    // Then truncate everything after the domain (matches common TLDs)
    const domainMatch = cleanUrl.match(/^([^\/\?#]+\.(com|org|net|io|ai|co|gov|edu|app|dev|me|info|biz|us|uk|ca|au|de|fr|jp|ru|br|in|cn|nl|se)).*$/i);
    if (domainMatch) {
      return domainMatch[1];
    }
    
    // If no common TLD found, just truncate at the first slash, question mark or hash
    return cleanUrl.split(/[\/\?#]/)[0];
  }

  const normalizedLeads = leads.map((lead) => ({
    ...lead,
    company: normalizeLeadValue(lead.company),
    website: normalizeLeadValue(lead.website),
    industry: normalizeLeadValue(lead.industry),
    street: normalizeLeadValue(lead.street),
    city: normalizeLeadValue(lead.city),
    state: normalizeLeadValue(lead.state),
    bbb_rating: normalizeLeadValue(lead.bbb_rating),
    business_phone: normalizeLeadValue(lead.business_phone),
  }))

  const [enrichedResults, setEnrichedResults] = useState<any[]>([])
  const [selectedCompanies, setSelectedCompanies] = useState<number[]>([])
  const [selectAll, setSelectAll] = useState(false)
  const [industryFilter, setIndustryFilter] = useState("")
  const [cityFilter, setCityFilter] = useState("")
  const [stateFilter, setStateFilter] = useState("")
  const [bbbRatingFilter, setBbbRatingFilter] = useState("")
  const [showFilters, setShowFilters] = useState(false)
  

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [industryFilter, cityFilter, stateFilter, bbbRatingFilter]);


  const downloadCSV = (data: any[], filename: string) => {
  const headers = Object.keys(data[0])
  const csvRows = [
    headers.join(","), // header row
    ...data.map(row =>
      headers.map(field => `"${(row[field] ?? "").toString().replace(/"/g, '""')}"`).join(",")
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
  

  // Calculate pagination values
  const totalPages = Math.ceil(filteredLeads.length / itemsPerPage)
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredLeads.slice(indexOfFirstItem, indexOfLastItem)

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const pageNumbers = [];
    
    if (totalPages <= 7) {
      // Show all pages if there are 7 or fewer
      for (let i = 1; i <= totalPages; i++) {
        pageNumbers.push(i);
      }
    } else {
      // Always show first and last page, with ellipsis for hidden pages
      pageNumbers.push(1);
      
      // Determine range to show around current page
      let startPage = Math.max(2, currentPage - 2);
      let endPage = Math.min(totalPages - 1, currentPage + 2);
      
      // Adjust if we're near the beginning or end
      if (currentPage <= 4) {
        endPage = 5;
      } else if (currentPage >= totalPages - 3) {
        startPage = totalPages - 4;
      }
      
      // Add ellipsis if needed
      if (startPage > 2) {
        pageNumbers.push('ellipsis');
      }
      
      // Add middle pages
      for (let i = startPage; i <= endPage; i++) {
        pageNumbers.push(i);
      }
      
      // Add ellipsis if needed
      if (endPage < totalPages - 1) {
        pageNumbers.push('ellipsis');
      }
      
      pageNumbers.push(totalPages);
    }
    
    return pageNumbers;
  };


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
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedCompanies([])
    } else {
      setSelectedCompanies(normalizedLeads.map((company) => company.id))
    }
    setSelectAll(!selectAll)
  }

  const handleSelectCompany = (id: number) => {
    if (selectedCompanies.includes(id)) {
      setSelectedCompanies(selectedCompanies.filter((companyId) => companyId !== id))
      setSelectAll(false)
    } else {
      const updated = [...selectedCompanies, id]
      setSelectedCompanies(updated)
      if (updated.length === normalizedLeads.length) {
        setSelectAll(true)
      }
    }
  }

  const normalizeWebsite = (url: string) => {
    return url.replace(/^https?:\/\//, "").replace(/\/$/, "").toLowerCase()
  }

  const getSource = (growjo: any, apollo: any, person: any) => {
    const g = growjo && Object.keys(growjo).some((k) => growjo[k])
    const a = apollo && Object.keys(apollo).some((k) => apollo[k])
    const p = person && Object.keys(person).some((k) => person[k])
    if (g && a) return "Growjo + Apollo"
    if (g) return "Growjo"
    if (a) return "Apollo"
    return "N/A"
  }
const [loading, setLoading] = useState(false)


const handleStartEnrichment = async () => {
  setLoading(true)

  try {
    const selected = normalizedLeads.filter((c) => selectedCompanies.includes(c.id))
    const headers = { headers: { "Content-Type": "application/json" } }

    // 1. Fetch all existing leads from DB
    const dbRes = await axios.get(`${DATABASE_URL}/leads`, headers)
    const dbLeads = Array.isArray(dbRes.data)
  ? dbRes.data
  : Array.isArray(dbRes.data.leads)
    ? dbRes.data.leads
    : []
    const existingNames = new Set(dbLeads.map((lead: any) => lead.company?.toLowerCase()))

    const alreadyInDb = dbLeads.filter((lead: any) =>
      selected.some((s) => s.company.toLowerCase() === lead.company?.toLowerCase())
    )

    const needEnrichment = selected.filter(
      (c) => !existingNames.has(c.company.toLowerCase())
    )

    let enriched: any[] = []

    if (needEnrichment.length > 0) {
      // 2. Scrape from Growjo
      const growjoRes = await axios.post(
        `${BACKEND_URL}/scrape-growjo-batch`,
        needEnrichment.map((c) => ({ company: c.company })),
        headers
      )

      const growjoMap = Object.fromEntries(
        (growjoRes.data || []).map((item: any) => [
          item.company_name?.toLowerCase() || item.input_name?.toLowerCase(),
          item
        ])
      )

      const enrichedWithWebsites = needEnrichment.map((company) => {
        const growjo = growjoMap[company.company.toLowerCase()] || {}
        return {
          ...company,
          website:
            growjo.company_website && growjo.company_website.toLowerCase() !== "not found"
              ? growjo.company_website
              : company.website,
        }
      }).filter((c) => {
        const domain = normalizeWebsite(c.website)
        return domain && domain !== "n/a"
      })

      const updatedDomains = [...new Set(enrichedWithWebsites.map((c) => normalizeWebsite(c.website)))]

      let apolloRes = { data: [] }
      let personRes = { data: [] }

      if (updatedDomains.length > 0) {
        [apolloRes, personRes] = await Promise.all([
          axios.post(`${BACKEND_URL}/apollo-scrape-batch`, { domains: updatedDomains }, headers),
          axios.post(`${BACKEND_URL}/find-best-person-batch`, { domains: updatedDomains }, headers),
        ])
      }

      const apolloMap = Object.fromEntries(
        (apolloRes.data || [])
          .filter((item: any) => item && item.domain)
          .map((item: any) => [item.domain, item])
      )
      const personMap = Object.fromEntries(
        (personRes.data || [])
          .filter((item: any) => item && item.domain)  // 🛡️ Filter out null/undefined or missing domain
          .map((item: any) => [item.domain, item])
      )

      const newlyEnriched = enrichedWithWebsites.map((company) => {
        const domain = normalizeWebsite(company.website)
        const growjo = growjoMap[company.company.toLowerCase()] || {}
        const apollo = apolloMap[domain] || {}
        const person = personMap[domain] || {}

        const growjoScore = [
          growjo.decider_email, growjo.decider_name, growjo.decider_phone,
          growjo.decider_title, growjo.decider_linkedin
        ].filter(Boolean).length

        const apolloScore = [
          person.email, person.first_name, person.last_name,
          person.title, person.linkedin_url
        ].filter(Boolean).length

        const useApollo = apolloScore > growjoScore

        const decider = useApollo
          ? {
              firstName: person.first_name || "",
              lastName: person.last_name || "",
              email: person.email === "email_not_unlocked@domain.com" ? "N/A" : (person.email || ""),
              phone: person.phone_number || "",
              linkedin: person.linkedin_url || "",
              title: person.title || "",
            }
          : {
              firstName: growjo.decider_name?.split(" ")[0] || "",
              lastName: growjo.decider_name?.split(" ").slice(1).join(" ") || "",
              email: growjo.decider_email === "email_not_unlocked@domain.com" ? "N/A" : (growjo.decider_email || ""),
              phone: growjo.decider_phone || "",
              linkedin: growjo.decider_linkedin || "",
              title: growjo.decider_title || "",
            }

        return {
          company: growjo.company_name || company.company,
          website: growjo.company_website || apollo.company_website || company.website,
          owner_phone_number: decider.phone,
          owner_linkedin: decider.linkedin,
          street: company.street || "",
          // Extra fields (optional)
          industry: growjo.industry || apollo.industry || company.industry,
          productCategory: growjo.interests || (Array.isArray(apollo.keywords) ? apollo.keywords.join(", ") : apollo.keywords || ""),
          businessType: apollo.business_type || "",
          employees: growjo.employee_count || apollo.employee_count,
          revenue: growjo.revenue || apollo.annual_revenue_printed,
          yearFounded: apollo.founded_year || "",
          city: growjo.location?.split(", ")[0] || company.city,
          state: growjo.location?.split(", ")[1] || company.state,
          bbbRating: company.bbb_rating,
          companyPhone: company.business_phone,
          companyLinkedin: apollo.linkedin_url || "",
          ownerFirstName: decider.firstName,
          ownerLastName: decider.lastName,
          ownerTitle: decider.title,
          ownerEmail: decider.email,
          source: getSource(growjo, apollo, person),
        }
      })

      // 3. Upload enriched leads to DB
      
      const normalizeValue = (val: any) =>
        val === null || val === undefined || val === "" || val === "NA" || val === "N/A"
          ? "N/A"
          : val;
      
      const validLeads = newlyEnriched
        .map((lead) => ({
          company: normalizeValue(lead.company),
          website: normalizeValue(lead.website),
          industry: normalizeValue(lead.industry),
          product_category: normalizeValue(lead.productCategory),
          business_type: normalizeValue(lead.businessType),
          employees: typeof lead.employees === "number" ? lead.employees : parseInt(lead.employees) || 0,
          revenue: normalizeValue(lead.revenue),
          year_founded: typeof lead.yearFounded === "number" ? lead.yearFounded : parseInt(lead.yearFounded) || 0,
          bbb_rating: normalizeValue(lead.bbbRating),
          street: normalizeValue(lead.street),
          city: normalizeValue(lead.city),
          state: normalizeValue(lead.state),
          company_phone: normalizeValue(lead.companyPhone),
          company_linkedin: normalizeValue(lead.companyLinkedin),
          owner_first_name: normalizeValue(lead.ownerFirstName),
          owner_last_name: normalizeValue(lead.ownerLastName),
          owner_title: normalizeValue(lead.ownerTitle),
          owner_linkedin: normalizeValue(lead.owner_linkedin),
          owner_phone_number: normalizeValue(lead.owner_phone_number),
          owner_email: normalizeValue(lead.ownerEmail),
          phone: normalizeValue(lead.owner_phone_number),
          source: normalizeValue(lead.source),
        }))
        .filter(
          (lead) =>
            lead.company !== "N/A" &&
            lead.owner_email !== "N/A" &&
            lead.owner_phone_number !== "N/A"
        );
            

      console.log("📦 Uploading sanitized leads:", validLeads);
      console.log("🚀 Payload shape:", JSON.stringify(validLeads, null, 2));

      // Final check before upload
      if (!Array.isArray(validLeads)) {
      console.error("⛔ upload_leads payload must be an array");
      return;
      }

      // for (const lead of validLeads) {
      // if (!lead.company || !lead.owner_email || !lead.phone || !lead.source) {
      //   console.error("⛔ Invalid lead detected:", lead);
      //   return;
      // }
      // }

      try {
        console.log("🚀 Uploading to:", `${DATABASE_URL}/upload_leads`);
        console.log("📦 Final payload:", JSON.stringify(validLeads, null, 2));
      
        const response = await axios.post(
          `${DATABASE_URL}/upload_leads`,
          JSON.stringify(validLeads),
          {
            headers: {
              "Content-Type": "application/json"
            }
          }
        );
      
        console.log("✅ Upload success:", response.data);
      } catch (error: any) {
        console.error("❌ Upload failed:", error.response?.data || error.message);
      }

      enriched = [...alreadyInDb, ...newlyEnriched];

    } else {
      enriched = alreadyInDb
    }

    setEnrichedResults(
      enriched.map((e) => ({
        ...e,
        ownerPhoneNumber: e.owner_phone_number,
        ownerLinkedin: e.owner_linkedin,
        // optionally preserve the snake_case keys too or remove them
      }))
    )
    setShowResults(true)
  } catch (error) {
    console.error("Enrichment failed:", error)
  } finally {
    setLoading(false)
  }
}




  if (showResults) {
    return <EnrichmentResults enrichedCompanies={enrichedResults} />
  }

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

            {/* Pagination controls */}
            {filteredLeads.length > 0 && (
              <div className="mb-4 flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filteredLeads.length)} of {filteredLeads.length} results
                </div>
                
                <div className="flex items-center gap-4">
                  <Select value={itemsPerPage.toString()} onValueChange={(value) => {
                    setItemsPerPage(Number(value));
                    setCurrentPage(1); // Reset to first page when changing items per page
                  }}>
                    <SelectTrigger className="w-[120px]">
                      <SelectValue placeholder="Items per page" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="25">25 per page</SelectItem>
                      <SelectItem value="50">50 per page</SelectItem>
                      <SelectItem value="100">100 per page</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Pagination>
                    <PaginationContent>
                      <PaginationItem>
                        <PaginationPrevious 
                          onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                          aria-disabled={currentPage === 1}
                          className={currentPage === 1 ? "pointer-events-none opacity-50" : ""}
                        />
                      </PaginationItem>
                      
                      {getPageNumbers().map((page, index) => (
                        <PaginationItem key={index}>
                          {page === 'ellipsis' ? (
                            <PaginationEllipsis />
                          ) : (
                            <PaginationLink
                              isActive={page === currentPage}
                              onClick={() => setCurrentPage(Number(page))}
                            >
                              {page}
                            </PaginationLink>
                          )}
                        </PaginationItem>
                      ))}
                      
                      <PaginationItem>
                        <PaginationNext 
                          onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                          aria-disabled={currentPage === totalPages}
                          className={currentPage === totalPages ? "pointer-events-none opacity-50" : ""}
                        />
                      </PaginationItem>
                    </PaginationContent>
                  </Pagination>
                </div>
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
                  {currentItems.length > 0 ? (
                    currentItems.map((company) => (
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
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {company.website ? cleanUrlForDisplay(company.website) : "N/A"}
                            {company.website && company.website !== "N/A" && company.website !== "NA" && (
                              <a
                                href={company.website.toString().startsWith('http') ? company.website : `https://${company.website}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-500 hover:text-blue-700"
                                title="Open website in new tab"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <ExternalLink className="h-4 w-4" />
                              </a>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow key="no-results">
                      <TableCell colSpan={9} className="text-center">
                        No results found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>

              </Table>
            </div>

            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                {selectedCompanies.length} of {filteredLeads.length} selected
              </div>
              <Button onClick={handleStartEnrichment} disabled={selectedCompanies.length === 0 || loading}>
                {loading ? "Enriching..." : "Start Enrichment"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}