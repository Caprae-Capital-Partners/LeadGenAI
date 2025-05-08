"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import { Search, Download, ArrowLeft, X } from "lucide-react"
import { useRouter } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

export function EnrichmentResults() {
  const router = useRouter()
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>(["1", "2", "3", "4", "5"])
  const [selectAll, setSelectAll] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [employeesFilter, setEmployeesFilter] = useState("")
  const [revenueFilter, setRevenueFilter] = useState("")
  const [filteredCompanies, setFilteredCompanies] = useState<any[]>([])

  const enrichedCompanies = [
    {
      id: "1",
      company: "Acme Inc",
      website: "acme.com",
      industry: "Software & Technology",
      product: "Enterprise Software",
      businessType: "B2B",
      employees: 120,
      employeesDisplay: "120 employees",
      revenue: 25000000,
      revenueDisplay: "$25.0M",
      founded: "2010",
      address: "123 Tech Blvd, San Francisco, CA",
      rating: "A+",
      contactName: "John Smith",
      title: "CTO",
      email: "john@acme.com",
      phone: "+1 (555) 123-4567",
      linkedin: "linkedin.com/in/johnsmith",
    },
    {
      id: "2",
      company: "TechCorp",
      website: "techcorp.io",
      industry: "Software & Technology",
      product: "SaaS Platform",
      businessType: "B2B",
      employees: 45,
      employeesDisplay: "45 employees",
      revenue: 5000000,
      revenueDisplay: "$5.0M",
      founded: "2018",
      address: "456 Innovation Way, Austin, TX",
      rating: "A",
      contactName: "Sarah Johnson",
      title: "CEO",
      email: "sarah@techcorp.io",
      phone: "+1 (555) 987-6543",
      linkedin: "linkedin.com/in/sarahjohnson",
    },
    {
      id: "3",
      company: "DataSystems",
      website: "datasystems.co",
      industry: "Software & Technology",
      product: "Data Analytics",
      businessType: "B2B2C",
      employees: 320,
      employeesDisplay: "320 employees",
      revenue: 75000000,
      revenueDisplay: "$75.0M",
      founded: "2005",
      address: "789 Data Drive, New York, NY",
      rating: "A+",
      contactName: "Michael Chen",
      title: "CIO",
      email: "michael@datasystems.co",
      phone: "+1 (555) 456-7890",
      linkedin: "linkedin.com/in/michaelchen",
    },
    {
      id: "4",
      company: "CloudWorks",
      website: "cloudworks.net",
      industry: "Software & Technology",
      product: "Cloud Infrastructure",
      businessType: "B2B",
      employees: 150,
      employeesDisplay: "150 employees",
      revenue: 30000000,
      revenueDisplay: "$30.0M",
      founded: "2012",
      address: "321 Cloud Ave, Seattle, WA",
      rating: "B+",
      contactName: "Emily Davis",
      title: "VP of Sales",
      email: "emily@cloudworks.net",
      phone: "+1 (555) 234-5678",
      linkedin: "linkedin.com/in/emilydavis",
    },
    {
      id: "5",
      company: "AI Solutions",
      website: "aisolutions.ai",
      industry: "Software & Technology",
      product: "Artificial Intelligence",
      businessType: "B2B",
      employees: 35,
      employeesDisplay: "35 employees",
      revenue: 3000000,
      revenueDisplay: "$3.0M",
      founded: "2020",
      address: "555 AI Parkway, Boston, MA",
      rating: "A-",
      contactName: "David Wilson",
      title: "Founder",
      email: "david@aisolutions.ai",
      phone: "+1 (555) 876-5432",
      linkedin: "linkedin.com/in/davidwilson",
    },
  ]

  // Parse revenue string to number
  const parseRevenue = (revenueStr: string): number | null => {
    revenueStr = revenueStr.toLowerCase().trim()

    // Remove $ and commas
    revenueStr = revenueStr.replace(/[$,]/g, "")

    // Handle K, M, B suffixes
    let multiplier = 1
    if (revenueStr.endsWith("k")) {
      multiplier = 1000
      revenueStr = revenueStr.slice(0, -1)
    } else if (revenueStr.endsWith("m")) {
      multiplier = 1000000
      revenueStr = revenueStr.slice(0, -1)
    } else if (revenueStr.endsWith("b")) {
      multiplier = 1000000000
      revenueStr = revenueStr.slice(0, -1)
    }

    const value = Number.parseFloat(revenueStr)
    return isNaN(value) ? null : value * multiplier
  }

  // Parse filter string to get operation and value
  const parseFilter = (  filterStr: string,  isRevenue = false): { operation: string; value: number | null; upper?: number | null } => 
    {
      filterStr = filterStr.toLowerCase().trim()

      const result = {
        operation: "exact",
        value: null as number | null,
        upper: null as number | null,
      }

      // Handle range: e.g., "100 - 400"
      const rangeMatch = filterStr.match(/^(\d+(?:[kmb]?)?)\s*-\s*(\d+(?:[kmb]?)?)$/)
      if (rangeMatch) {
        const val1 = isRevenue ? parseRevenue(rangeMatch[1]) : parseInt(rangeMatch[1])
        const val2 = isRevenue ? parseRevenue(rangeMatch[2]) : parseInt(rangeMatch[2])
        result.operation = "between"
        result.value = val1 ?? null
        result.upper = val2 ?? null
        return result
      }

      // Greater than or equal
      if (filterStr.startsWith(">=")) {
        result.operation = "greater than or equal"
        filterStr = filterStr.slice(2).trim()
      }
      // Greater than
      else if (filterStr.startsWith(">")) {
        result.operation = "greater than"
        filterStr = filterStr.slice(1).trim()
      }
      // Less than or equal
      else if (filterStr.startsWith("<=")) {
        result.operation = "less than or equal"
        filterStr = filterStr.slice(2).trim()
      }
      // Less than
      else if (filterStr.startsWith("<")) {
        result.operation = "less than"
        filterStr = filterStr.slice(1).trim()
      }

      // Parse value
      if (isRevenue) {
        result.value = parseRevenue(filterStr)
      } else {
        result.value = parseInt(filterStr)
      }

      return result
    }


  // Apply filters to the data
  useEffect(() => {
    let filtered = [...enrichedCompanies]

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(
        (company) =>
          company.company.toLowerCase().includes(term) ||
          company.website.toLowerCase().includes(term) ||
          company.industry.toLowerCase().includes(term) ||
          company.product.toLowerCase().includes(term) ||
          company.contactName.toLowerCase().includes(term),
      )
    }

    // Apply employees filter
    if (employeesFilter) {
      const { operation, value, upper } = parseFilter(employeesFilter)
      if (value !== null) {
        filtered = filtered.filter((company) => {
          if (operation === "exact") return company.employees === value
          if (operation === "less than") return company.employees < value
          if (operation === "less than or equal") return company.employees <= value
          if (operation === "greater than") return company.employees > value
          if (operation === "greater than or equal") return company.employees >= value
          if (operation === "between") return company.employees >= value && company.employees <= (upper ?? value)
          return true
        })
      }
    }


    // Apply revenue filter
    if (revenueFilter) {
      const { operation, value, upper } = parseFilter(revenueFilter, true)
      if (value !== null) {
        filtered = filtered.filter((company) => {
          if (operation === "exact") return company.revenue === value
          if (operation === "less than") return company.revenue < value
          if (operation === "less than or equal") return company.revenue <= value
          if (operation === "greater than") return company.revenue > value
          if (operation === "greater than or equal") return company.revenue >= value
          if (operation === "between") return company.revenue >= value && company.revenue <= (upper ?? value)
          return true
        })
      }
    }


    setFilteredCompanies(filtered)
  }, [searchTerm, employeesFilter, revenueFilter])

  // Initialize filtered companies
  useEffect(() => {
    setFilteredCompanies(enrichedCompanies)
  }, [])

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedCompanies([])
    } else {
      setSelectedCompanies(filteredCompanies.map((company) => company.id))
    }
    setSelectAll(!selectAll)
  }

  const handleSelectCompany = (id: string) => {
    if (selectedCompanies.includes(id)) {
      setSelectedCompanies(selectedCompanies.filter((companyId) => companyId !== id))
      setSelectAll(false)
    } else {
      setSelectedCompanies([...selectedCompanies, id])
      if (selectedCompanies.length + 1 === filteredCompanies.length) {
        setSelectAll(true)
      }
    }
  }

  const handleBack = () => {
    router.push("?tab=data-enhancement")
    // Reload the page to reset the state
    window.location.reload()
  }

  const clearFilter = (filterType: "search" | "employees" | "revenue") => {
    if (filterType === "search") setSearchTerm("")
    if (filterType === "employees") setEmployeesFilter("")
    if (filterType === "revenue") setRevenueFilter("")
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
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search results..."
                  className="pl-8"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                {searchTerm && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => clearFilter("search")}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="relative min-w-[200px]">
                      <Input
                        type="text"
                        placeholder="Filter by employees..."
                        value={employeesFilter}
                        onChange={(e) => setEmployeesFilter(e.target.value)}
                      />
                      {employeesFilter && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => clearFilter("employees")}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{'>100'} → greater than 100</p>
                    <p>{'>=100'} → at least 100</p>
                    <p>{'<100'} → less than 100</p>
                    <p>{'<=100'} → at most 100</p>
                    <p>{'100 - 400'} → between 100 and 400</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="relative min-w-[200px]">
                      <Input
                        type="text"
                        placeholder="Filter by revenue..."
                        value={revenueFilter}
                        onChange={(e) => setRevenueFilter(e.target.value)}
                      />
                      {revenueFilter && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3"
                          onClick={() => clearFilter("revenue")}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{'>100'} → greater than 100</p>
                    <p>{'>=100'} → at least 100</p>
                    <p>{'<100'} → less than 100</p>
                    <p>{'<=100'} → at most 100</p>
                    <p>{'100 - 400'} → between 100 and 400</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <Button variant="outline" size="sm" className="gap-1 ml-auto">
                <Download className="h-4 w-4" />
                Export
              </Button>
            </div>

            {/* Active filters */}
            {(searchTerm || employeesFilter || revenueFilter) && (
              <div className="flex flex-wrap gap-2">
                {searchTerm && (
                  <Badge variant="outline" className="flex items-center gap-1">
                    Search: {searchTerm}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 ml-1"
                      onClick={() => clearFilter("search")}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
                {employeesFilter && (
                  <Badge variant="outline" className="flex items-center gap-1">
                    Employees: {employeesFilter}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 ml-1"
                      onClick={() => clearFilter("employees")}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
                {revenueFilter && (
                  <Badge variant="outline" className="flex items-center gap-1">
                    Revenue: {revenueFilter}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 ml-1"
                      onClick={() => clearFilter("revenue")}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
              </div>
            )}

            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectAll && filteredCompanies.length > 0}
                        onCheckedChange={handleSelectAll}
                        aria-label="Select all"
                      />
                    </TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Website</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Product/Service</TableHead>
                    <TableHead>Business Type</TableHead>
                    <TableHead>Employees</TableHead>
                    <TableHead>Revenue</TableHead>
                    <TableHead>Founded</TableHead>
                    <TableHead>Address</TableHead>
                    <TableHead>BBB Rating</TableHead>
                    <TableHead>Contact Name</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>LinkedIn</TableHead>
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
                            aria-label={`Select ${company.company}`}
                          />
                        </TableCell>
                        <TableCell className="font-medium">{company.company}</TableCell>
                        <TableCell>{company.website}</TableCell>
                        <TableCell>{company.industry}</TableCell>
                        <TableCell>{company.product}</TableCell>
                        <TableCell>{company.businessType}</TableCell>
                        <TableCell>{company.employeesDisplay}</TableCell>
                        <TableCell>{company.revenueDisplay}</TableCell>
                        <TableCell>{company.founded}</TableCell>
                        <TableCell>{company.address}</TableCell>
                        <TableCell>{company.rating}</TableCell>
                        <TableCell>{company.contactName}</TableCell>
                        <TableCell>{company.title}</TableCell>
                        <TableCell>{company.email}</TableCell>
                        <TableCell>{company.phone}</TableCell>
                        <TableCell>{company.linkedin}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={16} className="h-24 text-center">
                        No results found. Try adjusting your filters.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="flex justify-between items-center">
              <p className="text-sm text-muted-foreground">
                {selectedCompanies.filter((id) => filteredCompanies.some((company) => company.id === id)).length} of{" "}
                {filteredCompanies.length} selected for export
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
