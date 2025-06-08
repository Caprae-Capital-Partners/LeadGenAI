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
import { Search, Download, ArrowLeft, Filter, X, ExternalLink } from "lucide-react"
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
import { useEnrichment } from "@/components/EnrichmentProvider"
import Notif  from "@/components/ui/notif"
import axios from "axios"

interface EnrichmentResultsProps {
  enrichedCompanies: EnrichedCompany[]
  loading?: boolean
  rowClassName?: (company: EnrichedCompany, index: number) => string
}
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL!


export interface EnrichedCompany {
  id: string
  lead_id?: string;
  draft_id?: string; 
  company: string
  website: string
  industry: string
  productCategory: string
  businessType: string
  employees: number | null
  revenue: string | number
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
  sourceType?: "database" | "scraped";
}


export const EnrichmentResults: FC<EnrichmentResultsProps> = ({
  enrichedCompanies,
  loading,
  rowClassName,
}) => {
  const [notif, setNotif] = useState({
    show: false,
    message: "",
    type: "success" as "success" | "error" | "info",
  });
  const showNotification = (message: string, type: "success" | "error" | "info" = "success") => {
    setNotif({ show: true, message, type });

    // Automatically hide after X seconds (let Notif handle it visually)
    // Optional if Notif itself auto-hides — but helpful as backup
    setTimeout(() => {
      setNotif(prev => ({ ...prev, show: false }));
    }, 3500);
  };
  
  const [editableCompanies, setEditableCompanies] = useState<EnrichedCompany[]>([])
  const [editingCell, setEditingCell] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  // const { enrichedCompanies, loading } = useEnrichment()
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
  const handleFieldChange = (id: string, field: keyof EnrichedCompany, value: any) => {
    setEditableCompanies(prev =>
      prev.map(company =>
        company.id === id ? { ...company, [field]: value } : company
      )
    )
  }
  const handleDiscardChanges = () => {
    setEditableCompanies([...enrichedCompanies])
  }

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)


  // Reset to first page when search term or filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, employeesFilter, revenueFilter, businessTypeFilter, productFilter,
    yearFoundedFilter, bbbRatingFilter, streetFilter, cityFilter, stateFilter, sourceFilter]);

  const downloadCSV = (data: any[], filename: string) => {
    const headers = Object.keys(data[0]).filter(header => 
      header !== 'id' && header !== 'lead_id' && header !== 'draft_id'
    )
    const normalizeCSVValue = (field: string, value: any) => {
      const normalized = normalizeDisplayValue(value)
      return field === "source" && normalized === "N/A"
        ? "Not available in any source"
        : normalized
    }

    const csvRows = [
      headers.join(","),
      ...data.map(row =>
        headers.map(field =>
          `"${normalizeCSVValue(field, row[field]).toString().replace(/"/g, '""')}"`
        ).join(",")
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

    if (revenueStr.endsWith("k")) {
      multiplier = 1_000
      revenueStr = revenueStr.slice(0, -1)
    } else if (revenueStr.endsWith("m")) {
      multiplier = 1_000_000
      revenueStr = revenueStr.slice(0, -1)
    } else if (revenueStr.endsWith("b")) {
      multiplier = 1_000_000_000
      revenueStr = revenueStr.slice(0, -1)
    } else {
      // If there's no suffix, treat as-is (e.g. user inputs "50000")
      multiplier = 1
    }

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
          const val = typeof company.revenue === "string"
            ? parseRevenue(company.revenue)
            : company.revenue ?? 0

          if (val === null) return false
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

    setEditableCompanies(filtered)

    setFilteredCompanies(filtered)

    // Initialize all companies as selected if selectAll is true
    if (selectAll) {
      setSelectedCompanies(filtered.map(c => c.id))
    }
  }, [enrichedCompanies, searchTerm, employeesFilter, revenueFilter, businessTypeFilter, productFilter, yearFoundedFilter, bbbRatingFilter, streetFilter, cityFilter, stateFilter, sourceFilter, selectAll])

  // Calculate pagination values
  const totalPages = Math.ceil(filteredCompanies.length / itemsPerPage)
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = editableCompanies.slice(indexOfFirstItem, indexOfLastItem)
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
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
  const normalizeDisplayValue = (value: any) => {
    if (
      value === null ||
      value === undefined ||
      value.toString().trim() === "" ||
      value.toString().trim().toUpperCase() === "NA" ||
      value.toString().trim().toUpperCase() === "N/A" ||
      value.toString().trim().toUpperCase() === "not" ||
      value.toString().trim().toUpperCase() === "found" ||
      value.toString().trim().toLowerCase() === "not found"
    ) {
      return "N/A"
    }

    return value
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

  const clearFilter = (type: "search" | "employees" | "revenue" | "business") => {
    if (type === "search") setSearchTerm("")
    if (type === "employees") setEmployeesFilter("")
    if (type === "revenue") setRevenueFilter("")
    if (type === "business") setBusinessTypeFilter("")
  }

  const handleExportCSVWithCredits = async () => {
    // 1) Grab current user’s role
    const stored = sessionStorage.getItem("user");
    const currentUser = stored ? JSON.parse(stored) : {};
    const role = currentUser.role || "";

    // 2) If they’re a developer, skip all checks
    if (role === "developer") {
      downloadCSV(filteredCompanies, "enriched_results.csv");
      return;
    }

    // 3) Otherwise, do the existing subscription/credits checks
    try {
      const { data: subscriptionInfo } = await axios.get(
        `${DATABASE_URL}/user/subscription_info`,
        { withCredentials: true }
      );

      const planName =
        subscriptionInfo?.subscription?.plan_name?.toLowerCase() || "free";
      const availableCredits =
        subscriptionInfo?.subscription?.credits_remaining ?? 0;
      const requiredCredits = filteredCompanies.length;

      if (planName === "free") {
        showNotification(
          "Exporting is not allowed on the Free tier. Please upgrade your plan.",
          "info"
        );
        return;
      }

      if (availableCredits < requiredCredits) {
        showNotification(
          "Insufficient credits to export all selected leads. Please upgrade or reduce selection.",
          "error"
        );
        return;
      }

      downloadCSV(filteredCompanies, "enriched_results.csv");
    } catch (checkErr) {
      console.error("❌ Failed to verify subscription:", checkErr);
      showNotification(
        "Failed to verify your subscription. Please try again later.",
        "error"
      );
    }
  };
  

  const handleToggleFiltersWithCheck = async () => {
    // 1) Grab the current user from sessionStorage
    const stored = sessionStorage.getItem("user");
    const currentUser = stored ? JSON.parse(stored) : {};
    const role = currentUser.role || "";

    // 2) If they’re a developer, skip subscription check entirely
    if (role === "developer") {
      setShowFilters((prev) => !prev);
      return;
    }

    // 3) Otherwise, fall back to the existing “free‐tier” logic
    try {
      const { data: subscriptionInfo } = await axios.get(
        `${DATABASE_URL}/user/subscription_info`,
        { withCredentials: true }
      );

      const planName =
        subscriptionInfo?.subscription?.plan_name?.toLowerCase() || "free";

      if (planName === "free") {
        showNotification(
          "Advanced filters are disabled on the Free tier. Please upgrade your plan.",
          "info"
        );
        return;
      }

      setShowFilters((prev) => !prev);
    } catch (err) {
      console.error("❌ Failed to verify subscription:", err);
      showNotification(
        "Failed to verify your subscription. Please try again later.",
        "error"
      );
    }
  };
  


  const handleBack = () => {
    router.push("?tab=data-enhancement")
    window.location.reload()
  }

  const handleSaveEditedCompanies = async () => {
    const user = JSON.parse(sessionStorage.getItem("user") || "{}");
    const user_id = user.id || user.user_id || user._id;

    if (!user_id) {
      showNotification("User not found in session. Please re-login.", "error");
      return;
    }

    const draftMap = JSON.parse(sessionStorage.getItem("leadToDraftMap") || "{}");
    const companiesToSave = editableCompanies.filter((c) =>
      selectedCompanies.includes(c.id)
    );

    if (companiesToSave.length === 0) {
      showNotification("Please select at least one company to save.", "info");
      return;
    }

    console.log(`💾 Attempting to save ${companiesToSave.length} companies`);

    for (const [index, c] of companiesToSave.entries()) {
      try {
        const lead_id = c.lead_id || c.id;
        const draftId = draftMap[lead_id]?.draft_id;

        const draftPayload = {
          draft_data: {
            user_id,
            company: c.company,
            website: c.website,
            industry: c.industry,
            product_category: c.productCategory,
            business_type: c.businessType,
            employees: typeof c.employees === "number" ? c.employees : parseInt(c.employees as any) || 0,
            revenue: typeof c.revenue === "string" ? parseFloat(c.revenue.replace(/[^0-9.]/g, "")) : c.revenue,
            year_founded: parseInt(c.yearFounded) || 0,
            bbb_rating: c.bbbRating,
            street: c.street,
            city: c.city,
            state: c.state,
            company_phone: c.companyPhone,
            company_linkedin: c.companyLinkedin,
            owner_first_name: c.ownerFirstName,
            owner_last_name: c.ownerLastName,
            owner_title: c.ownerTitle,
            owner_linkedin: c.ownerLinkedin,
            owner_phone_number: c.ownerPhoneNumber,
            owner_email: c.ownerEmail,
            source: c.source,
          },
          change_summary: "User edited company info",
        };

        const flatPayload = {
          ...draftPayload.draft_data,
          user_id,
        };

        console.log(`📤 (${index + 1}/${companiesToSave.length}) Saving:`, c.company);

        // ✅ Step 1: PUT to /leads/drafts/:draft_id
        if (draftId) {
          const res = await fetch(`https://data.capraeleadseekers.site/api/leads/drafts/${draftId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify(draftPayload),
          });

          const text = await res.text();
          console.log("📥 Draft update response:", text);
          try {
            const data = JSON.parse(text);
            if (!res.ok || data.error) {
              console.error("❌ Failed to update draft:", draftId, data);
              showNotification(`Failed to update draft: ${c.company}`, "error");
            } else {
              console.log(`✅ Draft updated: ${c.company}`);
            }
          } catch {
            console.error("❌ Non-JSON response from draft endpoint");
          }
        } else {
          console.warn(`⚠️ No draft_id for ${c.company}`);
        }

        // ✅ Step 2: POST to /leads/:lead_id/edit
        const editRes = await fetch(`https://data.capraeleadseekers.site/leads/${lead_id}/edit`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(flatPayload),
        });

        const editText = await editRes.text();
        console.log("📥 Edit draft response:", editText);
        try {
          const editJson = JSON.parse(editText);
          if (!editRes.ok || editJson.success === false) {
            console.error("❌ Failed to POST to edit API:", editJson);
            showNotification(`Failed to save edit for ${c.company}`, "error");
          } else {
            console.log(`✅ Edit saved: ${c.company}`);
          }
        } catch {
          console.error("❌ Invalid JSON from /edit");
          showNotification("Unexpected response from /edit", "error");
        }

      } catch (err) {
        console.error("❌ Error saving company:", err);
        showNotification(`Error saving ${c.company}`, "error");
      }
    }

    showNotification("Done saving selected companies.", "success");
  };
  
  
  











  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        {/* <div>
          <h1 className="text-3xl font-bold">Data Enhancement</h1>
          <p className="text-muted-foreground">Enrich company data with additional information</p>
        </div> */}
        {/* <Button variant="outline" onClick={handleBack} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button> */}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Enrichment Results</CardTitle>
          <CardDescription>{filteredCompanies.length} companies enriched successfully</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              {/* Stretched Search Bar */}
              <div className="flex-grow">
                <Input
                  placeholder="Search companies..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full"
                />
              </div>

              {/* Right: Filter + Export + Edit */}
              <div className="flex flex-wrap items-center gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={handleToggleFiltersWithCheck}>
                  <Filter className="h-4 w-4 mr-2" />
                  {showFilters ? "Hide Filters" : "Show Filters"}
                </Button>

                <Button
                  onClick={handleExportCSVWithCredits}
                  disabled={filteredCompanies.length === 0}
                  variant="outline"
                  size="sm"
                  className="gap-1"
                >
                  <Download className="h-4 w-4" />
                  Export CSV
                </Button>

                {isEditing ? (
                  <>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => {
                        setEditableCompanies([...enrichedCompanies])
                        setIsEditing(false)
                      }}
                    >
                      Discard Changes
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => {
                        handleSaveEditedCompanies()
                        setIsEditing(false)
                      }}
                    >
                      Save Changes
                    </Button>
                  </>
                ) : (
                  <Button
                    onClick={() => setIsEditing(true)}
                    variant="outline"
                    size="sm"
                  >
                    Edit
                  </Button>
                )}
              </div>
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

            <div className="w-full overflow-x-auto rounded-md border">
              <div className="w-full overflow-x-auto rounded-md border">
                <Table className="w-full overflow-x-auto">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="px-6 py-2 w-12">
                        <Checkbox checked={selectAll} onCheckedChange={handleSelectAll} />
                      </TableHead>
                      {[
                        "Company",
                        "Website",
                        "Industry",
                        "Product/Service Category",
                        "Business Type (B2B, B2B2C)",
                        "Employees Count",
                        "Revenue",
                        "Year Founded",
                        "BBB Rating",
                        "Street",
                        "City",
                        "State",
                        "Company Phone",
                        "Company LinkedIn",
                        "Owner's First Name",
                        "Owner's Last Name",
                        "Owner's Title",
                        "Owner's LinkedIn",
                        "Owner's Phone Number",
                        "Owner's Email",
                        "Source",
                      ].map((label, i) => (
                        <TableHead
                          key={i}
                          className="text-xs font-semibold text-black px-6 py-2 whitespace-nowrap"
                        >
                          {label}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {currentItems.length > 0 ? (
                      currentItems.map((company, i) => (
                        <TableRow
                          key={company.id}
                          className={
                            rowClassName?.(company, i) ??
                            (company.sourceType === "database"
                              ? "bg-teal-50"
                              : company.sourceType === "scraped"
                                ? "bg-yellow-50"
                                : "")
                          }
                        >
                          <TableCell className="px-6 py-2">
                            <Checkbox
                              checked={selectedCompanies.includes(company.id)}
                              onCheckedChange={() => handleSelectCompany(company.id)}
                            />
                          </TableCell>

                          {[
                            "company",
                            "website",
                            "industry",
                            "productCategory",
                            "businessType",
                            "employees",
                            "revenue",
                            "yearFounded",
                            "bbbRating",
                            "street",
                            "city",
                            "state",
                            "companyPhone",
                            "companyLinkedin",
                            "ownerFirstName",
                            "ownerLastName",
                            "ownerTitle",
                            "ownerLinkedin",
                            "ownerPhoneNumber",
                            "ownerEmail",
                            "source",
                          ].map((field) => {
                            const value = company[field as keyof EnrichedCompany] ?? "";
                            const displayValue = normalizeDisplayValue(value);

                            const isLinkedInField = ["companyLinkedin", "ownerLinkedin"].includes(field);
                            const isValidLink = typeof value === "string" && value.startsWith("http");

                            // Toggle logic only for productCategory
                            if (field === "productCategory") {
                              const isExpanded = expandedRows.has(i);
                              return (
                                <TableCell
                                  key={field}
                                  className="px-6 py-2 text-sm align-top max-w-[240px]"
                                >
                                  <div className={`${isExpanded ? "" : "line-clamp-3"} break-words overflow-hidden`}>
                                    {displayValue}
                                  </div>
                                  {displayValue.length > 100 && (
                                    <button
                                      onClick={() => {
                                        const newSet = new Set(expandedRows);
                                        isExpanded ? newSet.delete(i) : newSet.add(i);
                                        setExpandedRows(newSet);
                                      }}
                                      className="text-xs text-blue-500 hover:underline mt-1 block"
                                    >
                                      {isExpanded ? "Show less" : "Show more"}
                                    </button>
                                  )}
                                </TableCell>
                              );
                            }

                            return (
                              <TableCell
                                key={field}
                                className="px-6 py-2 text-sm align-top whitespace-nowrap"
                                title={displayValue}
                              >
                                {isEditing ? (
                                  <input
                                    type="text"
                                    className="w-full bg-transparent border-b border-muted focus:outline-none text-sm"
                                    value={String(value)}
                                    onChange={(e) =>
                                      handleFieldChange(
                                        company.id,
                                        field as keyof EnrichedCompany,
                                        e.target.value
                                      )
                                    }
                                  />
                                ) : (
                                  // If this cell is “website” and has a non‐empty string value, render a blue <a>…
                                  field === "website" &&
                                    typeof value === "string" &&
                                    value.trim() !== "" ? (
                                    <a
                                      href={value.startsWith("http") ? value : `https://${value}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-500 hover:text-blue-700 truncate"
                                      title={value}
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      {cleanUrlForDisplay(value)}
                                    </a>

                                    // Otherwise, if this field is a LinkedIn field and starts with “http”, render a blue <a>…
                                  ) : isLinkedInField &&
                                    typeof value === "string" &&
                                    value.startsWith("http") ? (
                                    <a
                                      href={value}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-500 hover:text-blue-700 truncate"
                                      title={value}
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      {value.replace(/^https?:\/\/(www\.)?/, "").split("?")[0]}
                                    </a>

                                    // For all other cases, just show the plain text (or “N/A” if empty)
                                  ) : (
                                    displayValue
                                  )
                                )}
                              </TableCell>
                            );
                          })}
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={22} className="text-center py-4">
                          No results found.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>

                </Table>

              </div>
            </div>

            {/* Pagination controls */}
            {filteredCompanies.length > 0 && (
              <div className="mb-4 flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filteredCompanies.length)} of {filteredCompanies.length} results
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

          </div>
          <Notif
            show={notif.show}
            message={notif.message}
            type={notif.type}
            onClose={() => setNotif(prev => ({ ...prev, show: false }))}
          />
        </CardContent>
      </Card>
    </div>
  )
}
