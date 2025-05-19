"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Download, Search, ArrowRight, Save } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import * as XLSX from "xlsx"
import { useLeads } from "@/components/LeadsProvider"
import { addUniqueIdsToLeads } from "@/lib/leadUtils"
import axios from "axios"

interface ScraperResultsProps {
  data: any[]
}

export function ScraperResults({ data }: { data: string | any[] }) {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState("")
  const [leads, setLeads] = useState<any[]>([])
  const [exportFormat, setExportFormat] = useState("csv")
  const { setLeads: setGlobalLeads } = useLeads()
  const textareaRefs = useRef<(HTMLTextAreaElement | null)[]>([])
  const [updatedLeads, setUpdatedLeads] = useState<any[]>([])

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
  // Normalize the data
  const normalizedWithoutIds = parsedData.map((item, idx) => ({
    lead_id: item.lead_id, // Temporary ID that will be replaced by addUniqueIdsToLeads
    company: item.Company || item.company || "",
    website: item.Website || item.website || "",
    industry: item.Industry || item.industry || "",
    street: item.Street || item.street || "",
    city: item.City || item.city || "",
    state: item.State || item.state || "",
    bbb_rating: item.BBB_rating || item.bbb_rating || "",
    business_phone: item.Business_phone || item.business_phone || "",
  }));
  
  // Apply unique IDs using the hash function
  const normalized = addUniqueIdsToLeads(normalizedWithoutIds);
  
  setLeads(normalized)
  setGlobalLeads(normalized);
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

  const handleCellChange = (rowIdx: number, field: string, value: string) => {
    setLeads(prev =>
      prev.map((row, idx) =>
        idx === rowIdx ? { ...row, [field]: value } : row
      )
    );
  
    const leadId = leads[rowIdx].lead_id;
  
    setUpdatedLeads(prev => {
      const existing = prev.find(item => item.lead_id === leadId);
      
      if (existing) {
        return prev.map(item =>
          item.lead_id === leadId
            ? { ...item, [field]: value }
            : item
        );
      } else {
        return [...prev, { lead_id: leadId, [field]: value }];
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
    router.push("?tab=enhancement")
  }

  const handleSave = async () => {
    try {
      // Prepare data for batch update API
      // const batchUpdateData = leads.map(lead => ({
      //   lead_id: lead.id,
      //   company: lead.company,
      //   website: lead.website,
      //   industry: lead.industry,
      //   street: lead.street,
      //   city: lead.city,
      //   state: lead.state,
      //   bbb_rating: lead.bbb_rating,
      //   business_phone: lead.business_phone,
      // }));
      console.log('Batch update data:',updatedLeads);
      // Make API call to batch update endpoint
      const FETCH_DB_API = `${process.env.NEXT_PUBLIC_DATABASE_URL}/leads/batch`;
      const response = await axios.put(
        FETCH_DB_API,updatedLeads)
      // if (!response?.ok) {
        // throw new Error(`HTTP error! status: ${response.status}`);
      // }

      const result = response.data;
      
      // Show success message with details
      console.log('Save successful:', result);
      
      // You can add a toast notification here instead of console.log
      // toast.success(`Successfully updated ${result.updated} leads, skipped ${result.skipped} leads`);
      
      if (result.failed && result.failed.length > 0) {
        console.warn('Some leads failed to update:', result.failed);
        // toast.warning(`${result.failed.length} leads failed to update`);
      }

    } catch (error) {
      console.error('Error saving leads:', error);
      // toast.error('Failed to save leads. Please try again.');
    }
  }


  const filteredResults = leads.filter(
    (result) =>
      result.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.state.toLowerCase().includes(searchTerm.toLowerCase())
  )

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
  const normalizeDisplayValue = (value: any) => {
    return value === null || value === undefined || value === "" ? "N/A" : value
  }
  

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Company Search Results</CardTitle>
            <CardDescription>{leads.length} companies found</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search results..."
                className="w-64 pl-8"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table className="w-full" fixedLayout={false}>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[18%] break-words">Company</TableHead>
                <TableHead className="w-[15%] break-words">Industry</TableHead>
                <TableHead className="w-[25%] break-words">Address</TableHead>
                <TableHead className="w-[10%] break-words">BBB Rating</TableHead>
                <TableHead className="w-[12%] break-words">Phone</TableHead>
                <TableHead className="w-[20%]">Website</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredResults.length > 0 ? (
                filteredResults.map((result, rowIdx) => (
                  <TableRow key={result.id}>
                    <TableCell className="break-words">
                      <textarea
                        className="font-medium border-b w-full bg-transparent break-words resize-none min-h-[24px] overflow-hidden"
                        value={normalizeDisplayValue(result.company)}
                        onChange={e => handleCellChange(rowIdx, "company", e.target.value)}
                        rows={1}
                        ref={(el) => {
                          textareaRefs.current[rowIdx * 3] = el;
                        }}
                      />
                    </TableCell>
                    <TableCell className="break-words">
                      <textarea
                        className="border-b w-full bg-transparent break-words resize-none min-h-[24px] overflow-hidden"
                        value={normalizeDisplayValue(result.industry)}
                        onChange={e => handleCellChange(rowIdx, "industry", e.target.value)}
                        rows={1}
                        ref={(el) => {
                          textareaRefs.current[rowIdx * 3 + 1] = el;
                        }}
                      />
                    </TableCell>
                    <TableCell className="break-words">
                      <textarea
                        className="border-b w-full bg-transparent break-words resize-none min-h-[24px] overflow-hidden"
                        value={normalizeDisplayValue(result.street)}
                        onChange={e => handleCellChange(rowIdx, "street", e.target.value)}
                        placeholder="Street"
                        rows={1}
                        ref={(el) => {
                          textareaRefs.current[rowIdx * 3 + 2] = el;
                        }}
                      />
                      <div className="flex gap-1 mt-1">
                        <input
                          className="border-b w-1/2 bg-transparent text-sm text-muted-foreground break-words"
                          value={normalizeDisplayValue(result.city)}
                          onChange={e => handleCellChange(rowIdx, "city", e.target.value)}
                          placeholder="City"
                        />
                        <input
                          className="border-b w-1/2 bg-transparent text-sm text-muted-foreground break-words"
                          value={normalizeDisplayValue(result.state)}
                          onChange={e => handleCellChange(rowIdx, "state", e.target.value)}
                          placeholder="State"
                        />
                      </div>
                    </TableCell>
                    <TableCell className="break-words">
                      <input
                        className="border-b w-full bg-transparent break-words"
                        value={normalizeDisplayValue(result.bbb_rating)}
                        onChange={e => handleCellChange(rowIdx, "bbb_rating", e.target.value)}
                      />
                    </TableCell>
                    <TableCell className="break-words">
                      {normalizeDisplayValue(result.business_phone)
                        .split(",")
                        .map((phone: string, i: number) => (
                          <div key={i} className="break-words">
                            {normalizeDisplayValue(phone.trim())}
                          </div>
                        ))}
                    </TableCell>
                    <TableCell>
                      <input
                        className="border-b w-full bg-transparent"
                        value={normalizeDisplayValue(result.website)}
                        onChange={e => handleCellChange(rowIdx, "website", e.target.value)}
                      />
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center">
                    No results found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <div className="text-sm text-muted-foreground" />
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleSave}
          >
            <Save className="mr-2 h-4 w-4" />
            Save
          </Button>
          <Button
            className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600"
            onClick={handleNext}
          >
            <ArrowRight className="mr-2 h-4 w-4" />
            Next
          </Button>
          <Select value={exportFormat} onValueChange={setExportFormat}>
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
  )
}