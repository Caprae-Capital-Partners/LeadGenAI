"use client"

import React from "react"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Checkbox } from "../components/ui/checkbox"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
import type { FC } from "react"
import { Search, Download, ArrowLeft, Filter, X } from "lucide-react"

interface EnrichedCompany {
  id: string
  company: string
  website: string
  industry: string
  productCategory: string
  businessType: string
  employees: number | null
  revenue: number | null
  yearFounded: string
  bbbRating: string
  street: string
  city: string
  state: string
  companyPhone: string
  companyLinkedin: string
  ownerFirstName: string
  ownerLastName: string
  ownerTitle: string
  ownerLinkedin: string
  ownerPhoneNumber: string
  ownerEmail: string
  source: string
}

interface EnrichmentResultsProps {
  enrichedCompanies: EnrichedCompany[]
}

export const EnrichmentResults: FC<EnrichmentResultsProps> = ({ enrichedCompanies }) => {
  const router = useRouter()
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([])
  const [selectAll, setSelectAll] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [employeesFilter, setEmployeesFilter] = useState("")
  const [revenueFilter, setRevenueFilter] = useState("")
  const [businessTypeFilter, setBusinessTypeFilter] = useState("")
  const [productFilter, setProductFilter] = useState("")
  const [yearFoundedFilter, setYearFoundedFilter] = useState("")
  const [bbbRatingFilter, setBbbRatingFilter] = useState("")
  const [streetFilter, setStreetFilter] = useState("")
  const [cityFilter, setCityFilter] = useState("")
  const [stateFilter, setStateFilter] = useState("")
  const [sourceFilter, setSourceFilter] = useState("")
  const [filteredCompanies, setFilteredCompanies] = useState<EnrichedCompany[]>([])
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


  const parseRevenue = (revenueStr: string): number | null => {
    revenueStr = revenueStr.toLowerCase().trim().replace(/[$,]/g, "")
    let multiplier = 1
    if (revenueStr.endsWith("k")) multiplier = 1_000, revenueStr = revenueStr.slice(0, -1)
    else if (revenueStr.endsWith("m")) multiplier = 1_000_000, revenueStr = revenueStr.slice(0, -1)
    else if (revenueStr.endsWith("b")) multiplier = 1_000_000_000, revenueStr = revenueStr.slice(0, -1)
    const value = parseFloat(revenueStr)
    return isNaN(value) ? null : value * multiplier
  }

  const parseFilter = (filterStr: string, isRevenue = false) => {
    const result = { operation: "exact", value: null as number | null, upper: null as number | null }
    filterStr = filterStr.toLowerCase().trim()
    const rangeMatch = filterStr.match(/^(\d+(?:[kmb]?)?)\s*-\s*(\d+(?:[kmb]?)?)$/)
    if (rangeMatch) {
      const val1 = isRevenue ? parseRevenue(rangeMatch[1]) : parseInt(rangeMatch[1])
      const val2 = isRevenue ? parseRevenue(rangeMatch[2]) : parseInt(rangeMatch[2])
      return { operation: "between", value: val1, upper: val2 }
    }
    if (filterStr.startsWith(">=")) result.operation = "greater than or equal", filterStr = filterStr.slice(2)
    else if (filterStr.startsWith(">")) result.operation = "greater than", filterStr = filterStr.slice(1)
    else if (filterStr.startsWith("<=")) result.operation = "less than or equal", filterStr = filterStr.slice(2)
    else if (filterStr.startsWith("<")) result.operation = "less than", filterStr = filterStr.slice(1)
    result.value = isRevenue ? parseRevenue(filterStr) : parseInt(filterStr)
    return result
  }

  useEffect(() => {
    let filtered = [...enrichedCompanies]

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(
        (company) =>
          company.company?.toLowerCase().includes(term) ||
          company.website?.toLowerCase().includes(term) ||
          company.industry?.toLowerCase().includes(term) ||
          company.productCategory?.toLowerCase().includes(term) ||
          `${company.ownerFirstName ?? ""} ${company.ownerLastName ?? ""}`.toLowerCase().includes(term)
      )
    }

    if (employeesFilter) {
      const { operation, value, upper } = parseFilter(employeesFilter)
      if (value !== null) {
        filtered = filtered.filter((company) => {
          const val = company.employees ?? 0
          if (operation === "exact") return val === value
          if (operation === "less than") return val < value
          if (operation === "less than or equal") return val <= value
          if (operation === "greater than") return val > value
          if (operation === "greater than or equal") return val >= value
          if (operation === "between") return val >= value && val <= (upper ?? value)
          return true
        })
      }
    }

    if (revenueFilter) {
      const { operation, value, upper } = parseFilter(revenueFilter, true)
      if (value !== null) {
        filtered = filtered.filter((company) => {
          const val = company.revenue ?? 0
          if (operation === "exact") return val === value
          if (operation === "less than") return val < value
          if (operation === "less than or equal") return val <= value
          if (operation === "greater than") return val > value
          if (operation === "greater than or equal") return val >= value
          if (operation === "between") return val >= value && val <= (upper ?? value)
          return true
        })
      }
    }

    if (businessTypeFilter) {
      filtered = filtered.filter((c) => c.businessType.toLowerCase().includes(businessTypeFilter.toLowerCase()))
    }
    if (productFilter) {
      filtered = filtered.filter((company) =>
        company.productCategory?.toLowerCase().includes(productFilter.toLowerCase())
      )
    }

    if (yearFoundedFilter) {
      filtered = filtered.filter((company) =>
        company.yearFounded?.toLowerCase().includes(yearFoundedFilter.toLowerCase())
      )
    }

    if (bbbRatingFilter) {
      filtered = filtered.filter((company) =>
        company.bbbRating?.toLowerCase().includes(bbbRatingFilter.toLowerCase())
      )
    }

    if (streetFilter) {
      filtered = filtered.filter((company) =>
        company.street?.toLowerCase().includes(streetFilter.toLowerCase())
      )
    }

    if (cityFilter) {
      filtered = filtered.filter((company) =>
        company.city?.toLowerCase().includes(cityFilter.toLowerCase())
      )
    }

    if (stateFilter) {
      filtered = filtered.filter((company) =>
        company.state?.toLowerCase().includes(stateFilter.toLowerCase())
      )
    }

    if (sourceFilter) {
      filtered = filtered.filter((company) =>
        company.source?.toLowerCase().includes(sourceFilter.toLowerCase())
      )
    }


    setFilteredCompanies(filtered)
    }, [
      searchTerm,
      employeesFilter,
      revenueFilter,
      businessTypeFilter,
      productFilter,
      yearFoundedFilter,
      bbbRatingFilter,
      streetFilter,
      cityFilter,
      stateFilter,
      sourceFilter,
      enrichedCompanies
    ])

  useEffect(() => {
    setFilteredCompanies(enrichedCompanies)
    setSelectedCompanies(enrichedCompanies.map((c) => c.id))
  }, [enrichedCompanies])

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedCompanies([])
    } else {
      setSelectedCompanies(filteredCompanies.map((c) => c.id))
    }
    setSelectAll(!selectAll)
  }

  const handleSelectCompany = (id: string) => {
    if (selectedCompanies.includes(id)) {
      setSelectedCompanies(selectedCompanies.filter((cid) => cid !== id))
      setSelectAll(false)
    } else {
      const updated = [...selectedCompanies, id]
      setSelectedCompanies(updated)
      if (updated.length === filteredCompanies.length) {
        setSelectAll(true)
      }
    }
  }

  const clearFilter = (type: "search" | "employees" | "revenue" | "business") => {
    if (type === "search") setSearchTerm("")
    if (type === "employees") setEmployeesFilter("")
    if (type === "revenue") setRevenueFilter("")
    if (type === "business") setBusinessTypeFilter("")
  }

  const handleBack = () => {
    router.push("?tab=data-enhancement")
    window.location.reload()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Enhancement</h1>
          <p className="text-muted-foreground">Enrich company data with additional information</p>
        </div>
        <Button variant="outline" onClick={handleBack} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Enrichment Results</CardTitle>
          <CardDescription>{filteredCompanies.length} companies enriched successfully</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Input
                placeholder="Search companies, keywords, or contact"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-[240px]"
              />
              <Button variant="outline" size="sm" onClick={() => setShowFilters(!showFilters)}>
                <Filter className="h-4 w-4 mr-2" />
                {showFilters ? "Hide Filters" : "Show Filters"}
              </Button>
            </div>

            {showFilters && (
              <div className="flex flex-wrap gap-4 my-4">
                <Input
                  placeholder="Employees (e.g. >1000, 50-200)"
                  value={employeesFilter}
                  onChange={(e) => setEmployeesFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Input
                  placeholder="Revenue (e.g. >1M, 500K-2M)"
                  value={revenueFilter}
                  onChange={(e) => setRevenueFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Input
                  placeholder="Business Type (e.g. B2B)"
                  value={businessTypeFilter}
                  onChange={(e) => setBusinessTypeFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Input
                  placeholder="Product Category (e.g. SaaS)"
                  value={productFilter}
                  onChange={(e) => setProductFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Input
                  placeholder="Year Founded (e.g. 2015)"
                  value={yearFoundedFilter}
                  onChange={(e) => setYearFoundedFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Input
                  placeholder="BBB Rating (e.g. A+)"
                  value={bbbRatingFilter}
                  onChange={(e) => setBbbRatingFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Input
                  placeholder="Street"
                  value={streetFilter}
                  onChange={(e) => setStreetFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Input
                  placeholder="City"
                  value={cityFilter}
                  onChange={(e) => setCityFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Input
                  placeholder="State"
                  value={stateFilter}
                  onChange={(e) => setStateFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Input
                  placeholder="Source (e.g. Growjo)"
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  className="w-[240px]"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setEmployeesFilter("")
                    setRevenueFilter("")
                    setBusinessTypeFilter("")
                    setProductFilter("")
                    setYearFoundedFilter("")
                    setBbbRatingFilter("")
                    setStreetFilter("")
                    setCityFilter("")
                    setStateFilter("")
                    setSourceFilter("")
                  }}

                >
                  <X className="h-4 w-4 mr-1" />
                  Clear All
                </Button>
              </div>
            )}

            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox checked={selectAll} onCheckedChange={handleSelectAll} />
                    </TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Website</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Product/Service Category</TableHead>
                    <TableHead>Business Type (B2B, B2B2C)</TableHead>
                    <TableHead>Employees count</TableHead>
                    <TableHead>Revenue</TableHead>
                    <TableHead>Year Founded</TableHead>
                    <TableHead>BBB Rating</TableHead>
                    <TableHead>Street</TableHead>
                    <TableHead>City</TableHead>
                    <TableHead>State</TableHead>
                    <TableHead>Company Phone</TableHead>
                    <TableHead>Company LinkedIn</TableHead>
                    <TableHead>Owner's First Name</TableHead>
                    <TableHead>Owner's Last Name</TableHead>
                    <TableHead>Owner's Title</TableHead>
                    <TableHead>Owner's LinkedIn</TableHead>
                    <TableHead>Owner's Phone Number</TableHead>
                    <TableHead>Owner's Email</TableHead>
                    <TableHead>Source</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCompanies.length > 0 ? (
                    filteredCompanies.map((company) => (
                      <TableRow key={company.id}>
                        <TableCell>
                          <Checkbox
                            checked={selectedCompanies.includes(company.id)}
                            onCheckedChange={() => handleSelectCompany(company.id)}
                          />
                        </TableCell>
                        <TableCell>{company.company}</TableCell>
                        <TableCell>{company.website}</TableCell>
                        <TableCell>{company.industry}</TableCell>
                        <TableCell>{company.productCategory}</TableCell>
                        <TableCell>{company.businessType}</TableCell>
                        <TableCell>{company.employees ?? ""}</TableCell>
                        <TableCell>{company.revenue ?? ""}</TableCell>
                        <TableCell>{company.yearFounded}</TableCell>
                        <TableCell>{company.bbbRating}</TableCell>
                        <TableCell>{company.street}</TableCell>
                        <TableCell>{company.city}</TableCell>
                        <TableCell>{company.state}</TableCell>
                        <TableCell>{company.companyPhone}</TableCell>
                        <TableCell>{company.companyLinkedin}</TableCell>
                        <TableCell>{company.ownerFirstName}</TableCell>
                        <TableCell>{company.ownerLastName}</TableCell>
                        <TableCell>{company.ownerTitle}</TableCell>
                        <TableCell>{company.ownerLinkedin}</TableCell>
                        <TableCell>{company.ownerPhoneNumber}</TableCell>
                        <TableCell>{company.ownerEmail}</TableCell>
                        <TableCell>{company.source}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={22} className="text-center">No results found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
          <div className="flex justify-end mt-4">
            <Button
              onClick={() => downloadCSV(filteredCompanies, "enriched_results.csv")}
              disabled={filteredCompanies.length === 0}
              variant="outline"
              size="sm"
              className="gap-1"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
