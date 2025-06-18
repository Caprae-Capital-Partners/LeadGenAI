"use client"

import { Header } from "@/components/header"
import { Sidebar } from "@/components/sidebar"
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Download, Filter, X, ExternalLink } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import PopupBig from "@/components/ui/popup-big";
import FeedbackPopup from "@/components/FeedbackPopup";
import axios from "axios";
import { SortDropdown } from "@/components/ui/sort-dropdown";
import Notif from "@/components/ui/notif";
import { Eye, Globe, Linkedin, MapPin, Edit, Pencil, Mail, StickyNote, MessageSquare, Star } from "lucide-react";
import React from "react";

const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL;
const DATABASE_URL_NOAPI = DATABASE_URL?.replace(/\/api\/?$/, "");

const dummyData = [
{
    id: "1",
    lead_id: "1",
    draft_id: "draft_1",
    company: "Acme Corporation",
    website: "https://acme.com",
    industry: "Manufacturing",
    productCategory: "Industrial Supplies",
    businessType: "B2B",
    employees: "250",
    revenue: "$50M",
    yearFounded: "1985",
    bbbRating: "A+",
    street: "123 Industrial Way",
    city: "Springfield",
    state: "IL",
    companyPhone: "(555) 123-4567",
    companyLinkedin: "https://linkedin.com/company/acme-corp",
    ownerFirstName: "John",
    ownerLastName: "Doe",
    ownerTitle: "CEO",
    ownerLinkedin: "https://linkedin.com/in/johndoe",
    ownerPhoneNumber: "(555) 987-6543",
    ownerEmail: "john.doe@acme.com",
    source: "Manual Entry",
    created: "2023-05-15T10:30:00Z",
    updated: "2023-06-20T14:45:00Z",
    sourceType: "database"
},
{
    id: "2",
    lead_id: "2",
    draft_id: "draft_2",
    company: "TechSolutions Inc.",
    website: "https://techsolutions.com",
    industry: "Information Technology",
    productCategory: "Software Development",
    businessType: "B2B",
    employees: "120",
    revenue: "$25M",
    yearFounded: "2010",
    bbbRating: "A",
    street: "456 Tech Boulevard",
    city: "San Francisco",
    state: "CA",
    companyPhone: "(415) 555-7890",
    companyLinkedin: "https://linkedin.com/company/techsolutions",
    ownerFirstName: "Sarah",
    ownerLastName: "Johnson",
    ownerTitle: "CTO",
    ownerLinkedin: "https://linkedin.com/in/sarahjohnson",
    ownerPhoneNumber: "(415) 555-1234",
    ownerEmail: "sarah.johnson@techsolutions.com",
    source: "Web Scraper",
    created: "2023-04-10T09:15:00Z",
    updated: "2023-05-18T11:20:00Z",
    sourceType: "database"
},
{
    id: "3",
    lead_id: "3",
    draft_id: "draft_3",
    company: "GreenEarth Organics",
    website: "https://greenearth.com",
    industry: "Agriculture",
    productCategory: "Organic Produce",
    businessType: "B2C",
    employees: "75",
    revenue: "$12M",
    yearFounded: "2005",
    bbbRating: "A+",
    street: "789 Farm Road",
    city: "Portland",
    state: "OR",
    companyPhone: "(503) 555-4567",
    companyLinkedin: "https://linkedin.com/company/greenearth",
    ownerFirstName: "Michael",
    ownerLastName: "Brown",
    ownerTitle: "Founder",
    ownerLinkedin: "https://linkedin.com/in/michaelbrown",
    ownerPhoneNumber: "(503) 555-8901",
    ownerEmail: "michael.brown@greenearth.com",
    source: "Trade Show",
    created: "2023-03-22T14:00:00Z",
    updated: "2023-04-30T16:30:00Z",
    sourceType: "database"
},
{
    id: "4",
    lead_id: "4",
    draft_id: "draft_4",
    company: "UrbanStyle Apparel",
    website: "https://urbanstyle.com",
    industry: "Fashion",
    productCategory: "Clothing",
    businessType: "B2C",
    employees: "200",
    revenue: "$40M",
    yearFounded: "2015",
    bbbRating: "A-",
    street: "321 Fashion Avenue",
    city: "New York",
    state: "NY",
    companyPhone: "(212) 555-6789",
    companyLinkedin: "https://linkedin.com/company/urbanstyle",
    ownerFirstName: "Jessica",
    ownerLastName: "Williams",
    ownerTitle: "Creative Director",
    ownerLinkedin: "https://linkedin.com/in/jessicawilliams",
    ownerPhoneNumber: "(212) 555-2345",
    ownerEmail: "jessica.williams@urbanstyle.com",
    source: "Social Media",
    created: "2023-02-18T11:45:00Z",
    updated: "2023-03-25T13:15:00Z",
    sourceType: "database"
},
{
    id: "5",
    lead_id: "5",
    draft_id: "draft_5",
    company: "BlueOcean Consulting",
    website: "https://blueocean.com",
    industry: "Professional Services",
    productCategory: "Business Consulting",
    businessType: "B2B",
    employees: "50",
    revenue: "$15M",
    yearFounded: "2018",
    bbbRating: "A",
    street: "654 Corporate Lane",
    city: "Boston",
    state: "MA",
    companyPhone: "(617) 555-3456",
    companyLinkedin: "https://linkedin.com/company/blueocean",
    ownerFirstName: "David",
    ownerLastName: "Miller",
    ownerTitle: "Managing Partner",
    ownerLinkedin: "https://linkedin.com/in/davidmiller",
    ownerPhoneNumber: "(617) 555-7890",
    ownerEmail: "david.miller@blueocean.com",
    source: "Referral",
    created: "2023-01-05T08:30:00Z",
    updated: "2023-02-12T10:45:00Z",
    sourceType: "database"
}
];

