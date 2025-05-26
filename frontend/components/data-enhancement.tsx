"use client"
import React, { useMemo, useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "../components/ui/card"
import { EnrichmentResults } from "../components/enrichment-results"
import { Button } from "../components/ui/button"
import { Checkbox } from "../components/ui/checkbox"
import { Input } from "../components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
import { Search, Filter, Download, X, ExternalLink, Save } from "lucide-react"
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
import type { EnrichedCompany } from "@/components/enrichment-results"
import { useEnrichment } from "@/components/EnrichmentProvider"
import Loader from "@/components/ui/loader"
import * as XLSX from "xlsx"
import { toast } from "sonner"
import { useRouter } from "next/navigation";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL_P2!
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL!

export function DataEnhancement() {
  const [showResults, setShowResults] = useState(false)
  const { leads, setLeads } = useLeads()
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const [exportFormat, setExportFormat] = useState("csv")
  const [isSaving, setIsSaving] = useState(false)
  const [localLeads, setLocalLeads] = useState<any[]>([])
  const textareaRefs = useRef<(HTMLTextAreaElement | null)[]>([])
  const [updatedLeads, setUpdatedLeads] = useState<{ id: number }[]>([])
  const router = useRouter();

  // Restore leads from sessionStorage if available
  useEffect(() => {
    const savedLeads = sessionStorage.getItem("leads");
    if (savedLeads) {
      try {
        const parsed = JSON.parse(savedLeads);
        setLeads(parsed);
      } catch (err) {
        console.error("Failed to restore leads from sessionStorage:", err);
      }
    }
  }, [setLeads]);

  // Memoized normalization of leads
  const normalizeLeadValue = (val: any) => {
    const v = (val || "").toString().trim().toLowerCase()
    return v === "" || v === "na" || v === "n/a" || v === "none" || v === "not" || v === "found" || v === "not found"
      ? "N/A"
      : val
  }
  const normalizedLeads = useMemo(() =>
    leads.map((lead) => ({
      ...lead,
      company: normalizeLeadValue(lead.company),
      website: normalizeLeadValue(lead.website),
      industry: normalizeLeadValue(lead.industry),
      street: normalizeLeadValue(lead.street),
      city: normalizeLeadValue(lead.city),
      state: normalizeLeadValue(lead.state),
      bbb_rating: normalizeLeadValue(lead.bbb_rating),
      business_phone: normalizeLeadValue(lead.business_phone),
    })),
    [leads]
  )

  // Keep localLeads in sync with normalizedLeads
  useEffect(() => {
    setLocalLeads(normalizedLeads)
  }, [normalizedLeads])

  // Auto-resize textareas
  useEffect(() => {
    const resizeTextareas = () => {
      textareaRefs.current.forEach(textarea => {
        if (textarea) {
          textarea.style.height = 'auto'
          textarea.style.height = textarea.scrollHeight + 'px'
        }
      })
    }
    resizeTextareas()
    textareaRefs.current = textareaRefs.current.slice(0, localLeads.length * 3)
  }, [localLeads.length])

  // Handle cell change for editing
  const handleCellChange = (leadId: number, field: string, value: string) => {
    setLocalLeads(prev =>
      prev.map((row) =>
        row.id === leadId ? { ...row, [field]: value } : row
      )
    )
    setUpdatedLeads((prev: { id: number }[]) => {
      const existing = prev.find((item: { id: number }) => item.id === leadId)
      if (existing) {
        return prev.map((item: { id: number }) =>
          item.id === leadId
            ? { ...item, [field]: value }
            : item
        )
      } else {
        return [...prev, { id: leadId, [field]: value }]
      }
    })
  }

  // Save changes to backend
  const handleSave = async () => {
    setIsSaving(true);
    try {
      const response = await axios.put(
        `${DATABASE_URL}/leads/batch`,
        updatedLeads,
        { headers: { "Content-Type": "application/json" } }
      );
      toast.success(`Updated ${response.data.updated || updatedLeads.length} lead(s) successfully`);
      setUpdatedLeads([]);
      setLeads(localLeads); // Update global leads state
    } catch (error) {
      toast.error("Failed to save changes. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  // Export functions
  const exportExcel = (data: any[]) => {
    const worksheet = XLSX.utils.json_to_sheet(data)
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, "Enriched Companies")
    const excelBuffer = XLSX.write(workbook, { bookType: "xlsx", type: "array" })
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "enriched-companies.xlsx"
    a.click()
    URL.revokeObjectURL(url)
  }
  const exportJSON = (data: any[]) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "enriched-companies.json"
    a.click()
    URL.revokeObjectURL(url)
  }
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
  const handleExport = () => {
    const dataToExport = sortedFilteredLeads.length > 0 ? sortedFilteredLeads : currentItems;
    if (dataToExport.length === 0) {
      toast.error("No data to export")
      return
    }
    if (exportFormat === "csv") {
      downloadCSV(dataToExport, "companies.csv")
    } else if (exportFormat === "excel") {
      exportExcel(dataToExport)
    } else if (exportFormat === "json") {
      exportJSON(dataToExport)
    }
  }

  // Filtering and pagination
  const [industryFilter, setIndustryFilter] = useState("")
  const [cityFilter, setCityFilter] = useState("")
  const [stateFilter, setStateFilter] = useState("")
  const [bbbRatingFilter, setBbbRatingFilter] = useState("")
  const [showFilters, setShowFilters] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)
  useEffect(() => {
    setCurrentPage(1);
  }, [industryFilter, cityFilter, stateFilter, bbbRatingFilter]);
  const filteredLeads = localLeads.filter((company) => {
    return (
      company.industry.toLowerCase().includes(industryFilter.toLowerCase()) &&
      company.city.toLowerCase().includes(cityFilter.toLowerCase()) &&
      company.state.toLowerCase().includes(stateFilter.toLowerCase()) &&
      company.bbb_rating.toLowerCase().includes(bbbRatingFilter.toLowerCase())
    )
  })

  // Sorting
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'ascending' | 'descending';
  } | null>(null);
  const requestSort = (key: string) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };
  const getSortedData = (data: any[]) => {
    if (!sortConfig) return data;
    return [...data].sort((a, b) => {
      const aValue = (a[sortConfig.key] ?? "").toString().toLowerCase();
      const bValue = (b[sortConfig.key] ?? "").toString().toLowerCase();
      const aIsNA = aValue === "n/a" || aValue === "na" || aValue === "";
      const bIsNA = bValue === "n/a" || bValue === "na" || bValue === "";
      if (aIsNA && !bIsNA) return 1;
      if (!aIsNA && bIsNA) return -1;
      if (sortConfig.direction === 'ascending') {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });
  };
  const sortedFilteredLeads = getSortedData(filteredLeads)
  const totalPages = Math.ceil(sortedFilteredLeads.length / itemsPerPage)
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = sortedFilteredLeads.slice(indexOfFirstItem, indexOfLastItem)
  const getPageNumbers = () => {
    const pageNumbers = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) {
        pageNumbers.push(i);
      }
    } else {
      pageNumbers.push(1);
      let startPage = Math.max(2, currentPage - 2);
      let endPage = Math.min(totalPages - 1, currentPage + 2);
      if (currentPage <= 4) {
        endPage = 5;
      } else if (currentPage >= totalPages - 3) {
        startPage = totalPages - 4;
      }
      if (startPage > 2) {
        pageNumbers.push('ellipsis');
      }
      for (let i = startPage; i <= endPage; i++) {
        pageNumbers.push(i);
      }
      if (endPage < totalPages - 1) {
        pageNumbers.push('ellipsis');
      }
      pageNumbers.push(totalPages);
    }
    return pageNumbers;
  };

  // Select functionality
  const [selectedCompanies, setSelectedCompanies] = useState<number[]>([])
  const [selectAll, setSelectAll] = useState(false)
  const handleSelectAll = () => {
    const visibleIds = currentItems.map(c => c.id);
    if (selectedCompanies.length === visibleIds.length) {
      setSelectedCompanies([]);
      setSelectAll(false)
    } else {
      setSelectedCompanies(visibleIds);
      setSelectAll(true)
    }
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

  // ...rest of your enrichment logic and rendering (not changed for select/checkbox/merge)

  // The rest of your code (enrichment, results, etc.) remains unchanged

  // --- UI rendering below (unchanged except for select/checkbox logic) ---

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
            {sortedFilteredLeads.length > 0 && (
              <div className="mb-4 flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, sortedFilteredLeads.length)} of {sortedFilteredLeads.length} results
                </div>
                <div className="flex items-center gap-4">
                  <Select value={itemsPerPage.toString()} onValueChange={(value) => {
                    setItemsPerPage(Number(value));
                    setCurrentPage(1);
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

            <div className="w-full overflow-x-auto rounded-md border">
              <Table className="w-full table-fixed">
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectAll}
                        onCheckedChange={handleSelectAll}
                        aria-label="Select all"
                      />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => requestSort('company')}
                    >
                      <div className="flex items-center">
                        Company
                        {sortConfig?.key === 'company' && (
                          <span className="ml-2">
                            {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => requestSort('industry')}
                    >
                      <div className="flex items-center">
                        Industry
                        {sortConfig?.key === 'industry' && (
                          <span className="ml-2">
                            {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => requestSort('street')}
                    >
                      <div className="flex items-center">
                        Street
                        {sortConfig?.key === 'street' && (
                          <span className="ml-2">
                            {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => requestSort('city')}
                    >
                      <div className="flex items-center">
                        City
                        {sortConfig?.key === 'city' && (
                          <span className="ml-2">
                            {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => requestSort('state')}
                    >
                      <div className="flex items-center">
                        State
                        {sortConfig?.key === 'state' && (
                          <span className="ml-2">
                            {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => requestSort('bbb_rating')}
                    >
                      <div className="flex items-center">
                        BBB Rating
                        {sortConfig?.key === 'bbb_rating' && (
                          <span className="ml-2">
                            {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => requestSort('business_phone')}
                    >
                      <div className="flex items-center">
                        Company Phone
                        {sortConfig?.key === 'business_phone' && (
                          <span className="ml-2">
                            {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => requestSort('website')}
                    >
                      <div className="flex items-center">
                        Website
                        {sortConfig?.key === 'website' && (
                          <span className="ml-2">
                            {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <>
                    {currentItems.length > 0 &&
                      currentItems.map((company, idx) => (
                        <TableRow key={company.id ?? `${company.company}-${Math.random()}`}>
                          <TableCell>
                            <Checkbox
                              checked={selectedCompanies.includes(company.id)}
                              onCheckedChange={() => handleSelectCompany(company.id)}
                              aria-label={`Select ${company.company}`}
                            />
                          </TableCell>
                          <TableCell>
                            <input
                              value={company.company || ""}
                              onChange={(e) => handleCellChange(company.id, 'company', e.target.value)}
                              className="border-b bg-transparent w-full"
                            />
                          </TableCell>
                          <TableCell>
                            <input
                              value={company.industry || ""}
                              onChange={(e) => handleCellChange(company.id, 'industry', e.target.value)}
                              className="border-b bg-transparent w-full"
                            />
                          </TableCell>
                          <TableCell>
                            <textarea
                              value={company.street || ""}
                              onChange={(e) => handleCellChange(company.id, 'street', e.target.value)}
                              className="border-b bg-transparent w-full resize-none"
                              rows={1}
                              ref={el => { textareaRefs.current[idx * 3 + 2] = el }}
                            />
                          </TableCell>
                          <TableCell>
                            <input
                              value={company.city || ""}
                              onChange={(e) => handleCellChange(company.id, 'city', e.target.value)}
                              className="border-b bg-transparent w-full"
                            />
                          </TableCell>
                          <TableCell>
                            <input
                              value={company.state || ""}
                              onChange={(e) => handleCellChange(company.id, 'state', e.target.value)}
                              className="border-b bg-transparent w-full"
                            />
                          </TableCell>
                          <TableCell>
                            <select
                              value={company.bbb_rating || ""}
                              onChange={(e) => handleCellChange(company.id, 'bbb_rating', e.target.value)}
                              className="border-b bg-transparent"
                            >
                              {['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F'].map((rating) => (
                                <option key={rating} value={rating}>{rating}</option>
                              ))}
                            </select>
                          </TableCell>
                          <TableCell>
                            <input
                              value={company.business_phone || ""}
                              onChange={(e) => handleCellChange(company.id, 'business_phone', e.target.value)}
                              className="border-b bg-transparent w-full"
                            />
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <input
                                value={company.website || ""}
                                onChange={(e) => handleCellChange(company.id, 'website', e.target.value)}
                                className="border-b bg-transparent flex-1"
                                placeholder="Enter website"
                              />
                              {company.website && company.website !== "N/A" && company.website !== "NA" && (
                                <a
                                  href={company.website.toString().startsWith("http") ? company.website : `https://${company.website}`}
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
                      ))}
                    {!loading && currentItems.length === 0 && (
                      <TableRow key="no-results">
                        <TableCell colSpan={9} className="text-center">
                          No results found.
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                </TableBody>
              </Table>
            </div>
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                {selectedCompanies.length} of {sortedFilteredLeads.length} selected
              </div>
              <div className="flex items-center gap-4">
                {loading && (
                  <div className="text-sm font-medium">
                    {/* Progress: {progress}% */}
                  </div>
                )}
                <Button
                  // onClick={...} // your enrichment logic here
                  disabled={selectedCompanies.length === 0 || loading}
                >
                  {loading ? "Enriching..." : "Start Enrichment"}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          <div className="text-sm text-muted-foreground">
            {updatedLeads.length} unsaved changes
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleSave}
              disabled={isSaving || updatedLeads.length === 0}
            >
              <Save className="mr-2 h-4 w-4" />
              {isSaving ? "Saving..." : "Save Changes"}
            </Button>
            <Select
              value={exportFormat}
              onValueChange={(val) => val && setExportFormat(val)}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Format" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="excel">Excel</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={handleExport}>
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        </CardFooter>
      </Card>
      {/* ...rest of your enrichment/results UI */}
    </div>
  )
}