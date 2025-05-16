"use client"
import React from "react"
import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { EnrichmentResults } from "../components/enrichment-results"
import { Button } from "../components/ui/button"
import { Checkbox } from "../components/ui/checkbox"
import { Input } from "../components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
import { Search, Filter, Download, X } from "lucide-react"
import { useLeads } from "./LeadsProvider"
import type { ApolloCompany, GrowjoCompany, ApolloPerson } from "../types/enrichment"
import axios from "axios"


const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL_P2!
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL!

export function DataEnhancement() {
  const [showResults, setShowResults] = useState(false)
  const { leads } = useLeads()
  const normalizeLeadValue = (val: any) => {
    return val === null || val === undefined || val === "" || val === "NA" || val === "N/A" ? "N/A" : val
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
      
      const validLeads = newlyEnriched
      .filter((lead) =>
        lead.company &&
        lead.ownerEmail &&
        lead.owner_phone_number &&
        lead.source &&
        !["n/a", "not found", "N/A", "", null].includes((lead.owner_phone_number || "").toLowerCase())
      )
      .map((lead) => ({
        company: lead.company,
        website: lead.website,
        owner_linkedin: lead.owner_linkedin,
        owner_phone_number: lead.owner_phone_number,
        owner_first_name: lead.ownerFirstName || "",
        owner_last_name: lead.ownerLastName || "",
        owner_email: lead.ownerEmail || "",
        company_phone: lead.companyPhone || "",
        company_linkedin: lead.companyLinkedin || "",
        owner_title: lead.ownerTitle || "",
        industry: lead.industry || "",
        city: lead.city || "",
        state: lead.state || "",
        source: lead.source || "N/A"
      }));

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
                  {filteredLeads.length > 0 ? (
                    filteredLeads.map((company) => (
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
                          {company.website && company.website !== "N/A" ? (
                            <a 
                              href={company.website.toString().startsWith('http') ? company.website : `https://${company.website}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-500 hover:text-blue-700 hover:underline"
                            >
                              {company.website}
                            </a>
                          ) : (
                            company.website || "N/A"
                          )}
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

            <div className="flex justify-between items-center">
              <p className="text-sm text-muted-foreground">
                {selectedCompanies.length} of {filteredLeads.length} selected
              </p>
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