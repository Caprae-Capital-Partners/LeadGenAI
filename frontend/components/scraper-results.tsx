"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Download, Filter, Search, ArrowRight } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useRouter } from "next/navigation"
import { useLeads } from "./LeadsProvider"
import * as XLSX from "xlsx"

// Mock data for demonstration
const mockResults = [
  {
    id: 1,
    company: "Acme Inc",
    website: "acme.com",
    industry: "Software & Technology",
    street: "123 Tech Blvd",
    city: "San Francisco",
    state: "CA",
    bbb_rating: "A+",
    business_phone: "+1 (555) 123-4567",
  },
  {
    id: 2,
    company: "TechCorp",
    website: "techcorp.io",
    industry: "Software & Technology",
    street: "456 Innovation Way",
    city: "Austin",
    state: "TX",
    bbb_rating: "A",
    business_phone: "+1 (555) 987-6543",
  },
  {
    id: 3,
    company: "DataSystems",
    website: "datasystems.co",
    industry: "Software & Technology",
    street: "789 Data Drive",
    city: "New York",
    state: "NY",
    bbb_rating: "A+",
    business_phone: "+1 (555) 456-7890",
  },
  {
    id: 4,
    company: "CloudWorks",
    website: "cloudworks.net",
    industry: "Software & Technology",
    street: "321 Cloud Ave",
    city: "Seattle",
    state: "WA",
    bbb_rating: "B+",
    business_phone: "+1 (555) 234-5678",
  },
  {
    id: 5,
    company: "AI Solutions",
    website: "aisolutions.ai",
    industry: "Software & Technology",
    street: "555 AI Parkway",
    city: "Boston",
    state: "MA",
    bbb_rating: "A-",
    business_phone: "+1 (555) 876-5432",
  },
]

export function ScraperResults() {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState("")
  const { leads, setLeads } = useLeads()
  const [exportFormat, setExportFormat] = useState("csv")

  const handleCellChange = (rowIdx: number, field: string, value: string) => {
    setLeads(prev =>
      prev.map((row, idx) =>
        idx === rowIdx ? { ...row, [field]: value } : row
      )
    )
  }

  const handleNext = () => {
    // Navigate to the data enhancement page
    router.push("?tab=enhancement")
  }

  const filteredResults = leads.filter(
    (result) =>
      result.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.state.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const exportCSV = () => {
    const csvRows = [
      Object.keys(leads[0]).join(","), // header
      ...leads.map(row => Object.values(row).map(val => `"${String(val).replace(/"/g, '""')}"`).join(","))
    ];
    const blob = new Blob([csvRows.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "leads.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(leads, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "leads.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(leads);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Leads");
    const excelBuffer = XLSX.write(workbook, { bookType: "xlsx", type: "array" });
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "leads.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExport = () => {
    if (exportFormat === "csv") exportCSV();
    else if (exportFormat === "excel") exportExcel();
    else if (exportFormat === "json") exportJSON();
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Company Search Results</CardTitle>
            <CardDescription>{mockResults.length} companies found</CardDescription>
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
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Company</TableHead>
                <TableHead>Industry</TableHead>
                <TableHead>Address</TableHead>
                <TableHead>BBB Rating</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Website</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredResults.length > 0 ? (
                filteredResults.map((result, rowIdx) => (
                  <TableRow key={result.id}>
                    <TableCell>
                      <input
                        className="font-medium border-b w-full bg-transparent"
                        value={result.company}
                        onChange={e =>
                          handleCellChange(rowIdx, "company", e.target.value)
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <input
                        className="border-b w-full bg-transparent"
                        value={result.industry}
                        onChange={e =>
                          handleCellChange(rowIdx, "industry", e.target.value)
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <input
                        className="border-b w-full bg-transparent"
                        value={result.street}
                        onChange={e =>
                          handleCellChange(rowIdx, "street", e.target.value)
                        }
                        placeholder="Street"
                      />
                      <div className="flex gap-1 mt-1">
                        <input
                          className="border-b w-1/2 bg-transparent text-sm text-muted-foreground"
                          value={result.city}
                          onChange={e =>
                            handleCellChange(rowIdx, "city", e.target.value)
                          }
                          placeholder="City"
                        />
                        <input
                          className="border-b w-1/2 bg-transparent text-sm text-muted-foreground"
                          value={result.state}
                          onChange={e =>
                            handleCellChange(rowIdx, "state", e.target.value)
                          }
                          placeholder="State"
                        />
                      </div>
                    </TableCell>
                    <TableCell>
                      <input
                        className="border-b w-full bg-transparent"
                        value={result.bbb_rating}
                        onChange={e =>
                          handleCellChange(rowIdx, "bbb_rating", e.target.value)
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <input
                        className="border-b w-full bg-transparent"
                        value={result.business_phone}
                        onChange={e =>
                          handleCellChange(rowIdx, "business_phone", e.target.value)
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <input
                        className="border-b w-full bg-transparent"
                        value={result.website}
                        onChange={e =>
                          handleCellChange(rowIdx, "website", e.target.value)
                        }
                      />
                    </TableCell>
                  </TableRow>
                ))
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
      </CardContent>
      <CardFooter className="flex justify-between">
        <div className="text-sm text-muted-foreground"></div>
        <div className="flex gap-2">
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
