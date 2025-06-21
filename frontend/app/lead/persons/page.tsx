"use client"
import axios from 'axios';
import { useState, useEffect } from "react"
import { Header } from "@/components/header"
import { Sidebar } from "@/components/sidebar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import FeedbackPopup from "@/components/FeedbackPopup";
import { SortDropdown } from "@/app/lead/persons/sort-dropdown"
import { 
  Search, 
  Download, 
  Edit, 
  Mail, 
  FileText, 
  Filter,
  X,
  ExternalLink as LinkIcon,
  Eye,
  Building,
  MapPin,
  Calendar,
  Users,
  Globe,
  Phone,
  Linkedin,
  Pencil,
  StickyNote,
  MessageSquare,
Star,  
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import Notif from "@/components/ui/notif"

// Database URLs
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL;
const DATABASE_URL_NOAPI = DATABASE_URL?.replace(/\/api\/?$/, "");

// Person interface - updated to match actual data structure
interface Person {
  id: string;
  draft_id?: string; // Added optional draft_id
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
  updated?: string; // Added optional updated field
}

type SortOption = "filled" | "company" | "employees" | "owner" | "recent"

// Message settings interface
interface MessageSettings {
  tone: string;
  focus: string;
  additionalcontext: string;
}

// Constants moved to top level
const overviewFields = [
  { key: "name", label: "Name" },
  { key: "title", label: "Title" },
  { key: "company", label: "Company" },
  { key: "industry", label: "Industry" },
  { key: "businessType", label: "Business Type" },
  { key: "website", label: "Website" },
  { key: "employees", label: "Employees Count" },
  { key: "yearFounded", label: "Year Founded" },
  { key: "address", label: "Address" },
  { key: "location", label: "Location" }
];

const contactFields = [
  { key: "email", label: "Email" },
  { key: "phone", label: "Phone Number" },
  { key: "linkedin", label: "LinkedIn Profile" }
];

// EmailMessageGenerator Component
interface EmailMessageGeneratorProps {
  person: Person;
  onClose: () => void;
  onGenerate: () => Promise<void>;
  generatedMessage: string;
  isGenerating: boolean;
  settings: MessageSettings;
  onSettingsChange: (settings: MessageSettings) => void;
}

const EmailMessageGenerator: React.FC<EmailMessageGeneratorProps> = ({ 
  person, 
  onClose,
  onGenerate,
  generatedMessage,
  isGenerating,
  settings,
  onSettingsChange
}) => {
  return (
    <div className="space-y-6 p-6">
      <div className="mb-4">
        {/* Removed duplicate title */}
      </div>

      <div className="space-y-4">
        <div className="p-4 border rounded-lg text-white bg-gray-600">
          <div className="flex items-baseline gap-2">
            <p className="font-medium">Person:</p>
            <p className="text-lg">{person.name}</p>
          </div>
          <p className="text-sm text-white mt-1">Company: {person.company}</p>
          {person.email && (
            <p className="text-sm text-white mt-1">
              Email: <span className="text-blue-200">{person.email}</span>
            </p>
          )}
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tone</label>
            <Select 
              value={settings.tone}
              onValueChange={(value) => onSettingsChange({...settings, tone: value})}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select tone" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="professional">Professional</SelectItem>
                <SelectItem value="friendly">Friendly</SelectItem>
                <SelectItem value="direct">Direct</SelectItem>
                <SelectItem value="casual">Casual</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Focus</label>
            <Select 
              value={settings.focus}
              onValueChange={(value) => onSettingsChange({...settings, focus: value})}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select focus" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="partnership">Partnership</SelectItem>
                <SelectItem value="collaboration">Collaboration</SelectItem>
                <SelectItem value="networking">Networking</SelectItem>
                <SelectItem value="sales">Sales</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Additional Context</label>
            <Input 
              value={settings.additionalcontext}
              onChange={(e) => onSettingsChange({...settings,additionalcontext: e.target.value})}
              placeholder="Any special notes or context"
            />
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <Button 
            onClick={onGenerate}
            disabled={isGenerating}
            className="flex-1"
          >
            {isGenerating ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Generating...
              </div>
            ) : "Generate Message"}
          </Button>
        </div>

        {generatedMessage && (
  <div className="mt-4 space-y-2">
    <label className="block text-sm font-medium text-gray-700">Generated Message</label>
    <div className="p-4 border rounded-lg text-white bg-gray-600 whitespace-pre-wrap max-h-60 overflow-y-auto">
      {generatedMessage}
    </div>
    <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => {
                navigator.clipboard.writeText(generatedMessage);
                // You might want to show a notification here
              }}>
                Copy to Clipboard
              </Button>
              <Button onClick={() => {
                if (person.email) {
                  window.open(`https://mail.google.com/mail/?view=cm&fs=1&to=${person.email}`, '_blank');
                }
              }}>
                Open in Email
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
// LinkedIn Message Generator Component
interface LinkedInMessageGeneratorProps {
    person: Person;
    onClose: () => void;
    onGenerate: () => Promise<void>;
    generatedMessage: string;
    isGenerating: boolean;
    settings: MessageSettings;
    onSettingsChange: (settings: MessageSettings) => void;
  }
  
  const LinkedInMessageGenerator: React.FC<LinkedInMessageGeneratorProps> = ({ 
    person, 
    onClose,
    onGenerate,
    generatedMessage,
    isGenerating,
    settings,
    onSettingsChange
  }) => {
    return (
      <div className="space-y-6 p-6">
        {/* Removed duplicate title */}
        <div className="space-y-4">
          <div className="p-4 border rounded-lg text-white bg-blue-600">
            <div className="flex items-baseline gap-2">
              <p className="font-medium">Person:</p>
              <p className="text-lg">{person.name}</p>
            </div>
            <p className="text-sm text-white mt-1">Company: {person.company}</p>
            {person.linkedin && (
              <p className="text-sm text-white mt-1">
                LinkedIn: <span className="text-blue-200">{person.linkedin}</span>
              </p>
            )}
          </div>
  
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tone</label>
              <Select 
                value={settings.tone}
                onValueChange={(value) => onSettingsChange({...settings, tone: value})}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select tone" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="professional">Professional</SelectItem>
                  <SelectItem value="friendly">Friendly</SelectItem>
                  <SelectItem value="direct">Direct</SelectItem>
                  <SelectItem value="casual">Casual</SelectItem>
                </SelectContent>
              </Select>
            </div>
  
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Focus</label>
              <Select 
                value={settings.focus}
                onValueChange={(value) => onSettingsChange({...settings, focus: value})}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select focus" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="partnership">Partnership</SelectItem>
                  <SelectItem value="collaboration">Collaboration</SelectItem>
                  <SelectItem value="networking">Networking</SelectItem>
                  <SelectItem value="sales">Sales</SelectItem>
                </SelectContent>
              </Select>
            </div>
  
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Additional Context</label>
              <Input 
                value={settings.additionalcontext}
                onChange={(e) => onSettingsChange({...settings,additionalcontext: e.target.value})}
                placeholder="Any special notes or context"
              />
            </div>
          </div>
  
          <div className="flex gap-3 pt-2">
            <Button 
              onClick={onGenerate}
              disabled={isGenerating}
              className="flex-1"
            >
              {isGenerating ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Generating...
                </div>
              ) : "Generate Message"}
            </Button>
          </div>
  
          {generatedMessage && (
            <div className="mt-4 space-y-2">
              <label className="block text-sm font-medium text-gray-700">Generated Message</label>
              <div className="p-4 border rounded-lg text-white bg-blue-600 whitespace-pre-wrap max-h-60 overflow-y-auto">
                {generatedMessage}
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => {
                  navigator.clipboard.writeText(generatedMessage);
                  // You might want to show a notification here
                }}>
                  Copy to Clipboard
                </Button>
                <Button onClick={() => {
                  if (person.linkedin) {
                    window.open(person.linkedin, '_blank');
                  }
                }}>
                  Open LinkedIn Profile
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

// PopupBig Component
interface PopupBigProps {
  show: boolean;
  onClose: () => void;
  person: Person | null;
  isEditing: boolean;
  popupTab: string;
  setPopupTab: (tab: string) => void;
  setPopupData: (person: Person) => void;
  onSave: () => void;
}

const PopupBig: React.FC<PopupBigProps> = ({ 
  show, 
  onClose, 
  person, 
  isEditing, 
  popupTab, 
  setPopupTab, 
  setPopupData, 
  onSave 
}) => {
  if (!person) return null;

  const handleClose = () => {
    onClose();
    setPopupTab('overview');
  };

  return (
    <Dialog open={show} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">{person.name}</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-8">
          {/* Tab Navigation */}
          <div className="border-b pb-4">
            <div className="flex space-x-4">
              <button
                onClick={() => setPopupTab('overview')}
                className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                  popupTab === 'overview'
                    ? 'border-teal-500 text-teal-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setPopupTab('contact')}
                className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                  popupTab === 'contact'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Contact Info
              </button>
            </div>
          </div>

          {/* Overview Tab Content */}
          {popupTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {overviewFields.map(({ key, label }) => {
                let value = person[key as keyof Person] || "";
                const isLink = key === "website" || key === "linkedin";
                
                // Special handling for website field
                if (key === "website" && value && !value.toString().startsWith('http')) {
                  value = `https://${value}`;
                }

                return (
                  <div key={key} className="space-y-1">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      {label}
                    </label>
                    {isEditing ? (
                      <Input
                        value={value.toString()}
                        onChange={(e) =>
                          setPopupData({ ...person, [key]: e.target.value })
                        }
                        className="text-sm"
                        placeholder={isLink ? "https://..." : ""}
                      />
                    ) : (
                      <div className="px-3 py-2 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-zinc-800 text-sm text-gray-900 dark:text-white">
                        {isLink && value ? (
                          <a 
                            href={value.toString()} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {value.toString()}
                          </a>
                        ) : value || <span className="italic text-gray-400">N/A</span>}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Contact Tab Content */}
          {popupTab === 'contact' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {contactFields.map(({ key, label }) => {
                const value = person[key as keyof Person] || "";
                const isLink = key === "linkedin";
                
                return (
                  <div key={key} className="space-y-1">
                    <label className="block text-sm font-medium text-gray-700">
                      {label}
                    </label>
                    {isEditing ? (
                      <Input
                        value={value.toString()}
                        onChange={(e) =>
                          setPopupData({ ...person, [key]: e.target.value })
                        }
                        className="text-sm"
                        placeholder={isLink ? "https://..." : ""}
                      />
                    ) : (
                      <div className="px-3 py-2 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-zinc-800 text-sm text-gray-900 dark:text-white">
                        {isLink && value ? (
                          <a 
                            href={value.toString()} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {value.toString()}
                          </a>
                        ) : value || <span className="italic text-gray-400">N/A</span>}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-4 pt-4 border-t">
            {isEditing ? (
              <Button size="sm" onClick={onSave}>
                Save Changes
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => person.email && window.open(`mailto:${person.email}`, '_blank')}
                  disabled={!person.email || person.email === 'N/A'}
                >
                  <Mail className="h-4 w-4 mr-2" />
                  Send Email
                </Button>
                
                <Button
                  variant="outline"
                  onClick={() => person.linkedin && window.open(person.linkedin, '_blank')}
                  disabled={!person.linkedin || person.linkedin === 'N/A'}
                >
                  <Linkedin className="h-4 w-4 mr-2" />
                  LinkedIn
                </Button>
                
                {person.website && person.website !== 'N/A' && (
                  <Button
                    variant="outline"
                    onClick={() => window.open(person.website.startsWith('http') ? person.website : `https://${person.website}`, '_blank')}
                  >
                    <Globe className="h-4 w-4 mr-2" />
                    Website
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const ExpandableCell: React.FC<{ text: string }> = ({ text }) => {
    const [expanded, setExpanded] = useState(false);
    const isLong = text && text.length > 30;
    if (!isLong) return <span>{text}</span>;

    return (
        <div className="whitespace-pre-wrap">
            <span>
                {expanded ? text : `${text.slice(0, 30)}...`}
            </span>
            <button
                className="text-blue-500 hover:underline text-xs ml-1"
                onClick={() => setExpanded(!expanded)}
            >
                {expanded ? "Show less" : "Show more"}
            </button>
        </div>
    );
};

// Main PersonsPage Component
export default function PersonsPage() {
  // State declarations
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)
  const [selectedPersons, setSelectedPersons] = useState<string[]>([])
  const [showFilters, setShowFilters] = useState(false)
  const [popupData, setPopupData] = useState<Person | null>(null)
  const [popupTab, setPopupTab] = useState('overview')
  const [isEditing, setIsEditing] = useState(false)

  // Email popup states
  const [emailPopupData, setEmailPopupData] = useState<Person | null>(null)
  const [generatedMessage, setGeneratedMessage] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [messageSettings, setMessageSettings] = useState<MessageSettings>({
    tone: "professional",
    focus: "partnership",
    additionalcontext: ""
  })
  const [linkedinPopupData, setLinkedinPopupData] = useState<Person | null>(null)
  const [linkedinGeneratedMessage, setLinkedinGeneratedMessage] = useState("")
  const [linkedinIsGenerating, setLinkedinIsGenerating] = useState(false)
  const [linkedinMessageSettings, setLinkedinMessageSettings] = useState<MessageSettings>({
    tone: "professional",
    focus: "partnership",
    additionalcontext: ""
  })

  // Notification state
  const [notif, setNotif] = useState<{
    show: boolean;
    message: string;
    type: "success" | "error" | "info";
  }>({
    show: false,
    message: "",
    type: "success",
  })

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
            draft_id: item.draft_id,
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

  // Handle search and filters
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

  // Handle sort functionality
  const handleSortBy = (sortBy: SortOption, direction: "most" | "least") => {
    // Count how many non-empty fields each row has
    const getFilledCount = (person: Person) =>
      Object.entries(person).filter(([key, value]) => {
        if (
          ["id", "draft_id", "updated"].includes(key) ||
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

  // Handle email message click
  const handleEmailMessageClick = (person: Person) => {
    setEmailPopupData(person);
    setGeneratedMessage(""); // Clear any previous message
  };
  const handleLinkedInMessageClick = (person: Person) => {
    setLinkedinPopupData(person);
    setLinkedinGeneratedMessage(""); // Clear any previous message
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

  // Handle popup save
  const handlePopupSave = async () => {
    if (!popupData) return;

    // Helper to convert camelCase keys into snake_case
    const toSnake = (str: string) => str.replace(/([A-Z])/g, "_$1").toLowerCase();
    const normalizeKeys = (obj: any) => {
      const result: any = {};
      for (const [k, v] of Object.entries(obj)) {
        result[toSnake(k)] = v;
      }
      return result;
    };

    try {
      const person = popupData;
      const leadId = person.id;
      const actualDraftId = person.draft_id;

      if (!actualDraftId) {
        throw new Error("Draft ID not found for this person");
      }

      // Normalize the edited fields so that every key is snake_case
      const normalizedPerson = normalizeKeys(person);

      // Create payload for the draft update
      const payload = {
        draft_data: normalizedPerson,
        change_summary: "Updated from persons page",
        phase: "draft",
        status: "pending",
      };

      const putUrl = `${process.env.NEXT_PUBLIC_DATABASE_URL}/leads/drafts/${actualDraftId}`;

      try {
        const putResponse = await axios.put(putUrl, payload, { withCredentials: true });
        // Update local state with the saved changes
        setPersons((prev) => prev.map((p) => p.id === person.id ? { ...person, draft_id: actualDraftId, updated: new Date().toLocaleString() } : p));
        setIsEditing(false);
        setPopupData(null);
        showNotification("Changes saved successfully.", "success");
      } catch (putError) {
        console.error("❌ PUT Request failed:", putError);
        if (axios.isAxiosError(putError)) {
          console.error("❌ PUT Error status:", putError.response?.status);
          console.error("❌ PUT Error data:", putError.response?.data);
        }
        throw putError;
      }
    } catch (err) {
      console.error("❌ Error saving person:", err);
      let errorMessage = "Failed to save person.";
      if (axios.isAxiosError(err)) {
        if (err.response) {
          errorMessage = `Save failed: ${err.response.data?.message || err.message}`;
        } else {
          errorMessage = "Network error: Unable to connect to server.";
        }
      } else if (err instanceof Error) {
        errorMessage = `Save failed: ${err.message}`;
      }
      showNotification(errorMessage, "error");
    }
  };

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const pageNumbers: (number | string)[] = []
    
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

  // Export functions
  const exportCSV = () => {
    const personsToExport = filteredPersons.filter(p => selectedPersons.includes(p.id));
    const csvRows = [
      "Name,Title,Company,Industry,Business Type,Website,Email,Phone,LinkedIn,Address,Employees,Year Founded",
      ...personsToExport.map(person =>
        `"${person.name}","${person.title}","${person.company}","${person.industry}","${person.businessType}","${person.website}","${person.email}","${person.phone}","${person.linkedin}","${person.address}","${person.employees}","${person.yearFounded}"`
      )
    ]
    const blob = new Blob([csvRows.join("\n")], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `persons-selected.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleExport = () => {
    if (selectedPersons.length === 0) {
      showNotification("Please select at least one row to export.", "info");
      return;
    }
    exportCSV();
  }

  // Action handlers
  const handleEdit = (person: Person) => {
    setPopupData(person);
    setIsEditing(true);
    setPopupTab('overview');
  };

  const handleNotes = (person: Person) => {
    console.log("Open notes for:", person)
    // Implement notes functionality
  }

  const handleEmail = (person: Person) => {
    if (person.email) {
      window.open(`mailto:${person.email}`, '_blank')
    }
  }

  const handleLinkedIn = (person: Person) => {
    if (person.linkedin) {
      window.open(person.linkedin, '_blank')
    }
  }

  const handleViewPerson = (person: Person) => {
    setPopupData(person);
  }

  // Function to show notifications
  const showNotification = (message: string, type: "success" | "error" | "info" = "success") => {
    setNotif({ show: true, message, type });
    setTimeout(() => {
      setNotif(prev => ({ ...prev, show: false }));
    }, 3500);
  };

  // Generate AI email message
  const generateEmailMessage = async (person: Person, settings: MessageSettings) => {
    setIsGenerating(true);
    try {
      const response = await axios.post(
        `${DATABASE_URL_NOAPI}/emailgen/scrape`,
        {
          company_name: person.company,
          homepage_url: person.website,
          // Optionally, you can send more context if your backend supports it
          tone: settings.tone,
          focus: settings.focus,
          additional_context: settings.additionalcontext,
        },
        { withCredentials: true }
      );
      setGeneratedMessage(response.data.email || "No email message returned.");
    } catch (error) {
      console.error("Error generating message:", error);
      showNotification("Error generating message", "error");
    } finally {
      setIsGenerating(false);
    }
  };

  const generateLinkedInMessage = async (person: Person, settings: MessageSettings) => {
    setLinkedinIsGenerating(true);
    try {
      const response = await axios.post(
        `${DATABASE_URL_NOAPI}/emailgen/scrape`,
        {
          company_name: person.company,
          homepage_url: person.website,
          // Optionally, you can send more context if your backend supports it
          tone: settings.tone,
          ocus: settings.focus,
          additional_context: settings.additionalcontext,
        },
        { withCredentials: true }
      );
      setLinkedinGeneratedMessage(response.data.linkedin_message || "No LinkedIn message returned.");
    } catch (error) {
      console.error("Error generating LinkedIn message:", error);
      showNotification("Error generating LinkedIn message", "error");
    } finally {
      setLinkedinIsGenerating(false);
    }
  };

return (
  <div className="flex flex-col h-screen">
    <FeedbackPopup />
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
                    onClick={() => setShowFilters(f => !f)}
                    title={showFilters ? "Hide Filters" : "Show Filters"}
                  >
                    <Filter className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" onClick={handleExport} title="Export Selected to CSV">
                    <Download className="h-4 w-4" />
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
            {/* Persons Table */}
            <div className="w-full overflow-x-auto relative border rounded-md">
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
                      <TableHead className="w-[50px] sticky top-0 left-0 z-40 bg-background border-r">
                        <Checkbox
                          checked={selectedPersons.length === currentItems.length && currentItems.length > 0}
                          onCheckedChange={handleSelectAll}
                          aria-label="Select all"
                        />
                      </TableHead>
                      <TableHead className="sticky top-0 left-[50px] z-30 bg-background border-r text-base font-bold text-white px-6 py-3 whitespace-nowrap min-w-[200px]">
                        Name
                      </TableHead>
                      <TableHead className="w-[140px] sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Actions</TableHead>
                      <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Title</TableHead>
                      <TableHead className="w-[120px] sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Links</TableHead>
                      <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Phone Number</TableHead>
                      <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Company</TableHead>
                      <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Industry</TableHead>
                      <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Business Type</TableHead>
                      <TableHead className="sticky top-0 z-20 bg-background text-base font-bold text-white px-6 py-3 whitespace-nowrap">Address</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {currentItems.length > 0 ? (
                      currentItems.map((person) => {
                        return (
                          <TableRow key={person.id}>
                            <TableCell className="w-[50px] sticky left-0 z-20 bg-inherit border-r">
                              <Checkbox
                                checked={selectedPersons.includes(person.id)}
                                onCheckedChange={() => handleSelectPerson(person.id)}
                                aria-label={`Select ${person.name}`}
                              />
                            </TableCell>
                            <TableCell className="sticky left-[50px] z-10 bg-inherit border-r px-6 py-2 max-w-[240px] align-top">
                              <ExpandableCell text={person.name} />
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                {person.email && person.email !== 'N/A' && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleEmailMessageClick(person)}
                                    title="Generate Email Message"
                                  >
                                    <Mail className="w-4 h-4 text-green-600" />
                                  </Button>
                                )}
                                {person.linkedin && person.linkedin !== 'N/A' && (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleLinkedInMessageClick(person)}
                                        title="Generate LinkedIn Message"
                                    >
                                        <Linkedin className="w-4 h-4 text-blue-700" />
                                    </Button>
                                )}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleEdit(person)}
                                  title="Edit"
                                  className="p-1 h-8 w-8"
                                >
                                  <div className="w-6 h-6 text-blue-500 flex items-center justify-center">
                                    <Pencil className="h-3 w-3 text-blue-500" />
                                  </div>
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleNotes(person)}
                                  title="Notes - Coming soon!"
                                >
                                  <StickyNote className="h-4 w-4 text-yellow-500" />
                                </Button>
                                <button
          title="Favorite - Coming soon!"
          className="hover:bg-gray-100 rounded p-1 group relative"
          onClick={(e) => {
            e.preventDefault();
            showNotification("Favorite feature coming soon!", "info");
          }}
        >
          <Star className="w-4 h-4 text-yellow-500" />
          <span className="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-300 absolute z-10 w-32 p-2 text-xs text-white bg-gray-800 rounded shadow-lg -top-8 -left-1/2">
            Favorite feature coming soon!
          </span>
        </button>
                              </div>
                            </TableCell>
                            <TableCell>
                              {person.title}
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleEmail(person)}
                                  title="Send Email"
                                  disabled={!person.email}
                                >
                                  <Mail className="h-4 w-4 text-green-600" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleLinkedIn(person)}
                                  title="LinkedIn Profile"
                                  disabled={!person.linkedin}
                                >
                                  <Linkedin className="h-4 w-4 text-blue-700" />
                                </Button>
                              </div>
                            </TableCell>
                            <TableCell>
                              {person.phone || 'N/A'}
                            </TableCell>
                            <TableCell>
                              {person.company}
                            </TableCell>
                            <TableCell>
                              {person.industry}
                            </TableCell>
                            <TableCell>
                              {person.businessType}
                            </TableCell>
                            <TableCell>
                              {person.address}
                            </TableCell>
                          </TableRow>
                        );
                      })
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
              <div className="flex flex-col md:flex-row justify-between items-center mt-4 gap-4 px-4 py-2">
                <div className="text-sm text-muted-foreground">
                    Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filteredPersons.length)} of {filteredPersons.length} persons
                    {selectedPersons.length > 0 && (
                        <span className="ml-2 text-blue-600">
                        ({selectedPersons.length} selected)
                        </span>
                    )}
                </div>
    
                <div className="flex items-center gap-3 px-3 py-2">
                    <Select
                        value={itemsPerPage.toString()}
                        onValueChange={(value) => {
                            setItemsPerPage(Number(value));
                            setCurrentPage(1);
                        }}
                    >
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
      </main>
    </div>

    {/* PopupBig Component */}
    <PopupBig 
      show={!!popupData}
      onClose={() => {
        setPopupData(null);
        setIsEditing(false);
        setPopupTab('overview');
      }}
      person={popupData}
      isEditing={isEditing}
      popupTab={popupTab}
      setPopupTab={setPopupTab}
      setPopupData={setPopupData}
      onSave={handlePopupSave}
    />

   {/* Email Popup Dialog */}
{emailPopupData && (
  <Dialog open={!!emailPopupData} onOpenChange={() => setEmailPopupData(null)}>
    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle className="text-2xl text-center">Email Message Generator</DialogTitle>
      </DialogHeader>
      <EmailMessageGenerator
        person={emailPopupData}
        onClose={() => setEmailPopupData(null)}
        onGenerate={() => generateEmailMessage(emailPopupData, messageSettings)}
        generatedMessage={generatedMessage}
        isGenerating={isGenerating}
        settings={messageSettings}
        onSettingsChange={setMessageSettings}
      />
    </DialogContent>
  </Dialog>
)}
{/* LinkedIn Popup Dialog */}
{linkedinPopupData && (
  <Dialog open={!!linkedinPopupData} onOpenChange={() => setLinkedinPopupData(null)}>
    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle className="text-2xl text-center">LinkedIn Message Generator</DialogTitle>
      </DialogHeader>
      <LinkedInMessageGenerator
        person={linkedinPopupData}
        onClose={() => setLinkedinPopupData(null)}
        onGenerate={() => generateLinkedInMessage(linkedinPopupData, linkedinMessageSettings)}
        generatedMessage={linkedinGeneratedMessage}
        isGenerating={linkedinIsGenerating}
        settings={linkedinMessageSettings}
        onSettingsChange={setLinkedinMessageSettings}
      />
    </DialogContent>
  </Dialog>
)}

    {/* Notification */}
    <Notif
      show={notif.show}
      message={notif.message}
      type={notif.type}
      onClose={() => setNotif((prev) => ({ ...prev, show: false }))}
    />
  </div>
);
}