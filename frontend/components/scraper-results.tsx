"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Download, Search, ArrowRight, ExternalLink, Save, Trash2 } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import * as XLSX from "xlsx"
import { Lead, useLeads } from "@/components/LeadsProvider"
import { toast } from "sonner";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"
import axios from "axios"

export function ScraperResults({ data, industry, location }: { data: string | any[], industry: string, location: string }) {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState("")
  const [leads, setLeads] = useState<any[]>([])
  const [exportFormat, setExportFormat] = useState("csv")
  const { setLeads: setGlobalLeads } = useLeads()
  const textareaRefs = useRef<(HTMLTextAreaElement | null)[]>([])

  // Updation state
  const [updatedLeads, setUpdatedLeads] = useState<{ id: number }[]>([])
  const [isSaving, setIsSaving] = useState(false)
  const UPDATE_DB_API = `${process.env.NEXT_PUBLIC_DATABASE_URL}/leads/batch`
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)

  const [selectedCompanies, setSelectedCompanies] = useState<number[]>([])
  const [selectAll, setSelectAll] = useState(false)
  const [isIndeterminate, setIsIndeterminate] = useState(false)
  const [showCheckboxes, setShowCheckboxes] = useState(false)

  // Add effect to handle indeterminate state
  useEffect(() => {
    setIsIndeterminate(
      selectedCompanies.length > 0 &&
      selectedCompanies.length < leads.length
    );
  }, [selectedCompanies, leads.length]);

  useEffect(() => {
    let parsedData;
    try {
      // Replace NaN with null in the JSON string if data is a string
      const sanitizedData = typeof data === "string" ? data.replace(/NaN/g, "null") : data;
      // Parse the sanitized data
      parsedData = typeof sanitizedData === "string" ? JSON.parse(sanitizedData) : sanitizedData;
      // Validate that parsedData is an array
      if (!Array.isArray(parsedData)) {
        console.error("Invalid data format: expected an array", parsedData);
        setLeads([]);
        return;
      }
    } catch (error) {
      console.error("Failed to parse data:", error);
      setLeads([]);
      return;
    }
    const defaultNA = (val: any) =>
      val === undefined || val === null || val === "" || val === "NA" ? "N/A" : val;

    // Normalize the data
    const normalizedWithoutIds = parsedData.map((item, idx) => ({
      id: idx + 1,  // Use 1-based index as ID
      lead_id: item.lead_id || "",
      company: defaultNA(item.Company || item.company),
      website: defaultNA(item.Website || item.website),
      industry: defaultNA(item.Industry || item.industry),
      street: defaultNA(item.Street || item.street),
      city: defaultNA(item.City || item.city),
      state: defaultNA(item.State || item.state),
      bbb_rating: defaultNA(item.BBB_rating || item.bbb_rating),
      business_phone: defaultNA(item.Business_phone || item.business_phone)
    }));
    
    setLeads(normalizedWithoutIds)
    setGlobalLeads(normalizedWithoutIds);
    // Reset to first page when data changes
    setCurrentPage(1);
  }, [data]);

  // Auto-resize textareas
  useEffect(() => {
    const resizeTextareas = () => {
      textareaRefs.current.forEach(textarea => {
        if (textarea) {
          textarea.style.height = 'auto';
          textarea.style.height = textarea.scrollHeight + 'px';
        }
      });
    };
    
    resizeTextareas();
    
    // Reset references when leads change
    textareaRefs.current = textareaRefs.current.slice(0, leads.length * 3);
  }, [leads.length]);

  // Auto-resize all textareas when leads data changes
  useEffect(() => {
    if (leads.length > 0) {
      setTimeout(() => {
        textareaRefs.current.forEach(textarea => {
          if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
          }
        });
      }, 0);
    }
  }, [leads]);

  // Reset to first page when search term changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);

  const handleCellChange = (rowIdx: number, field: string, value: string) => {
    setLeads(prev =>
      prev.map((row, idx) =>
        idx === rowIdx ? { ...row, [field]: value } : row
      )
    );
  
    const leadId = leads[rowIdx].id;
  
    setUpdatedLeads((prev: { id: number }[]) => {
      const existing = prev.find((item: { id: number }) => item.id === leadId);
      
      if (existing) {
        return prev.map((item: { id: number }) =>
          item.id === leadId
            ? { ...item, [field]: value }
            : item
        );
      } else {
        return [...prev, { id: leadId, [field]: value }];
      }
    });
  
    // Resize the textarea after content change
    setTimeout(() => {
      const index = field === "company" ? rowIdx * 3 :
                    field === "industry" ? rowIdx * 3 + 1 :
                    field === "street" ? rowIdx * 3 + 2 : -1;
  
      if (index >= 0 && textareaRefs.current[index]) {
        const textarea = textareaRefs.current[index];
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
      }
    }, 0);
  };

  const handleNext = () => {
    router.push(`/enhancement?industry=${encodeURIComponent(industry)}&location=${encodeURIComponent(location)}`)
  }

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Make API call to batch update endpoint
      const response = await axios.put(UPDATE_DB_API,updatedLeads)
      const result = response.data;

      toast.success(`Updated ${result.updated || updatedLeads.length} lead(s) successfully.`);

      if (result.failed && result.failed.length > 0) {
        toast.warning(`${result.failed.length} lead(s) failed to update.`);
      }
      setUpdatedLeads([]);
      setGlobalLeads(leads)
           
    } catch (error: any) {
      console.error('Error saving leads:', error);
      toast.error('Failed to save leads. Please try again.');
    } finally {
      setIsSaving(false)
    }
  }

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedCompanies([])
    } else {
      setSelectedCompanies(currentItems.map((company) => company.id))
    }
    setSelectAll(!selectAll)
  }

  const handleSelectCompany = (index: number) => {
    if (selectedCompanies.includes(index)) {
      setSelectedCompanies(selectedCompanies.filter((idx) => idx !== index))
      setSelectAll(false)
    } else {
      const updated = [...selectedCompanies, index]
      setSelectedCompanies(updated)
      if (updated.length === leads.length) {
        setSelectAll(true)
      }
    }
  }

  
  const filteredResults = leads.filter(
    (result) =>
      result.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.state.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Calculate pagination values
  const totalPages = Math.ceil(filteredResults.length / itemsPerPage)
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredResults.slice(indexOfFirstItem, indexOfLastItem)

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

  const exportCSV = () => {
    const csvRows = [
      Object.keys(leads[0]).join(","),
      ...leads.map(row =>
        Object.values(row).map(val => `"${String(val).replace(/"/g, '""')}"`).join(",")
      )
    ]
    const blob = new Blob([csvRows.join("\n")], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "leads.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(leads, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "leads.json"
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(leads)
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, "Leads")
    const excelBuffer = XLSX.write(workbook, { bookType: "xlsx", type: "array" })
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "leads.xlsx"
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleExport = () => {
    if (exportFormat === "csv") exportCSV()
    else if (exportFormat === "excel") exportExcel()
    else if (exportFormat === "json") exportJSON()
  }

  // Function to clean URLs for display (remove http://, https://, www. and anything after the TLD)
  const cleanUrlForDisplay = (url: string): string => {
    if (!url || typeof url !== 'string' || url === "N/A" || url === "NA") return url;
    
    // First remove http://, https://, and www.
    let cleanUrl = url.replace(/^(https?:\/\/)?(www\.)?/i, "");
    
    // Then truncate everything after the domain (matches common TLDs)
    const domainMatch = cleanUrl.match(/^([^\/\?#]+\.(com|org|net|io|ai|co|gov|edu|app|dev|me|info|biz|us|uk|ca|au|de|fr|jp|ru|br|in|cn|nl|se)).*$/i);
    if (domainMatch) {
      return domainMatch[1];
    }
    
    // If no common TLD found, just truncate at the first slash, question mark or hash
    return cleanUrl.split(/[\/\?#]/)[0];
  }

  const normalizeDisplayValue = (value: any) => {
    if (value === null || value === undefined) return "";
    if (value === "NA") return "N/A";
    return value;
  }
  
  const [isDeleting, setIsDeleting] = useState(false)
  const DELETE_LEADS_API = `${process.env.NEXT_PUBLIC_DATABASE_URL}/leads/delete-multiple`
  
  const handleDelete = async () => {
    if (selectedCompanies.length === 0) {
      toast.error("Please select at least one lead to delete");
      return;
    }
    setIsDeleting(true);
    setLeads(prev => prev.filter((_, idx) => !selectedCompanies.includes(idx)));
    setGlobalLeads(prev => prev.filter((_, idx) => !selectedCompanies.includes(idx)));
    setSelectedCompanies([]);
    setSelectAll(false);
    setShowCheckboxes(false); // Hide checkboxes after deletion
    toast.success("Lead removed successfully.");
    setIsDeleting(false);
  };

  const handleToggleDeleteMode = () => {
    setShowCheckboxes(!showCheckboxes);
    if (showCheckboxes) {
      // If hiding checkboxes, clear selection
      setSelectedCompanies([]);
      setSelectAll(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Company Search Results</CardTitle>
          <div className="flex items-center gap-4">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search results..."
                className="w-80 pl-8"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            {/* Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={handleToggleDeleteMode}
                className={showCheckboxes ? "bg-red-50 text-red-600 border-red-200 hover:bg-red-100" : ""}
                title={showCheckboxes ? "Cancel Delete Mode" : "Delete Items"}
              >
                <Trash2 className={`h-4 w-4 ${showCheckboxes ? "text-red-600" : ""}`} />
              </Button>
              {showCheckboxes && selectedCompanies.length > 0 && (
                <Button
                  variant="outline"
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="text-red-500 hover:text-red-700 hover:bg-red-50"
                >
                  {isDeleting ? "Deleting..." : `Delete (${selectedCompanies.length})`}
                </Button>
              )}
              <Button
                className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600"
                onClick={handleNext}
              >
                <ArrowRight className="mr-2 h-4 w-4" />
                Next
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Table container */}
        <div className="w-full overflow-x-auto relative border rounded-md">
          <Table className="w-full" fixedLayout={false}>
            <TableHeader>
              <TableRow>
                {showCheckboxes && (
                  <TableHead className="w-[50px] sticky top-0 left-0 z-40 bg-background border-r">
                    <Checkbox
                      checked={selectAll}
                      onCheckedChange={handleSelectAll}
                      aria-label="Select all"
                    />
                  </TableHead>
                )}
                <TableHead className={`sticky top-0 ${showCheckboxes ? 'left-[50px]' : 'left-0'} z-30 bg-background border-r text-base font-bold text-white px-6 py-3 whitespace-nowrap min-w-[200px]`}>
                  Company
                </TableHead>
                <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Industry</TableHead>
                <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Address</TableHead>
                <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">BBB Rating</TableHead>
                <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Phone</TableHead>
                <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Website</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentItems.length > 0 ? (
                currentItems.map((result, rowIdx) => {
                  // Calculate the actual index in the filtered results
                  const actualIndex = indexOfFirstItem + rowIdx;
                  return (
                    <TableRow key={result.id}>
                      {showCheckboxes && (
                        <TableCell className="w-[50px] sticky left-0 z-20 bg-inherit border-r">
                          <Checkbox
                            checked={selectedCompanies.includes(actualIndex)}
                            onCheckedChange={() => handleSelectCompany(actualIndex)}
                            aria-label={`Select ${result.company}`}
                          />
                        </TableCell>
                      )}
                      <TableCell className={`sticky ${showCheckboxes ? 'left-[50px]' : 'left-0'} z-10 bg-inherit border-r px-6 py-2 max-w-[240px] align-top`}>
                        <textarea
                          className="font-medium border-b w-full bg-transparent break-words resize-none min-h-[24px] overflow-hidden"
                          value={normalizeDisplayValue(result.company ?? "")}
                          onChange={e => handleCellChange(actualIndex, "company", e.target.value)}
                          rows={1}
                          onBlur={e => {
                            if (e.target.value.trim() === "") {
                              handleCellChange(actualIndex, "company", "N/A")
                            }
                          }}
                          ref={(el) => {
                            textareaRefs.current[actualIndex * 3] = el;
                          }}
                        />
                      </TableCell>
                      <TableCell className="px-6 py-2 max-w-[240px] align-top">
                        <textarea
                          className="border-b w-full bg-transparent break-words resize-none min-h-[24px] overflow-hidden"
                          value={normalizeDisplayValue(result.industry ?? "")}
                          onChange={e => handleCellChange(actualIndex, "industry", e.target.value)}
                          rows={1}
                          onBlur={e => {
                            if (e.target.value.trim() === "") {
                              handleCellChange(actualIndex, "industry", "N/A")
                            }
                          }}
                          ref={(el) => {
                            textareaRefs.current[actualIndex * 3 + 1] = el;
                          }}
                        />
                      </TableCell>
                      <TableCell className="px-6 py-2 max-w-[240px] align-top">
                        <textarea
                          className="border-b w-full bg-transparent break-words resize-none min-h-[24px] overflow-hidden"
                          value={normalizeDisplayValue(result.street)}
                          onChange={e => handleCellChange(actualIndex, "street", e.target.value)}
                          placeholder="Street"
                          rows={1}
                          onBlur={e => {
                            if (e.target.value.trim() === "") {
                              handleCellChange(actualIndex, "street", "N/A")
                            }
                          }}
                          ref={(el) => {
                            textareaRefs.current[actualIndex * 3 + 2] = el;
                          }}
                        />
                        <div className="flex gap-1 mt-1">
                          <input
                            className="border-b w-1/2 bg-transparent text-sm text-muted-foreground break-words"
                            value={normalizeDisplayValue(result.city)}
                            onChange={e => handleCellChange(actualIndex, "city", e.target.value)}
                            onBlur={e => {
                            if (e.target.value.trim() === "") {
                              handleCellChange(actualIndex, "city", "N/A")
                            }
                          }}
                            placeholder="City"
                          />
                          <input
                            className="border-b w-1/2 bg-transparent text-sm text-muted-foreground break-words"
                            value={normalizeDisplayValue(result.state)}
                            onChange={e => handleCellChange(actualIndex, "state", e.target.value)}
                            onBlur={e => {
                            if (e.target.value.trim() === "") {
                              handleCellChange(actualIndex, "state", "N/A")
                            }
                          }}
                            placeholder="State"
                          />
                        </div>
                      </TableCell>
                      <TableCell className="px-6 py-2 max-w-[240px] align-top">
                        <input
                          className="border-b w-full bg-transparent break-words"
                          value={normalizeDisplayValue(result.bbb_rating)}
                          onChange={e => handleCellChange(actualIndex, "bbb_rating", e.target.value)}
                          onBlur={e => {
                            if (e.target.value.trim() === "") {
                              handleCellChange(actualIndex, "bbb_rating", "N/A")
                            }
                          }}
                        />
                      </TableCell>
                      <TableCell className="px-6 py-2 max-w-[240px] align-top">
                        {normalizeDisplayValue(result.business_phone)
                          .split(",")
                          .map((phone: string, i: number) => (
                            <div key={`${result.id}-phone-${i}`} className="break-words">
                              {normalizeDisplayValue(phone.trim())}
                            </div>
                          ))}
                      </TableCell>
                      <TableCell className="px-6 py-2 max-w-[240px] align-top">
                        <div className="flex items-center gap-2">
                          <input
                            className="border-b w-full bg-transparent"
                            value={result.website ? cleanUrlForDisplay(normalizeDisplayValue(result.website)) : ""}
                            onChange={e => handleCellChange(actualIndex, "website", e.target.value)}
                            onBlur={e => {
                            if (e.target.value.trim() === "") {
                              handleCellChange(actualIndex, "website", "N/A")
                            }
                          }}
                            placeholder="Website (domain only)"
                          />
                          {result.website && normalizeDisplayValue(result.website) !== "N/A" && normalizeDisplayValue(result.website) !== "NA" && (
                            <a
                              href={result.website.toString().startsWith('http') ? result.website : `https://${result.website}`}
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
                  );
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    No results found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination at the bottom */}
        {filteredResults.length > 0 && (
          <div className="flex flex-col md:flex-row justify-between items-center mt-4 gap-4 px-4 py-2">
            <div className="text-sm text-muted-foreground">
              Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filteredResults.length)} of {filteredResults.length} results
              {selectedCompanies.length > 0 && (
                <span className="ml-2 text-blue-600">
                  ({selectedCompanies.length} selected)
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-3 px-3 py-2">
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
      </CardContent>
    </Card>
  )
}
