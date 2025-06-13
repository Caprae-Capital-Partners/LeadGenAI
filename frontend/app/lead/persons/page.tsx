"use client"

import { useState, useEffect } from "react"
import { Header } from "@/components/header"
import { Sidebar } from "@/components/sidebar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { SortDropdown } from "@/app/lead/persons/sort-dropdown"
import { 
  Search, 
  Download, 
  Edit, 
  Mail, 
  FileText, 
  Filter,
  X,
  ExternalLink as LinkIcon
} from "lucide-react"
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
  yearFounded: string;
  businessType: string;
  address: string;
}

type SortOption = "filled" | "company" | "employees" | "owner" | "recent"

export default function PersonsPage() {
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)
  const [exportFormat, setExportFormat] = useState("csv")
  const [selectedPersons, setSelectedPersons] = useState<string[]>([])
  const [showFilters, setShowFilters] = useState(false)

  // Filter states
  const [titleFilter, setTitleFilter] = useState("")
  const [companyFilter, setCompanyFilter] = useState("")
  const [industryFilter, setIndustryFilter] = useState("")
  const [businessTypeFilter, setBusinessTypeFilter] = useState("")
  const [addressFilter, setAddressFilter] = useState("")

  // Clear all filters function
  const clearAllFilters = () => {
    setTitleFilter("")
    setCompanyFilter("")
    setIndustryFilter("")
    setBusinessTypeFilter("")
    setAddressFilter("")
  }

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
            yearFounded: draftData.year_founded || 'N/A',
            businessType: draftData.business_type || 'N/A',
            address: `${draftData.street || ''} ${draftData.city || ''} ${draftData.state || ''}`.trim() || 'N/A'
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

  // Handle search and filters - updated to include filter logic
  const filteredPersons = persons.filter(person => {
    // Search term filter
    const matchesSearch = person.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      person.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      person.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
      person.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      person.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      person.businessType.toLowerCase().includes(searchTerm.toLowerCase())

    // Individual filters
    const matchTitle = person.title?.toLowerCase().includes(titleFilter.toLowerCase())
    const matchCompany = person.company?.toLowerCase().includes(companyFilter.toLowerCase())
    const matchIndustry = person.industry?.toLowerCase().includes(industryFilter.toLowerCase())
    const matchBusinessType = person.businessType?.toLowerCase().includes(businessTypeFilter.toLowerCase())
    const matchAddress = person.address?.toLowerCase().includes(addressFilter.toLowerCase())

    return matchesSearch && matchTitle && matchCompany && matchIndustry && matchBusinessType && matchAddress
  })

  // Pagination
  const totalPages = Math.ceil(filteredPersons.length / itemsPerPage)
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredPersons.slice(indexOfFirstItem, indexOfLastItem)

  // Reset to first page when search term or filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, titleFilter, companyFilter, industryFilter, businessTypeFilter, addressFilter])

  // Handle sort functionality (removed revenue)
  const handleSortBy = (sortBy: SortOption, direction: "most" | "least") => {
    // Count how many non-empty fields each row has
    const getFilledCount = (person: Person) =>
      Object.entries(person).filter(([key, value]) => {
        if (
          ["id"].includes(key) ||
          value === null ||
          value === undefined ||
          value === "" ||
          value === "N/A"
        ) {
          return false;
        }
        return true;
      }).length;

    // Determine the base array to sort
    const base = [...persons];

    // Sort based on the selected criteria
    const sorted = base.sort((a, b) => {
      if (sortBy === "filled") {
        const aCount = getFilledCount(a);
        const bCount = getFilledCount(b);
        return direction === "most" ? bCount - aCount : aCount - bCount;
      }
      
      if (sortBy === "company") {
        return direction === "most"
          ? a.company.localeCompare(b.company)
          : b.company.localeCompare(a.company);
      }
      
      if (sortBy === "employees") {
        return direction === "most" ? b.employees - a.employees : a.employees - b.employees;
      }
      
      if (sortBy === "owner") {
        // Sort by whether they have contact info (email or phone)
        const aHasContact = (a.email && a.email !== 'N/A') || (a.phone && a.phone !== 'N/A') ? 1 : 0;
        const bHasContact = (b.email && b.email !== 'N/A') || (b.phone && b.phone !== 'N/A') ? 1 : 0;
        return direction === "most" ? bHasContact - aHasContact : aHasContact - bHasContact;
      }
      
      if (sortBy === "recent") {
        // Sort by name as a fallback for "recent" since we don't have date info
        return direction === "most"
          ? a.name.localeCompare(b.name)
          : b.name.localeCompare(a.name);
      }
      
      return 0;
    });

    // Update the persons state with sorted data
    setPersons(sorted);
    setCurrentPage(1); // reset pagination to page 1
  };

  // Handle checkbox selection
  const handleSelectPerson = (personId: string) => {
    setSelectedPersons(prev => 
      prev.includes(personId) 
        ? prev.filter(id => id !== personId)
        : [...prev, personId]
    )
  }

  const handleSelectAll = () => {
    if (selectedPersons.length === currentItems.length) {
      setSelectedPersons([])
    } else {
      setSelectedPersons(currentItems.map(person => person.id))
    }
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
      "Name,Title,Company,Industry,Business Type,Website,Email,Phone,LinkedIn,Address,Employees,Year Founded",
      ...filteredPersons.map(person =>
        `"${person.name}","${person.title}","${person.company}","${person.industry}","${person.businessType}","${person.website}","${person.email}","${person.phone}","${person.linkedin}","${person.address}","${person.employees}","${person.yearFounded}"`
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
    const blob = new Blob([JSON.stringify(filteredPersons, null, 2)], { type: "application/json" })
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

  const handleLinkedIn = (person: any) => {
    if (person.linkedin) {
      window.open(person.linkedin, '_blank')
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
                  
                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <SortDropdown onApply={handleSortBy} />
                    
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setShowFilters((f) => !f)}
                      title={showFilters ? "Hide Filters" : "Show Filters"}
                    >
                      <Filter className="h-4 w-4" />
                    </Button>
                  </div>
                  
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

              {/* Filter Section */}
              {showFilters && (
                <div className="flex flex-wrap gap-4 my-4">
                  <Input
                    placeholder="Title"
                    value={titleFilter}
                    onChange={(e) => setTitleFilter(e.target.value)}
                    className="w-[240px]"
                  />
                  <Input
                    placeholder="Company"
                    value={companyFilter}
                    onChange={(e) => setCompanyFilter(e.target.value)}
                    className="w-[240px]"
                  />
                  <Input
                    placeholder="Industry"
                    value={industryFilter}
                    onChange={(e) => setIndustryFilter(e.target.value)}
                    className="w-[240px]"
                  />
                  <Input
                    placeholder="Business Type"
                    value={businessTypeFilter}
                    onChange={(e) => setBusinessTypeFilter(e.target.value)}
                    className="w-[240px]"
                  />
                  <Input
                    placeholder="Address"
                    value={addressFilter}
                    onChange={(e) => setAddressFilter(e.target.value)}
                    className="w-[240px]"
                  />
                  <Button variant="ghost" size="sm" onClick={clearAllFilters}>
                    <X className="h-4 w-4 mr-1" />
                    Clear All
                  </Button>
                </div>
              )}
            </CardHeader>
            
            <CardContent>
              {/* Pagination Info and Controls */}
              {filteredPersons.length > 0 && (
                <div className="mb-4 flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filteredPersons.length)} of {filteredPersons.length} persons
                    {selectedPersons.length > 0 && (
                      <span className="ml-2 text-blue-600">
                        ({selectedPersons.length} selected)
                      </span>
                    )}
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
                    <TableHeader className="sticky top-0 bg-background z-10">
                      <TableRow>
                        <TableHead className="w-[50px] bg-background">
                          <Checkbox
                            checked={selectedPersons.length === currentItems.length && currentItems.length > 0}
                            onCheckedChange={handleSelectAll}
                            aria-label="Select all"
                          />
                        </TableHead>
                        <TableHead className="bg-background">
                          Name
                        </TableHead>
                        <TableHead className="w-[120px] bg-background">Actions</TableHead>
                        <TableHead className="bg-background">
                          Title
                        </TableHead>
                        <TableHead className="w-[120px] bg-background">Links</TableHead>
                        <TableHead className="bg-background">Phone Number</TableHead>
                        <TableHead className="bg-background">
                          Company
                        </TableHead>
                        <TableHead className="bg-background">
                          Industry
                        </TableHead>
                        <TableHead className="bg-background">
                          Business Type
                        </TableHead>
                        <TableHead className="bg-background">Address</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {currentItems.length > 0 ? (
                        currentItems.map((person) => (
                          <TableRow key={person.id}>
                            <TableCell>
                              <Checkbox
                                checked={selectedPersons.includes(person.id)}
                                onCheckedChange={() => handleSelectPerson(person.id)}
                                aria-label={`Select ${person.name}`}
                              />
                            </TableCell>
                            <TableCell className="font-medium">
                              {person.name}
                            </TableCell>
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
                              </div>
                            </TableCell>
                            <TableCell>{person.title}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
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
                                  onClick={() => handleLinkedIn(person)}
                                  title="LinkedIn Profile"
                                  disabled={!person.linkedin}
                                >
                                  <LinkIcon className="h-4 w-4" />
                                </Button>
                              </div>
                            </TableCell>
                            <TableCell>{person.phone || 'N/A'}</TableCell>
                            <TableCell>{person.company}</TableCell>
                            <TableCell>{person.industry}</TableCell>
                            <TableCell>{person.businessType}</TableCell>
                            <TableCell>{person.address}</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={10} className="h-24 text-center">
                            {searchTerm || titleFilter || companyFilter || industryFilter || businessTypeFilter || addressFilter ? "No persons found matching your search and filters." : "No persons found."}
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                )}
              </div>

              {/* Pagination at the bottom */}
              {filteredPersons.length > 0 && (
                <div className="mt-4 flex items-center justify-center">
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
              )}
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  )
}