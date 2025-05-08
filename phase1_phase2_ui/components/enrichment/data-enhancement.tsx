"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EnrichmentResults } from "@/components/enrichment/enrichment-results"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Filter, Download } from "lucide-react"

export function DataEnhancement() {
  const [showResults, setShowResults] = useState(false)
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([])
  const [selectAll, setSelectAll] = useState(false)

  const companies = [
    { id: "1", name: "Acme Inc", website: "acme.com", industry: "Software" },
    { id: "2", name: "TechCorp", website: "techcorp.io", industry: "Technology" },
    { id: "3", name: "DataSystems", website: "datasystems.co", industry: "Data Analytics" },
    { id: "4", name: "CloudWorks", website: "cloudworks.net", industry: "Cloud Infrastructure" },
    { id: "5", name: "AI Solutions", website: "aisolutions.ai", industry: "Artificial Intelligence" },
  ]

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedCompanies([])
    } else {
      setSelectedCompanies(companies.map((company) => company.id))
    }
    setSelectAll(!selectAll)
  }

  const handleSelectCompany = (id: string) => {
    if (selectedCompanies.includes(id)) {
      setSelectedCompanies(selectedCompanies.filter((companyId) => companyId !== id))
      setSelectAll(false)
    } else {
      setSelectedCompanies([...selectedCompanies, id])
      if (selectedCompanies.length + 1 === companies.length) {
        setSelectAll(true)
      }
    }
  }

  const handleStartEnrichment = () => {
    setShowResults(true)
  }

  if (showResults) {
    return <EnrichmentResults />
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

            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox checked={selectAll} onCheckedChange={handleSelectAll} aria-label="Select all" />
                    </TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Website</TableHead>
                    <TableHead>Industry</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {companies.map((company) => (
                    <TableRow key={company.id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedCompanies.includes(company.id)}
                          onCheckedChange={() => handleSelectCompany(company.id)}
                          aria-label={`Select ${company.name}`}
                        />
                      </TableCell>
                      <TableCell className="font-medium">{company.name}</TableCell>
                      <TableCell>{company.website}</TableCell>
                      <TableCell>{company.industry}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="flex justify-between items-center">
              <p className="text-sm text-muted-foreground">
                {selectedCompanies.length} of {companies.length} selected
              </p>
              <Button onClick={handleStartEnrichment} disabled={selectedCompanies.length === 0}>
                Start Enrichment
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
