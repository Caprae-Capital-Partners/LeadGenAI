"use client"
import React from "react"
import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { EnrichmentResults } from "../components/enrichment-results"
import { Button } from "../components/ui/button"
import { Checkbox } from "../components/ui/checkbox"
import { Input } from "../components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
import { Search, Filter, Download } from "lucide-react"
import { useLeads } from "./LeadsProvider"
import type { ApolloCompany, GrowjoCompany, ApolloPerson } from "../types/enrichment"
import axios from "axios"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL!

export function DataEnhancement() {
  const [showResults, setShowResults] = useState(false)
  const { leads } = useLeads()
  const [enrichedResults, setEnrichedResults] = useState<any[]>([])
  const [selectedCompanies, setSelectedCompanies] = useState<number[]>([])
  const [selectAll, setSelectAll] = useState(false)

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
//   },
//   {
//     id: "2",
//     name: "Datadog",
//     website: "datadoghq.com",
//     industry: "Cloud Monitoring",
//     street: "620 8th Ave",
//     city: "New York",
//     state: "NY",
//     phone: "(866) 329-4466",
//     bbbRating: "A",
//   },
//   {
//     id: "3",
//     name: "Snowflake",
//     website: "snowflake.com",
//     industry: "Data Warehousing",
//     street: "450 Concar Dr",
//     city: "San Mateo",
//     state: "CA",
//     phone: "(844) 766-9355",
//     bbbRating: "A+",
//   },
//   {
//     id: "4",
//     name: "Zapier",
//     website: "zapier.com",
//     industry: "Automation Software",
//     street: "548 Market St",
//     city: "San Francisco",
//     state: "CA",
//     phone: "(415) 555-1234",
//     bbbRating: "A-",
//   },
//   {
//     id: "5",
//     name: "Figma",
//     website: "figma.com",
//     industry: "Design Tools",
//     street: "760 Market St",
//     city: "San Francisco",
//     state: "CA",
//     phone: "(415) 555-5678",
//     bbbRating: "A",
//   },
// ]
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedCompanies([])
    } else {
      setSelectedCompanies(leads.map((company) => company.id))
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
      if (updated.length === leads.length) {
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
    const selected = leads.filter((c) => selectedCompanies.includes(c.id))
    const companyNames = selected.map((c) => c.company)
    const domains = [...new Set(selected.map((c) => normalizeWebsite(c.website)))]

    // Step 1: Pre-pass Growjo to fill missing websites
    const companiesMissingWebsites = selected.filter((c) => !normalizeWebsite(c.website))
    const headers = { headers: { "Content-Type": "application/json" } }

    if (companiesMissingWebsites.length > 0) {
      const preRes = await axios.post(`${BACKEND_URL}/api/scrape-growjo-batch`,
        companiesMissingWebsites.map(c => ({ company: c.company})), headers)

      companiesMissingWebsites.forEach((c, i) => {
        const r = preRes.data[i]
        if (r?.company_website && r.company_website.toLowerCase() !== "not found") {
          c.website = r.company_website
        }
      })
    }

    const updatedDomains = [...new Set(selected.map((c) => normalizeWebsite(c.website)))]

    // Step 2: Batch API calls
    const [growjoRes, apolloRes, personRes] = await Promise.all([
      axios.post(`${BACKEND_URL}/api/scrape-growjo-batch`, companyNames.map((c) => ({ company: c })), headers),
      axios.post(`${BACKEND_URL}/api/apollo-scrape-batch`, { domains: updatedDomains }, headers),
      axios.post(`${BACKEND_URL}/api/find-best-person-batch`, { domains: updatedDomains }, headers),
    ])

    const growjoMap = Object.fromEntries(
      (growjoRes.data as GrowjoCompany[]).map((item) => [
        item.company_name?.toLowerCase() || item.input_name?.toLowerCase(),
        item,
      ])
    )

    const apolloMap = Object.fromEntries(
      (apolloRes.data as ApolloCompany[])
        .filter((item) => item && item.domain)
        .map((item) => [item.domain, item])
    )

    const personMap = Object.fromEntries(
      (personRes.data as ApolloPerson[])
        .filter((item) => item && item.domain)
        .map((item) => [item.domain, item])
    )


    // Step 3: Merge enriched results
    const enriched = selected.map((company) => {
        const companyLower = company.company.toLowerCase()
        const domain = normalizeWebsite(company.website)

        const growjo = growjoMap[companyLower] || {}
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

        const decider = useApollo ? {
          firstName: person.first_name || "",
          lastName: person.last_name || "",
          email: person.email || "",
          phone: person.phone_number || "",
          linkedin: person.linkedin_url || "",
          title: person.title || "",
        } : {
          firstName: growjo.decider_name?.split(" ")[0] || "",
          lastName: growjo.decider_name?.split(" ").slice(1).join(" ") || "",
          email: growjo.decider_email || "",
          phone: growjo.decider_phone || "",
          linkedin: growjo.decider_linkedin || "",
          title: growjo.decider_title || "",
        }

        return {
          id: company.id,
          company: growjo.company_name || company.company,
          website: growjo.company_website || apollo.company_website || company.website,
          industry: growjo.industry || apollo.industry || company.industry,
          productCategory: (growjo.interests && growjo.interests !== "N/A")
            ? growjo.interests
            : Array.isArray(apollo.keywords) ? apollo.keywords.join(", ") : apollo.keywords || "",
          businessType: apollo.business_type || "",
          employees: growjo.employee_count || apollo.employee_count || null,
          revenue: growjo.revenue || apollo.annual_revenue_printed || null,
          yearFounded: apollo.founded_year || "",
          bbbRating: company.bbb_rating,
          street: company.street,
          city: growjo.location?.split(", ")[0] || company.city,
          state: growjo.location?.split(", ")[1] || company.state,
          companyPhone: company.business_phone,
          companyLinkedin: apollo.linkedin_url || person.linkedin_url || "",
          ownerFirstName: decider.firstName,
          ownerLastName: decider.lastName,
          ownerTitle: decider.title,
          ownerLinkedin: decider.linkedin,
          ownerPhoneNumber: decider.phone,
          ownerEmail: decider.email,
          source: getSource(growjo, apollo, person),
        }
      }
  )

    setEnrichedResults(enriched)
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
              <Button variant="outline" size="sm" className="gap-1">
                <Filter className="h-4 w-4" />
                Filter
              </Button>
              <Button variant="outline" size="sm" className="gap-1">
                <Download className="h-4 w-4" />
                Export
              </Button>
            </div>

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
                    <TableHead>Website</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Street</TableHead>
                    <TableHead>City</TableHead>
                    <TableHead>State</TableHead>
                    <TableHead>Company Phone</TableHead>
                    <TableHead>BBB Rating</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leads.map((company) => (
                    <TableRow key={company.id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedCompanies.includes(company.id)}
                          onCheckedChange={() => handleSelectCompany(company.id)}
                          aria-label={`Select ${company.company}`}
                        />
                      </TableCell>
                      <TableCell className="font-medium">{company.company}</TableCell>
                      <TableCell>{company.website}</TableCell>
                      <TableCell>{company.industry}</TableCell>
                      <TableCell>{company.street}</TableCell>
                      <TableCell>{company.city}</TableCell>
                      <TableCell>{company.state}</TableCell>
                      <TableCell>{company.business_phone}</TableCell>
                      <TableCell>{company.bbb_rating}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="flex justify-between items-center">
              <p className="text-sm text-muted-foreground">
                {selectedCompanies.length} of {leads.length} selected
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
