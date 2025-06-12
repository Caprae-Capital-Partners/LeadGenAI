"use client"

import { useState, useEffect } from "react"
import { Header } from "@/components/header"
import { Sidebar } from "@/components/sidebar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { 
  Search, 
  Download, 
  Edit, 
  Mail, 
  FileText, 
  ExternalLink, 
  Link as LinkIcon, 
  MapPin,
  SortAsc,
  SortDesc,
  Filter,
  X,
  Save
} from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

// Database URLs
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL;
const DATABASE_URL_NOAPI = DATABASE_URL?.replace(/\/api\/?$/, "");

// Person interface - updated to match actual data structure
interface Person {
  id: string;
  name: string;
  title: string;
  website: string;
  email: string;
  location: string;
  company: string;
  phone: string;
  linkedin: string;
  industry: string;
  employees: number;
  revenue: string;
  yearFounded: string;
}

type SortField = 'name' | 'title' | 'location' | 'company' | 'industry'
type SortOrder = 'asc' | 'desc'

export default function PersonsPage() {
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [sortField, setSortField] = useState<SortField>('name')
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)
  const [exportFormat, setExportFormat] = useState("csv")

  // Fetch persons data from API
  useEffect(() => {
    const fetchPersons = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const draftsRes = await fetch(`${DATABASE_URL}/leads/drafts`, {
          method: "GET",
          credentials: "include",
        });

        if (!draftsRes.ok) {
          throw new Error(`HTTP error! status: ${draftsRes.status}`)
        }

        const data = await draftsRes.json()
        
        // Map the API response to Person interface - accessing draft_data
        const mappedPersons: Person[] = data.map((item: any, index: number) => {
          const draftData = item.draft_data || {};
          
          return {
            id: item.id || item.lead_id || index.toString(),
            name: `${draftData.owner_first_name || ''} ${draftData.owner_last_name || ''}`.trim() || 'N/A',
            title: draftData.owner_title || 'N/A',
            website: draftData.website || '',
            email: draftData.owner_email || '',
            location: `${draftData.city || ''}, ${draftData.state || ''}`.replace(', ', '').trim() || 'N/A',
            company: draftData.company || 'N/A',
            phone: draftData.owner_phone_number || draftData.company_phone || '',
            linkedin: draftData.owner_linkedin || draftData.company_linkedin || '',
            industry: draftData.industry || 'N/A',
            employees: draftData.employees || 0,
            revenue: draftData.revenue || 'N/A',
            yearFounded: draftData.year_founded || 'N/A'
          }
        })

        setPersons(mappedPersons)
      } catch (err) {
        console.error('Error fetching persons:', err)
        setError('Failed to fetch persons data')
      } finally {
        setLoading(false)
      }
    }

    fetchPersons()
  }, [])

  // Handle search - updated to include more fields
  const filteredPersons = persons.filter(person =>
    person.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    person.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    person.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
    person.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
    person.industry.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Handle sorting
  const sortedPersons = [...filteredPersons].sort((a, b) => {
    const aValue = a[sortField].toString().toLowerCase()
    const bValue = b[sortField].toString().toLowerCase()
    
    if (sortOrder === 'asc') {
      return aValue.localeCompare(bValue)
    } else {
      return bValue.localeCompare(aValue)
    }
  })

  // Pagination
  const totalPages = Math.ceil(sortedPersons.length / itemsPerPage)
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = sortedPersons.slice(indexOfFirstItem, indexOfLastItem)

  // Reset to first page when search term changes
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('asc')
    }
  }

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null
    return sortOrder === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />
  }

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const pageNumbers = []
    
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) {
        pageNumbers.push(i)
      }
    } else {
      pageNumbers.push(1)
      
      let startPage = Math.max(2, currentPage - 2)
      let endPage = Math.min(totalPages - 1, currentPage + 2)
      
      if (currentPage <= 4) {
        endPage = 5
      } else if (currentPage >= totalPages - 3) {
        startPage = totalPages - 4
      }
      
      if (startPage > 2) {
        pageNumbers.push('ellipsis')
      }
      
      for (let i = startPage; i <= endPage; i++) {
        pageNumbers.push(i)
      }
      
      if (endPage < totalPages - 1) {
        pageNumbers.push('ellipsis')
      }
      
      pageNumbers.push(totalPages)
    }
    
    return pageNumbers
  }

  // Export functions - updated to include more fields
  const exportCSV = () => {
    const csvRows = [
      "Name,Title,Company,Industry,Website,Email,Phone,LinkedIn,Location,Employees,Revenue,Year Founded",
      ...sortedPersons.map(person =>
        `"${person.name}","${person.title}","${person.company}","${person.industry}","${person.website}","${person.email}","${person.phone}","${person.linkedin}","${person.location}","${person.employees}","${person.revenue}","${person.yearFounded}"`
      )
    ]
    const blob = new Blob([csvRows.join("\n")], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "persons.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(sortedPersons, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "persons.json"
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleExport = () => {
    if (exportFormat === "csv") exportCSV()
    else if (exportFormat === "json") exportJSON()
  }

  // Action handlers
  const handleEdit = (person: any) => {
    console.log("Edit person:", person)
    // Implement edit functionality
  }

  const handleNotes = (person: any) => {
    console.log("Open notes for:", person)
    // Implement notes functionality
  }

  const handleEmail = (person: any) => {
    if (person.email) {
      window.open(`mailto:${person.email}`, '_blank')
    }
  }

  const handleWebsite = (person: any) => {
    if (person.website) {
      const url = person.website.startsWith('http') ? person.website : `https://${person.website}`
      window.open(url, '_blank')
    }
  }

  const handleLinkedIn = (person: any) => {
    if (person.linkedin) {
      window.open(person.linkedin, '_blank')
    }
  }

  const handleGoogleMaps = (person: any) => {
    if (person.location && person.location !== 'N/A') {
      const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(person.location)}`
      window.open(mapsUrl, '_blank')
    }
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Top Header */}
      <Header />
      
      {/* Below: Sidebar + Main content */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 p-6 overflow-auto">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Persons</CardTitle>
                <div className="flex items-center gap-4">
                  {/* Search Bar */}
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="search"
                      placeholder="Search persons, companies, industries..."
                      className="w-80 pl-8"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                  
                  {/* Filter Button */}
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    Filter
                  </Button>
                  
                  {/* Sort Dropdown */}
                  <Select value={`${sortField}-${sortOrder}`} onValueChange={(value) => {
                    const [field, order] = value.split('-') as [SortField, SortOrder]
                    setSortField(field)
                    setSortOrder(order)
                  }}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Sort by" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="name-asc">Name A-Z</SelectItem>
                      <SelectItem value="name-desc">Name Z-A</SelectItem>
                      <SelectItem value="title-asc">Title A-Z</SelectItem>
                      <SelectItem value="title-desc">Title Z-A</SelectItem>
                      <SelectItem value="company-asc">Company A-Z</SelectItem>
                      <SelectItem value="company-desc">Company Z-A</SelectItem>
                      <SelectItem value="industry-asc">Industry A-Z</SelectItem>
                      <SelectItem value="industry-desc">Industry Z-A</SelectItem>
                      <SelectItem value="location-asc">Location A-Z</SelectItem>
                      <SelectItem value="location-desc">Location Z-A</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  {/* Export */}
                  <div className="flex items-center gap-2">
                    <Select value={exportFormat} onValueChange={setExportFormat}>
                      <SelectTrigger className="w-20">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="csv">CSV</SelectItem>
                        <SelectItem value="json">JSON</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button variant="outline" onClick={handleExport}>
                      <Download className="mr-2 h-4 w-4" />
                      Export
                    </Button>
                  </div>
                </div>
              </div>
            </CardHeader>
            
            <CardContent>
              {/* Pagination Info and Controls */}
              {sortedPersons.length > 0 && (
                <div className="mb-4 flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, sortedPersons.length)} of {sortedPersons.length} persons
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <Select value={itemsPerPage.toString()} onValueChange={(value) => {
                      setItemsPerPage(Number(value))
                      setCurrentPage(1)
                    }}>
                      <SelectTrigger className="w-[120px]">
                        <SelectValue />
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
              
              {/* Persons Table */}
              <div className="rounded-md border">
                {loading ? (
                  <div className="p-8 text-center">
                    <div className="text-lg">Loading persons data...</div>
                  </div>
                ) : error ? (
                  <div className="p-8 text-center text-red-500">
                    <div className="text-lg">{error}</div>
                    <Button 
                      variant="outline" 
                      className="mt-4"
                      onClick={() => window.location.reload()}
                    >
                      Retry
                    </Button>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead 
                          className="cursor-pointer hover:bg-muted/50 select-none"
                          onClick={() => handleSort('name')}
                        >
                          <div className="flex items-center gap-2">
                            Name
                            {getSortIcon('name')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-muted/50 select-none"
                          onClick={() => handleSort('title')}
                        >
                          <div className="flex items-center gap-2">
                            Title
                            {getSortIcon('title')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-muted/50 select-none"
                          onClick={() => handleSort('company')}
                        >
                          <div className="flex items-center gap-2">
                            Company
                            {getSortIcon('company')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-muted/50 select-none"
                          onClick={() => handleSort('industry')}
                        >
                          <div className="flex items-center gap-2">
                            Industry
                            {getSortIcon('industry')}
                          </div>
                        </TableHead>
                        <TableHead className="w-[200px]">Actions</TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-muted/50 select-none"
                          onClick={() => handleSort('location')}
                        >
                          <div className="flex items-center gap-2">
                            Location
                            {getSortIcon('location')}
                          </div>
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {currentItems.length > 0 ? (
                        currentItems.map((person) => (
                          <TableRow key={person.id}>
                            <TableCell className="font-medium">
                              {person.name}
                            </TableCell>
                            <TableCell>{person.title}</TableCell>
                            <TableCell>{person.company}</TableCell>
                            <TableCell>{person.industry}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleEdit(person)}
                                  title="Edit"
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleNotes(person)}
                                  title="Notes"
                                >
                                  <FileText className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleEmail(person)}
                                  title="Send Email"
                                  disabled={!person.email}
                                >
                                  <Mail className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleWebsite(person)}
                                  title="Visit Website"
                                  disabled={!person.website}
                                >
                                  <ExternalLink className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleLinkedIn(person)}
                                  title="LinkedIn Profile"
                                  disabled={!person.linkedin}
                                >
                                  <LinkIcon className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleGoogleMaps(person)}
                                  title="Google Maps"
                                  disabled={!person.location || person.location === 'N/A'}
                                >
                                  <MapPin className="h-4 w-4" />
                                </Button>
                              </div>
                            </TableCell>
                            <TableCell>{person.location}</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={6} className="h-24 text-center">
                            {searchTerm ? "No persons found matching your search." : "No persons found."}
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                )}
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  )
}