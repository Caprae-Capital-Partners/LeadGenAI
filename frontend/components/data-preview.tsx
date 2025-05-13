"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Search, Filter } from "lucide-react"
import { useLeads } from "./LeadsProvider"

// Mock data for demonstration - this would come from the scraper results in a real app
const mockData = [
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

export function DataPreview() {
  const { leads } = useLeads()
  const [selectedRows, setSelectedRows] = useState<number[]>(leads.map((row) => row.id))
  const [searchTerm, setSearchTerm] = useState("")

  const toggleSelectAll = () => {
    if (selectedRows.length === leads.length) {
      setSelectedRows([])
    } else {
      setSelectedRows(leads.map((row) => row.id))
    }
  }

  const toggleSelectRow = (id: number) => {
    if (selectedRows.includes(id)) {
      setSelectedRows(selectedRows.filter((rowId) => rowId !== id))
    } else {
      setSelectedRows([...selectedRows, id])
    }
  }

  const filteredData = leads.filter(
    (row) =>
      row.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.state.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Preview and Select Companies</h3>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search companies..."
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

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">
                <Checkbox
                  checked={selectedRows.length === leads.length && leads.length > 0}
                  onCheckedChange={toggleSelectAll}
                />
              </TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Industry</TableHead>
              <TableHead>Address</TableHead>
              <TableHead>BBB Rating</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Website</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.map((row) => (
              <TableRow key={row.id}>
                <TableCell>
                  <Checkbox checked={selectedRows.includes(row.id)} onCheckedChange={() => toggleSelectRow(row.id)} />
                </TableCell>
                <TableCell>
                  <div className="font-medium">{row.company}</div>
                </TableCell>
                <TableCell>{row.industry}</TableCell>
                <TableCell>
                  <div>{row.street}</div>
                  <div className="text-sm text-muted-foreground">
                    {row.city}, {row.state}
                  </div>
                </TableCell>
                <TableCell>{row.bbb_rating}</TableCell>
                <TableCell>{row.business_phone}</TableCell>
                <TableCell>{row.website}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {selectedRows.length} of {leads.length} companies selected for enrichment
        </div>
        <Button
          variant="outline"
          onClick={() => setSelectedRows(leads.map((row) => row.id))}
          disabled={selectedRows.length === leads.length}
        >
          Select All
        </Button>
      </div>
    </div>
  )
}