const LinkedInMessageGenerator = ({ 
  company, 
  onClose,
  onGenerate,
  generatedMessage,
  isGenerating,
  settings,
  onSettingsChange
}) => {
  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">LinkedIn Message Generator</h2>
        <button 
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="space-y-4">
        <div className="p-4 border rounded-lg text-white bg-gray-600">
          <p className="font-medium">Company:</p>
          <p className="text-lg">{company.company}</p>
          {company.ownerLinkedin && (
            <p className="text-sm text-white mt-1">
              Recipient: <a href={company.ownerLinkedin} target="_blank" rel="noopener noreferrer" className="text-blue-600">
                {company.ownerFirstName} {company.ownerLastName}
              </a>
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
              value={settings.extraContext}
              onChange={(e) => onSettingsChange({...settings, extraContext: e.target.value})}
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
            <div className="p-4 border rounded-lg text-white bg-gray-600 whitespace-pre-wrap">
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
                window.open(
                  `https://www.linkedin.com/messaging/compose/?to=${company.ownerLinkedin?.split('/in/')[1]}`,
                  '_blank'
                );
              }}>
                Open in LinkedIn
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default function CompaniesPage() {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    // Copy ALL state from the original scraping history component
    const [searchTerm, setSearchTerm] = useState("");
    const [employeesFilter, setEmployeesFilter] = useState("");
    const [revenueFilter, setRevenueFilter] = useState("");
    const [businessTypeFilter, setBusinessTypeFilter] = useState("");
    const [productFilter, setProductFilter] = useState("");
    const [yearFoundedFilter, setYearFoundedFilter] = useState("");
    const [bbbRatingFilter, setBbbRatingFilter] = useState("");
    const [streetFilter, setStreetFilter] = useState("");
    const [industryFilter, setIndustryFilter] = useState("");
    const [cityFilter, setCityFilter] = useState("");
    const [stateFilter, setStateFilter] = useState("");
    const [sourceFilter, setSourceFilter] = useState("");
    const [showFilters, setShowFilters] = useState(false);
    const [selectAll, setSelectAll] = useState(false);
    const [scrapingHistory, setScrapingHistory] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(25);
    const [selectedCompanies, setSelectedCompanies] = useState([]);
    const [notif, setNotif] = useState({
        show: false,
        message: "",
        type: "success",
    });
    const [popupData, setPopupData] = useState(null); // null means no popup open
    const [popupTab, setPopupTab] = useState('overview');
    const [isEditing, setIsEditing] = useState(false);

    // Add to your existing state declarations
    const [linkedinPopupData, setLinkedinPopupData] = useState(null);
    const [generatedMessage, setGeneratedMessage] = useState("");
    const [isGenerating, setIsGenerating] = useState(false);
    const [messageSettings, setMessageSettings] = useState({
    tone: "professional",
    focus: "partnership",
    extraContext: ""
    });
    const router = useRouter();

    const saveLeadToAPI = async (lead) => {
        const toSnake = (str) => str.replace(/([A-Z])/g, "_$1").toLowerCase();
        const normalizeKeys = (obj) => {
            const result = {};
            for (const [k, v] of Object.entries(obj)) {
                result[toSnake(k)] = v;
            }
            return result;
        };

        const normalizedLead = normalizeKeys(lead);
        normalizedLead.user_id = user.id;

        try {
            // First POST
            const postResponse = await axios.post(
                `${DATABASE_URL_NOAPI}/leads/${lead.id}/edit`,
                normalizedLead,
                { withCredentials: true }
            );

            // Then PUT
            const payload = {
                draft_data: normalizedLead,
                change_summary: "Updated from popup",
                phase: "draft",
                status: "pending",
            };
            const actualDraftId = postResponse.data?.draft?.draft_id || lead.draft_id;

            await axios.put(`${DATABASE_URL}/leads/drafts/${actualDraftId}`, payload, {
                withCredentials: true,
            });

            return { success: true, updatedLead: { ...lead, ...normalizedLead } };
        } catch (err) {
            console.error("❌ Error saving lead:", err);
            return { success: false, error: err };
        }
    };

    const handlePopupSave = async () => {
        if (!popupData) return;

        const result = await saveLeadToAPI(popupData);

        if (result.success) {
            const updatedList = scrapingHistory.map((item) =>
                item.id === popupData.id ? popupData : item
            );
            setScrapingHistory(updatedList);
            setIsEditing(false);
            showNotification("Changes saved.", "success");
        } else {
            showNotification("Failed to save changes.", "error");
        }
    };

    const showNotification = (message, type = "success") => {
        setNotif({ show: true, message, type });

        // Automatically hide after X seconds
        setTimeout(() => {
        setNotif((prev) => ({ ...prev, show: false }));
        }, 3500);
    };

    const clearAllFilters = () => {
        setEmployeesFilter("");
        setRevenueFilter("");
        setBusinessTypeFilter("");
        setProductFilter("");
        setYearFoundedFilter("");
        setBbbRatingFilter("");
        setStreetFilter("");
        setCityFilter("");
        setStateFilter("");
        setSourceFilter("");
    };

    const parseRevenue = (revenueInput) => {
        if (typeof revenueInput === "number") return revenueInput;
        if (typeof revenueInput !== "string") return null;

        let revenueStr = revenueInput.toLowerCase().trim().replace(/[$,]/g, "");
        let multiplier = 1;

        if (revenueStr.endsWith("k")) {
        multiplier = 1_000;
        revenueStr = revenueStr.slice(0, -1);
        } else if (revenueStr.endsWith("m")) {
        multiplier = 1_000_000;
        revenueStr = revenueStr.slice(0, -1);
        } else if (revenueStr.endsWith("b")) {
        multiplier = 1_000_000_000;
        revenueStr = revenueStr.slice(0, -1);
        }

        const value = parseFloat(revenueStr);
        return isNaN(value) ? null : value * multiplier;
    };

    const parseFilter = (filterStr, isRevenue = false) => {
        const result = {
        operation: "exact",
        value: null | null,
        upper: null | null,
        };
        filterStr = filterStr.toLowerCase().trim();
        const rangeMatch = filterStr.match(
        /^(\d+(?:[kmb]?)?)\s*-\s*(\d+(?:[kmb]?)?)$/
        );
        if (rangeMatch) {
        const val1 = isRevenue
            ? parseRevenue(rangeMatch[1])
            : parseInt(rangeMatch[1]);
        const val2 = isRevenue
            ? parseRevenue(rangeMatch[2])
            : parseInt(rangeMatch[2]);
        return { operation: "between", value: val1, upper: val2 };
        }
        if (filterStr.startsWith(">="))
        (result.operation = "greater than or equal"),
            (filterStr = filterStr.slice(2));
        else if (filterStr.startsWith(">"))
        (result.operation = "greater than"), (filterStr = filterStr.slice(1));
        else if (filterStr.startsWith("<="))
        (result.operation = "less than or equal"),
            (filterStr = filterStr.slice(2));
        else if (filterStr.startsWith("<"))
        (result.operation = "less than"), (filterStr = filterStr.slice(1));
        result.value = isRevenue ? parseRevenue(filterStr) : parseInt(filterStr);
        return result;
    };

    const toCamelCase = (str) =>
        str.replace(/([-_][a-z])/gi, (group) =>
        group.toUpperCase().replace("-", "").replace("_", "")
        );

    const toCamelCaseKeys = (obj) => {
        const newObj = {};
        for (const key in obj) {
        const camelKey = toCamelCase(key);
        newObj[camelKey] = obj[key];
        }
        return newObj;
    };

    const ExpandableCell = ({ text, onClick }) => {
        const [expanded, setExpanded] = useState(false);
        const isLong = text && text.length > 100;
        if (!isLong) return <span onClick={onClick}>{text}</span>;
        return (
            <div className="whitespace-pre-wrap">
                <span onClick={onClick}>
                    {expanded ? text : text.slice(0, 30) + "... "}
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

    const handleExportCSV = () => {
        const headers = [
        "Company",
        "Website",
        "Industry",
        "Product Category",
        "Business Type",
        "Employees",
        "Revenue",
        "Year Founded",
        "BBB Rating",
        "Street",
        "City",
        "State",
        "Company Phone",
        "Company LinkedIn",
        "Owner First Name",
        "Owner Last Name",
        "Owner Title",
        "Owner LinkedIn",
        "Owner Phone Number",
        "Owner Email",
        "Source",
        "Created At",
        "Updated At",
        ];

        const csvContent = [
        headers.join(","), // Header row
        ...scrapingHistory.map((row) =>
            headers
            .map((h) => {
                const key =
                h === "Created At"
                    ? "created"
                    : h === "Updated At"
                    ? "updated"
                    : toCamelCaseKeys(h);
                return `"${row[key] || ""}"`;
            })
            .join(",")
        ),
        ].join("\n");

        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "scraping_history.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportCSVWithCredits = async () => {
        try {
        const { data: subscriptionInfo } = await axios.get(
            `${DATABASE_URL}/user/subscription_info`,
            {
            withCredentials: true,
            }
        );

        const planName =
            subscriptionInfo?.subscription?.plan_name?.toLowerCase() ?? "free";
        const availableCredits =
            subscriptionInfo?.subscription?.credits_remaining ?? 0;
        const requiredCredits = scrapingHistory.length;

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

        handleExportCSV();
        } catch (checkErr) {
        console.error("❌ Failed to verify subscription:", checkErr);
        showNotification(
            "Failed to verify your subscription. Please try again later.",
            "error"
        );
        }
    };

    const handleToggleFiltersWithCheck = async () => {
        try {
        const { data: subscriptionInfo } = await axios.get(
            `${DATABASE_URL}/user/subscription_info`,
            { withCredentials: true }
        );
        const planName =
            subscriptionInfo?.subscription?.plan_name?.toLowerCase() ?? "free";
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

    const filteredScrapingHistory = scrapingHistory.filter((entry) => {
        const matchIndustry = entry.industry
        ?.toLowerCase()
        .includes(industryFilter.toLowerCase());
        const matchCity = entry.city
        ?.toLowerCase()
        .includes(cityFilter.toLowerCase());
        const matchState = entry.state
        ?.toLowerCase()
        .includes(stateFilter.toLowerCase());
        const matchBBB = entry.bbbRating
        ?.toLowerCase()
        .includes(bbbRatingFilter.toLowerCase());
        const matchProduct = entry.productCategory
        ?.toLowerCase()
        .includes(productFilter.toLowerCase());
        const matchBusinessType = entry.businessType
        ?.toLowerCase()
        .includes(businessTypeFilter.toLowerCase());
        const matchSource = entry.source
        ?.toLowerCase()
        .includes(sourceFilter.toLowerCase());

        const {
        operation: revenueOp,
        value: revenueVal,
        upper: revenueUpper,
        } = parseFilter(revenueFilter, true);
        const rev = parseRevenue(entry.revenue);
        const matchRevenue =
        revenueVal === null
            ? true
            : revenueOp === "less than"
            ? rev < revenueVal
            : revenueOp === "greater than"
            ? rev > revenueVal
            : revenueOp === "less than or equal"
            ? rev <= revenueVal
            : revenueOp === "greater than or equal"
            ? rev >= revenueVal
            : revenueOp === "between"
            ? rev >= revenueVal && rev <= (revenueUpper ?? revenueVal)
            : rev === revenueVal;

        const {
        operation: empOp,
        value: empVal,
        upper: empUpper,
        } = parseFilter(employeesFilter);
        const emp = parseInt(entry.employees);
        const matchEmployees = isNaN(empVal)
        ? true
        : empOp === "less than"
        ? emp < empVal
        : empOp === "greater than"
        ? emp > empVal
        : empOp === "less than or equal"
        ? emp <= empVal
        : empOp === "greater than or equal"
        ? emp >= empVal
        : empOp === "between"
        ? emp >= empVal && emp <= (empUpper ?? empVal)
        : emp === empVal;

        const {
        operation: yearOp,
        value: yearVal,
        upper: yearUpper,
        } = parseFilter(yearFoundedFilter);
        const year = parseInt(entry.yearFounded);
        const matchYearFounded = isNaN(yearVal)
        ? true
        : yearOp === "less than"
        ? year < yearVal
        : yearOp === "greater than"
        ? year > yearVal
        : yearOp === "less than or equal"
        ? year <= yearVal
        : yearOp === "greater than or equal"
        ? year >= yearVal
        : yearOp === "between"
        ? year >= yearVal && year <= (yearUpper ?? yearVal)
        : year === yearVal;

        return (
        matchIndustry &&
        matchCity &&
        matchState &&
        matchBBB &&
        matchProduct &&
        matchBusinessType &&
        matchRevenue &&
        matchSource &&
        matchEmployees &&
        matchYearFounded
        );
    });

    const totalPages = Math.ceil(filteredScrapingHistory.length / itemsPerPage);
    const indexOfFirstItem = (currentPage - 1) * itemsPerPage;
    const indexOfLastItem = currentPage * itemsPerPage;
    const currentItems = filteredScrapingHistory.slice(
    indexOfFirstItem,
    indexOfLastItem
    );

    const handleSelectAll = () => {
        const visibleIds = scrapingHistory
        .slice(indexOfFirstItem, indexOfLastItem)
        .map((entry) => entry.id);

        if (selectAll) {
        setSelectedCompanies([]);
        } else {
        setSelectedCompanies(visibleIds);
        }

        setSelectAll(!selectAll);
    };

    const handleSelectCompany = (id) => {
        if (selectedCompanies.includes(id)) {
        setSelectedCompanies(selectedCompanies.filter(companyId => companyId !== id));
        } else {
        setSelectedCompanies([...selectedCompanies, id]);
        }
    };

    const handleSortBy = (sortBy, direction) => {
        // Count how many non‐empty fields each row has:
        const getFilledCount = (row) =>
        Object.entries(row).filter(([key, value]) => {
            if (
            ["id", "lead_id", "draft_id", "sourceType"].includes(key) ||
            value === null ||
            value === undefined ||
            value === "" ||
            value === "N/A"
            ) {
            return false;
            }
            return true;
        }).length;

        // Determine the base array to sort:
        const base = [...scrapingHistory];

        // Sort by completeness only if sortBy === "filled", otherwise you can
        // extend this switch for revenue, employees, etc.:
        const sorted = base.sort((a, b) => {
        if (sortBy === "filled") {
            const aCount = getFilledCount(a);
            const bCount = getFilledCount(b);
            return direction === "most" ? bCount - aCount : aCount - bCount;
        }
        // Example: alphabetical company
        if (sortBy === "company") {
            return direction === "most"
            ? b.company.localeCompare(a.company)
            : a.company.localeCompare(b.company);
        }
        // ...add more sortBy cases here...
        return 0;
        });

        // Push the new order into state:
        setScrapingHistory(sorted);
        setCurrentPage(1); // reset pagination to page 1
    };

    // Fetch data on component mount
    useEffect(() => {
    const storedUser = typeof window !== "undefined" 
        ? JSON.parse(sessionStorage.getItem("user") || "{}")
        : {};
    setUser(storedUser);

    const fetchDrafts = async () => {
        try {
        const draftsRes = await fetch(`${DATABASE_URL}/leads/drafts`, {
            method: "GET",
            credentials: "include",
        });

        if (!draftsRes.ok) {
            throw new Error("API request failed");
        }

        const data = await draftsRes.json();
        const parsed = data.map((entry) => {
            const draftData = entry.draft_data || {};
            return {
            id: entry.lead_id || entry.id || "",
            lead_id: entry.lead_id || entry.id || "",
            draft_id: entry.draft_id || "",
            company: draftData.company || "N/A",
            website: draftData.website || "",
            industry: draftData.industry || "",
            productCategory: draftData.product_category || "",
            businessType: draftData.business_type || "",
            employees: draftData.employees || "",
            revenue: draftData.revenue || "",
            yearFounded: draftData.year_founded?.toString() || "",
            bbbRating: draftData.bbb_rating || "",
            street: draftData.street || "",
            city: draftData.city || "",
            state: draftData.state || "",
            companyPhone: draftData.company_phone || "",
            companyLinkedin: draftData.company_linkedin || "",
            ownerFirstName: draftData.owner_first_name || "",
            ownerLastName: draftData.owner_last_name || "",
            ownerTitle: draftData.owner_title || "",
            ownerLinkedin: draftData.owner_linkedin || "",
            ownerPhoneNumber: draftData.owner_phone_number || "",
            ownerEmail: draftData.owner_email || "",
            source: draftData.source || "",
            created: entry.created_at
                ? new Date(entry.created_at).toLocaleString()
                : "N/A",
            updated: entry.updated_at
                ? new Date(entry.updated_at).toLocaleString()
                : "N/A",
            sourceType: "database",
            };
        });

        setScrapingHistory(parsed);
        } catch (error) {
        console.error("Error fetching drafts, using dummy data:", error);
        // Use dummy data when API fails
        setScrapingHistory(dummyData.map(item => ({
            ...item,
            created: new Date(item.created).toLocaleString(),
            updated: new Date(item.updated).toLocaleString()
        })));
        showNotification("Using sample data while API is unavailable", "info");
        } finally {
        setIsLoading(false);
        }
    };

    fetchDrafts();
    }, []);

    if (isLoading) {
    return (
        <div className="flex flex-col h-screen">
        <Header />
        <div className="flex flex-1 overflow-hidden">
            <Sidebar />
            <main className="flex-1 p-6 overflow-auto flex items-center justify-center">
            <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-yellow-400"></div>
            </main>
        </div>
        </div>
    );
    }

    const overviewFields = [
        { key: "company", label: "Company" },
        { key: "website", label: "Website" },
        { key: "companyLinkedin", label: "Company LinkedIn" },
        { key: "industry", label: "Industry" },
        { key: "productCategory", label: "Product/Service Category" },
        { key: "businessType", label: "Business Type" },
        { key: "employees", label: "Employees Count" },
        { key: "revenue", label: "Revenue" },
        { key: "yearFounded", label: "Year Founded" },
        { key: "bbbRating", label: "BBB Rating" },
        { key: "street", label: "Street" },
        { key: "city", label: "City" },
        { key: "state", label: "State" },
        { key: "companyPhone", label: "Company Phone" },
        { key: "source", label: "Source" },
    ];

    const peopleFields = [
        { key: "ownerFirstName", label: "Owner First Name" },
        { key: "ownerLastName", label: "Owner Last Name" },
        { key: "ownerTitle", label: "Owner Title" },
        { key: "ownerLinkedin", label: "Owner LinkedIn" },
        { key: "ownerPhoneNumber", label: "Owner Phone Number" },
        { key: "ownerEmail", label: "Owner Email" },
    ];

    // Replace your current LinkedIn message button click handler with this:
    const handleLinkedInMessageClick = (company) => {
        setLinkedinPopupData(company);
        setGeneratedMessage(""); // Clear any previous message
    };

    return (
    <div className="flex flex-col h-screen">
        <FeedbackPopup />
        <Header />
        <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 p-6 overflow-auto">
            <h1 className="text-2xl font-bold text-foreground mb-6">Companies</h1>
            
            {/* History Table */}
            <div className="mt-10">
                {/* Table container */}
                <div className="w-full overflow-x-auto rounded-md border">
                {/* Toolbar */}
                <div className="flex flex-wrap items-center justify-between p-4 border-b bg-surface">
                    {/* Search */}
                    <div className="flex-grow max-w-xs">
                    <Input
                        placeholder="Search history…"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full"
                    />
                    </div>
    
                    {/* Actions */}
                    <div className="flex items-center gap-2">
                    <SortDropdown onApply={handleSortBy} />
    
                    <Button
                        variant="outline"
                        size="icon"
                        onClick={handleToggleFiltersWithCheck}
                        title={showFilters ? "Hide Filters" : "Show Filters"}
                    >
                        <Filter className="h-4 w-4" />
                    </Button>
    
                    <Button
                        variant="outline"
                        size="icon"
                        onClick={handleExportCSVWithCredits}
                        title="Export CSV"
                    >
                        <Download className="h-4 w-4" />
                    </Button>
                    </div>
                </div>
                </div>
                {showFilters && (
                <div className="flex flex-wrap gap-4 my-4">
                    <Input
                    placeholder="Industry"
                    value={industryFilter}
                    onChange={(e) => setIndustryFilter(e.target.value)}
                    className="w-[240px]"
                    />
                    <Input
                    placeholder="Product/Service Category"
                    value={productFilter}
                    onChange={(e) => setProductFilter(e.target.value)}
                    className="w-[240px]"
                    />
                    <Input
                    placeholder="Business Type"
                    value={businessTypeFilter}
                    onChange={(e) => setBusinessTypeFilter(e.target.value)}
                    className="w-[240px]"
                    />
                    <Input
                    placeholder="Employees Count"
                    value={employeesFilter}
                    onChange={(e) => setEmployeesFilter(e.target.value)}
                    className="w-[240px]"
                    />
                    <Input
                    placeholder="Revenue"
                    value={revenueFilter}
                    onChange={(e) => setRevenueFilter(e.target.value)}
                    className="w-[240px]"
                    />
                    <Input
                    placeholder="Year Founded"
                    value={yearFoundedFilter}
                    onChange={(e) => setYearFoundedFilter(e.target.value)}
                    className="w-[240px]"
                    />
                    <Input
                    placeholder="BBB Rating"
                    value={bbbRatingFilter}
                    onChange={(e) => setBbbRatingFilter(e.target.value)}
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
                    placeholder="Source"
                    value={sourceFilter}
                    onChange={(e) => setSourceFilter(e.target.value)}
                    className="w-[240px]"
                    />
                    <Button variant="ghost" size="sm" onClick={clearAllFilters}>
                    <X className="h-4 w-4 mr-1" />
                    Clear All
                    </Button>
                </div>
                )}
                {/* Scrollable container */}
                <div className="w-full overflow-x-auto relative border rounded-md">
                <Table className="min-w-full text-sm ">
                    <TableHeader>
                    <TableRow>
                        {/* Sticky Checkbox Column */}
                        <TableHead className="sticky top-0 left-0 z-40 bg-[#1e263a] px-6 py-3 w-12 text-base font-bold text-white">
                        <Checkbox
                            checked={selectAll}
                            onCheckedChange={handleSelectAll}
                        />
                        </TableHead>
    
                        {/* Sticky Company Column */}
                        <TableHead className="sticky top-0 left-[3rem] z-30 bg-[#1e263a] text-base font-bold text-white px-6 py-3 whitespace-nowrap min-w-[200px]">
                        Company
                        </TableHead>

                        <TableHead className="sticky top-0 z-20 bg-[#1e263a] text-base font-bold text-white px-6 py-3 whitespace-nowrap">
                        Actions
                        </TableHead>
    
                        {/* Remaining Headers */}
                        {[
                        "Industry",
                        "Links",
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
                        "Source",
                        "Created Date",
                        "Updated",
                        ].map((label, i) => (
                        <TableHead
                            key={i}
                            className="sticky top-0 z-20 bg-[#1e263a] text-base font-bold text-white px-6 py-3 whitespace-nowrap"
                        >
                            {label}
                        </TableHead>
                        ))}
                    </TableRow>
                    </TableHeader>
    
                    <tbody>
                    {currentItems.map((row, i) => (
                        <TableRow key={i} className="border-t">
                        {/* Sticky Checkbox Column */}
                        <TableCell className="sticky left-0 z-20 bg-inherit px-6 py-2 w-12  ">
                            <Checkbox
                            checked={selectedCompanies.includes(row.id)}
                            onCheckedChange={() => handleSelectCompany(row.id)}
                            />
                        </TableCell>
    
                        {/* Sticky Company Column */}
                        <TableCell
                            key="company"
                            className="sticky left-[3rem] z-10 bg-inherit px-6 py-2 max-w-[240px] align-top cursor-pointer"
                        >
                            <ExpandableCell text={row.company || "N/A"} />
                        </TableCell>

                        {/* Action Column */}
                        <TableCell className="px-6 py-2">
                            <div className="flex items-center space-x-3">
                            <button
                                onClick={() => {
                                    setPopupData(row);
                                    setIsEditing(false);
                                    setPopupTab('overview');
                                }}
                                title="View Details"
                                className="hover:bg-gray-100 rounded p-1"
                                >
                                <Eye className="w-4 h-4 text-blue-500" />
                            </button>
                            {row.ownerLinkedin && (
                            <button
                                onClick={() => handleLinkedInMessageClick(row)}
                                title="Send LinkedIn Message"
                                className="hover:bg-gray-100 rounded p-1"
                            >
                                <MessageSquare className="w-4 h-4 text-blue-700" />
                            </button>
                            )}
                            <button
                                onClick={() => {
                                    setPopupData(row);
                                    setIsEditing(true);
                                    setPopupTab('overview');
                                }}
                                title="Edit"
                                className="hover:bg-gray-100 rounded p-1"
                            >
                                <Pencil className="w-4 h-4 text-blue-600" />
                            </button>

                            <button
                                title="Notes - Coming soon!"
                                className="hover:bg-gray-100 rounded p-1 group relative"
                                onClick={() => {}}
                            >
                                <StickyNote className="w-4 h-4 text-yellow-500" />
                                <span className="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-300 absolute z-10 w-32 p-2 text-xs text-white bg-gray-800 rounded shadow-lg -top-8 -left-1/2">
                                    Notes feature coming soon!
                                </span>
                            </button>
                            </div>

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
                        </TableCell>
    
                        {/* Remaining Cells */}
                        {[
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
                            "source",
                            "created",
                            "updated",
                        ].map((field, fieldIndex) => {
                            const rawValue = row[field];
                            const displayValue =
                            rawValue === null ||
                            rawValue === undefined ||
                            rawValue === ""
                                ? "N/A"
                                : rawValue;
    
                            const isUrl =
                            typeof rawValue === "string" &&
                            (rawValue.startsWith("http://") ||
                                rawValue.startsWith("https://"));
    
                            const shortened =
                            isUrl && rawValue.length > 0
                                ? rawValue
                                    .replace(/^https?:\/\//, "")
                                    .replace(/^www\./, "")
                                    .split("/")[0]
                                : displayValue;
    
                            return (
                            <React.Fragment key={field}>
                                <TableCell className="px-6 py-2 max-w-[240px] align-top">
                                    {isUrl ? (
                                    <a
                                        href={rawValue}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 underline hover:text-blue-800 block truncate"
                                        title={rawValue}
                                    >
                                        {shortened}
                                    </a>
                                    ) : (
                                    <ExpandableCell text={displayValue} />
                                    )}
                                </TableCell>

                                {/* Inject Actions Cell after "industry" */}
                                {field === "industry" && (
                                    <TableCell className="px-6 py-2 max-w-[240px] align-top space-x-2 whitespace-nowrap">
                                        {row.website && (
                                        <a
                                            href={row.website}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-block p-1 rounded hover:bg-gray-200"
                                            title="Website"
                                        >
                                            <Globe className="h-4 w-4 text-blue-600" />
                                        </a>
                                        )}
                                        {row.companyLinkedin && (
                                        <a
                                            href={row.companyLinkedin}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-block p-1 rounded hover:bg-gray-200"
                                            title="LinkedIn"
                                        >
                                            <Linkedin className="h-4 w-4 text-blue-700" />
                                        </a>
                                        )}
                                        {row.ownerEmail && (
                                        <a
                                            href={`mailto:${row.ownerEmail}`}
                                            onClick={(e) => {
                                            setTimeout(() => {
                                                window.open(`https://mail.google.com/mail/?view=cm&fs=1&to=${row.ownerEmail}`, '_blank');
                                            }, 500);
                                            }}
                                            title="Send Email"
                                            className="inline-block p-1 rounded hover:bg-gray-200"
                                        >
                                            <Mail className="h-4 w-4 text-green-600" />
                                        </a>
                                        )}
                                        {(row.street || row.city || row.state) && (
                                        <a
                                            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${row.street || ""}, ${row.city || ""}, ${row.state || ""}`)}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-block p-1 rounded hover:bg-gray-200"
                                            title="Map Location"
                                        >
                                            <MapPin className="h-4 w-4 text-red-600" />
                                        </a>
                                        )}
                                    </TableCell>
                                )}
                            </React.Fragment>
                            );
                        })}

                        </TableRow>
                    ))}
                    </tbody>
                </Table>
                </div>
                <div className="flex flex-col md:flex-row justify-between items-center mt-4 gap-4 px-4 py-2">
                <div className="text-sm text-muted-foreground">
                    Showing {indexOfFirstItem + 1}–
                    {Math.min(indexOfLastItem, scrapingHistory.length)} of{" "}
                    {scrapingHistory.length} results
                </div>
    
                <div className="flex items-center gap-3 px-3 py-2">
                    <Select
                    value={itemsPerPage.toString()}
                    onValueChange={(value) => {
                        setItemsPerPage(Number(value));
                        setCurrentPage(1);
                    }}
                    >
                    <SelectTrigger className="w-[120px]  text-black font-medium rounded-md hover:bg-[#6bb293]">
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
                            onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                            aria-disabled={currentPage === 1}
                            className={
                            currentPage === 1
                                ? "pointer-events-none opacity-50"
                                : ""
                            }
                        />
                        </PaginationItem>
    
                        {Array.from({ length: totalPages }, (_, i) => i + 1)
                        .filter((page) => {
                            // show all if totalPages <= 7
                            if (totalPages <= 7) return true;
    
                            // show first, last, current, and neighbors
                            return (
                            page === 1 ||
                            page === totalPages ||
                            Math.abs(page - currentPage) <= 1
                            );
                        })
                        .reduce((acc, page, i, arr) => {
                            if (i > 0 && page - arr[i - 1] > 1) {
                            acc.push("ellipsis");
                            }
                            acc.push(page);
                            return acc;
                        }, [])
                        .map((page, idx) => (
                            <PaginationItem key={idx}>
                            {page === "ellipsis" ? (
                                <PaginationEllipsis />
                            ) : (
                                <PaginationLink
                                isActive={page === currentPage}
                                onClick={() => setCurrentPage(page)}
                                className={`px-3 py-1 rounded-md text-sm font-medium ${
                                    page === currentPage
                                    ? " text-black" // active teal background
                                    : "text-black hover:bg-muted"
                                }`}
                                >
                                {page}
                                </PaginationLink>
                            )}
                            </PaginationItem>
                        ))}
    
                        <PaginationItem>
                        <PaginationNext
                            onClick={() =>
                            setCurrentPage((p) => Math.min(p + 1, totalPages))
                            }
                            aria-disabled={currentPage === totalPages}
                            className={
                            currentPage === totalPages
                                ? "pointer-events-none opacity-50"
                                : ""
                            }
                        />
                        </PaginationItem>
                    </PaginationContent>
                    </Pagination>
                </div>
                </div>
            </div>

            <PopupBig show={!!popupData} onClose={() => {
            setPopupData(null);
            setIsEditing(false);
            setPopupTab('overview');
            }}>
            {popupData && (
                <div className="space-y-8">
                {/* Title and Tabs */}
                <div className="border-b pb-4">
                    <h2 className="text-3xl font-semibold tracking-tight text-gray-900 dark:text-white">
                    {popupData.company}
                    </h2>
                    
                    {/* Tab Navigation */}
                    <div className="flex space-x-4 mt-4">
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
                        onClick={() => setPopupTab('people')}
                        className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                        popupTab === 'people'
                            ? 'border-teal-500 text-teal-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        People
                    </button>
                    </div>
                </div>

                {/* Overview Tab Content */}
                {popupTab === 'overview' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {overviewFields.map(({ key, label }) => {
                        let value = popupData[key] || "";
                        const isLink = key === "website" || key === "companyLinkedin";
                        
                        // Special handling for website field
                        if (key === "website" && value && !value.startsWith('http')) {
                            value = `https://${value}`;
                        }

                        return (
                        <div key={key} className="space-y-1">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            {label}
                            </label>
                            {isEditing ? (
                            <Input
                                value={value}
                                onChange={(e) =>
                                setPopupData({ ...popupData, [key]: e.target.value })
                                }
                                className="text-sm"
                                placeholder={isLink ? "https://..." : ""}
                            />
                            ) : (
                            <div className="px-3 py-2 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-zinc-800 text-sm text-gray-900 dark:text-white">
                                {isLink && value ? (
                                <a 
                                    href={value} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                >
                                    {value}
                                </a>
                                ) : value || <span className="italic text-gray-400">N/A</span>}
                            </div>
                            )}
                        </div>
                        );
                    })}
                    </div>
                )}

                {/* People Tab Content */}
                {popupTab === 'people' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {peopleFields.map(({ key, label }) => {
                        const value = popupData[key] || "";
                        const isLink = key === "ownerLinkedin";
                        
                        return (
                        <div key={key} className="space-y-1">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            {label}
                            </label>
                            {isEditing ? (
                            <Input
                                value={value}
                                onChange={(e) =>
                                setPopupData({ ...popupData, [key]: e.target.value })
                                }
                                className="text-sm"
                                placeholder={isLink ? "https://..." : ""}
                            />
                            ) : (
                            <div className="px-3 py-2 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-zinc-800 text-sm text-gray-900 dark:text-white">
                                {isLink && value ? (
                                <a 
                                    href={value} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                >
                                    {value}
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
                    {!isEditing ? (
                    // <Button
                    //     size="sm"
                    //     variant="outline"
                    //     onClick={() => setIsEditing(true)}
                    //     className="ml-auto"
                    // >
                    //     Edit
                    // </Button>
                    null
                    ) : (
                    <>
                        {/* <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setIsEditing(false)}
                        className="text-red-500 hover:text-red-600"
                        >
                        Cancel
                        </Button> */}
                        <Button size="sm" onClick={handlePopupSave}>
                        Save Changes
                        </Button>
                    </>
                    )}
                </div>
                </div>
            )}
            </PopupBig>
            <PopupBig show={!!linkedinPopupData} onClose={() => setLinkedinPopupData(null)}>
            {linkedinPopupData && (
                <LinkedInMessageGenerator
                company={linkedinPopupData}
                onClose={() => setLinkedinPopupData(null)}
                onGenerate={async () => {
                    setIsGenerating(true);
                    
                    // Mock API call - replace with real API when ready
                    try {
                    // This is where you'll call the real API
                    // const response = await axios.post('/api/generate-linkedin-message', {
                    //   company_name: linkedinPopupData.company,
                    //   website_url: linkedinPopupData.website,
                    //   user_linkedin_url: "https://linkedin.com/in/user", // You'll need to get this from user profile
                    //   founder_linkedin_url: linkedinPopupData.ownerLinkedin,
                    //   extra_context: messageSettings.extraContext,
                    //   tone: messageSettings.tone,
                    //   focus: messageSettings.focus
                    // });
                    // setGeneratedMessage(response.data.message);
                    
                    // Mock response for now
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    const mockMessage = `Hi ${linkedinPopupData.ownerFirstName || 'there'},

            I came across ${linkedinPopupData.company} and was impressed by your work in ${linkedinPopupData.industry || 'your industry'}. I'd love to connect and explore potential ${messageSettings.focus} opportunities.

            ${messageSettings.extraContext ? `\n${messageSettings.extraContext}\n` : ''}
            Looking forward to your thoughts!

            Best regards,
            [Your Name]`;
                    
                    setGeneratedMessage(mockMessage);
                    } catch (error) {
                    console.error("Error generating message:", error);
                    // You might want to show an error notification here
                    } finally {
                    setIsGenerating(false);
                    }
                }}
                generatedMessage={generatedMessage}
                isGenerating={isGenerating}
                settings={messageSettings}
                onSettingsChange={setMessageSettings}
                />
            )}
            </PopupBig>

            {/* Notification */}
            <div className="flex justify-end mt-3 gap-3">
            <Notif
                show={notif.show}
                message={notif.message}
                type={notif.type}
                onClose={() => setNotif((prev) => ({ ...prev, show: false }))}
            />
            </div>
        </main>
        </div>
    </div>
    );
}