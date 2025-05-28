"use client"
import React from "react"
import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { EnrichmentResults } from "../components/enrichment-results"
import { Button } from "../components/ui/button"
import { Checkbox } from "../components/ui/checkbox"
import { Input } from "../components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
import { Search, Filter, Download, X, ExternalLink } from "lucide-react"
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
import { useRouter } from "next/navigation";
import { flushSync } from "react-dom";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL_P2!
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL!

export function DataEnhancement() {
  const [mergedView, setMergedView] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const { leads, setLeads } = useLeads()
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null)
  // Get the original search criteria from URL parameters
  const getSearchCriteria = () => {
    if (typeof window === 'undefined') return { industry: '', location: '' };

    const params = new URLSearchParams(window.location.search);
    const industry = params.get('industry') || '';
    const location = params.get('location') || '';

    return {
      industry: industry,
      location: location
    };
  };

  const searchCriteria = getSearchCriteria();

  // Add sorting state
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'ascending' | 'descending';
  } | null>(null);

  // Cleanup function for progress simulation

  const router = useRouter();

  const handleBack = () => {
    sessionStorage.removeItem("leads");
    sessionStorage.removeItem("enrichedResults");
    router.push("/scraper"); // 🔁 adjust the path if needed
  };

  useEffect(() => {

    // Cleanup: clear progress simulation
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);




  // Function to stop progress simulation
  const stopProgressSimulation = (finalValue = 100) => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
    setProgress(finalValue);
  };

  const normalizeLeadValue = (val: any) => {
    const v = (val || "").toString().trim().toLowerCase()
    return v === "" || v === "na" || v === "n/a" || v === "none" || v === "not" || v === "found" || v === "not found"
      ? "N/A"
      : val
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

  const normalizedLeads = leads.map((lead) => ({
    ...lead,
    lead_id: lead.lead_id,
    company: normalizeLeadValue(lead.company),
    website: normalizeLeadValue(lead.website),
    industry: normalizeLeadValue(lead.industry),
    street: normalizeLeadValue(lead.street),
    city: normalizeLeadValue(lead.city),
    state: normalizeLeadValue(lead.state),
    bbb_rating: normalizeLeadValue(lead.bbb_rating),
    business_phone: normalizeLeadValue(lead.business_phone),
  }))

  // 1. Declare state variables first
  const [dbEnrichedCompanies, setDbEnrichedCompanies] = useState<EnrichedCompany[]>([]);
  const [scrapedEnrichedCompanies, setScrapedEnrichedCompanies] = useState<EnrichedCompany[]>([]);
  const [selectedCompanies, setSelectedCompanies] = useState<number[]>([]);

  // 2. Restore from sessionStorage on mount
  useEffect(() => {
    const saved = sessionStorage.getItem("enrichedResults");
    if (!saved) return;

    try {
      const all = JSON.parse(saved) as EnrichedCompany[];
      // split them back out by sourceType
      setDbEnrichedCompanies(
        all.filter(c => c.sourceType === "database")
      );
      setScrapedEnrichedCompanies(
        all.filter(c => c.sourceType === "scraped")
      );
      setShowResults(true);
    } catch (err) {
      console.error("Failed to restore enriched results:", err);
    }
  }, []);


  // 3. Persist to sessionStorage on updates
  useEffect(() => {
    // 1️⃣ build in the order: database results first, then freshly scraped
    const combined = [...dbEnrichedCompanies, ...scrapedEnrichedCompanies];

    // 2️⃣ persist into sessionStorage
    if (combined.length > 0) {
      sessionStorage.setItem("enrichedResults", JSON.stringify(combined));
    } else {
      sessionStorage.removeItem("enrichedResults");
    }

    // 3️⃣ sync through context so EnrichmentProvider has the up-to-date combined list
    setEnrichedCompanies(combined);

  }, [dbEnrichedCompanies, scrapedEnrichedCompanies]);

  // const { leads, setLeads } = useLeads(); // from LeadsContext or LeadsProvider

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
  }, []);


  const [selectAll, setSelectAll] = useState(false)
  const [industryFilter, setIndustryFilter] = useState("")
  const [cityFilter, setCityFilter] = useState("")
  const [stateFilter, setStateFilter] = useState("")
  const [bbbRatingFilter, setBbbRatingFilter] = useState("")
  const [showFilters, setShowFilters] = useState(false)



  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(25)

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [industryFilter, cityFilter, stateFilter, bbbRatingFilter]);


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
  const filteredLeads = normalizedLeads.filter((company) => {
    return (
      company.industry.toLowerCase().includes(industryFilter.toLowerCase()) &&
      company.city.toLowerCase().includes(cityFilter.toLowerCase()) &&
      company.state.toLowerCase().includes(stateFilter.toLowerCase()) &&
      company.bbb_rating.toLowerCase().includes(bbbRatingFilter.toLowerCase())
    )
  })


  // Function to handle sorting
  const requestSort = (key: string) => {
    let direction: 'ascending' | 'descending' = 'ascending';

    // If already sorting by this key, toggle direction
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }

    setSortConfig({ key, direction });
  };

  // Function to sort data with N/A values at the bottom
  const getSortedData = (data: any[]) => {
    // If no sort config, return original data
    if (!sortConfig) return data;

    return [...data].sort((a, b) => {
      // Get values for the sort key, treating null/undefined as empty string
      const aValue = (a[sortConfig.key] ?? "").toString().toLowerCase();
      const bValue = (b[sortConfig.key] ?? "").toString().toLowerCase();

      // Special handling for N/A values - always put them at the bottom
      const aIsNA = aValue === "n/a" || aValue === "na" || aValue === "";
      const bIsNA = bValue === "n/a" || bValue === "na" || bValue === "";

      // If one is N/A and the other isn't, the N/A value should be last
      if (aIsNA && !bIsNA) return 1;
      if (!aIsNA && bIsNA) return -1;

      // If both are N/A or both are not N/A, do normal comparison
      if (sortConfig.direction === 'ascending') {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });
  };

  // Apply sorting to the filtered data
  const sortedFilteredLeads = getSortedData(filteredLeads);

  // Use the sorted data for pagination
  const totalPages = Math.ceil(sortedFilteredLeads.length / itemsPerPage)
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = sortedFilteredLeads.slice(indexOfFirstItem, indexOfLastItem)

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


  //   const companies = [
  //   {
  //     id: "1",
  //     name: "HubSpot",
  //     website: "hubspot.com",
  //     industry: "CRM Software",
  //     street: "25 First Street",
  //     city: "Cambridge",
  //     state: "MA",
  //     phone: "(888) 482-7768",
  //     bbbRating: "A+",
  //   }
  // ]
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedCompanies([])
    } else {
      setSelectedCompanies(normalizedLeads.map((company) => company.id))
    }
    setSelectAll(!selectAll)
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

  const normalizeWebsite = (url: string) => {
    return url.replace(/^https?:\/\//, "").replace(/\/$/, "").toLowerCase()
  }

  const getSource = (growjo: any, apollo: any, person: any) => {
    const g = growjo && Object.keys(growjo).some((k) => growjo[k])
    const a = apollo && Object.keys(apollo).some((k) => apollo[k])
    const p = person && Object.keys(person).some((k) => person[k])
    if (g && a) return "Growjo + Apollo"
    if (g) return "Growjo"
    if (a) return "Apollo"
    return "N/A"
  }

  const buildEnrichedCompany = (company: any, growjo: any, apollo: any, person: any) => {
    const cleanVal = (val: any) => {
      const s = (val || "").toString().trim().toLowerCase();

      const isObscuredEmail = /^[a-z\*]+@[^ ]+\.[a-z]+$/.test(s) && s.includes("*");

      return (
        ["", "na", "n/a", "none", "not", "found", "not found", "n.a.", "email_not_unlocked@domain.com"].includes(s) ||
        isObscuredEmail
      )
        ? null
        : val.toString().trim();
    };


    const preferValue = (g: any, a: any, fallback: any = "") => cleanVal(g) ?? cleanVal(a) ?? fallback

    const splitGrowjoName = (() => {
      const raw = growjo.decider_name || ""
      const clean = raw.toString().trim().toLowerCase()
      if (["", "na", "n/a", "none", "not", "found", "not found"].includes(clean)) return []
      return raw.split(" ")
    })()
    const growjoFirstName = splitGrowjoName[0] || ""
    const growjoLastName = splitGrowjoName.slice(1).join(" ") || ""

    const decider = {
      firstName: preferValue(growjoFirstName, person.first_name),
      lastName: preferValue(growjoLastName, person.last_name),
      email: preferValue(growjo.decider_email, person.email),
      phone: preferValue(growjo.decider_phone, person.phone_number),
      linkedin: preferValue(growjo.decider_linkedin, person.linkedin_url),
      title: preferValue(growjo.decider_title, person.title),
    }

    return {
      company: preferValue(growjo.company_name, company.company),
      website: preferValue(growjo.company_website, apollo.website_url, company.website),
      industry: preferValue(growjo.industry, apollo.industry, company.industry),
      productCategory: preferValue(
        growjo.interests,
        Array.isArray(apollo.keywords) ? apollo.keywords.join(", ") : apollo.keywords
      ),
      businessType: preferValue("", apollo.business_type),
      employees: preferValue(growjo.employee_count, apollo.employee_count),
      revenue: preferValue(growjo.revenue, apollo.annual_revenue_printed),
      yearFounded: preferValue("", apollo.founded_year),
      city: preferValue(growjo.location?.split(", ")[0], company.city),
      state: preferValue(growjo.location?.split(", ")[1], company.state),
      bbbRating: company.bbb_rating,
      street: company.street || "",
      companyPhone: company.business_phone,
      companyLinkedin: preferValue("", apollo.linkedin_url),
      ownerFirstName: decider.firstName,
      ownerLastName: decider.lastName,
      ownerTitle: decider.title,
      ownerEmail: decider.email,
      ownerPhoneNumber: decider.phone,
      ownerLinkedin: decider.linkedin,
      source: getSource(growjo, apollo, person),
    }

  }
  const toCamelCase = (lead: any): EnrichedCompany => ({
    id: lead.id || `${lead.company}-${Math.random()}`,
    lead_id: lead.lead_id,
    company: lead.company,
    website: lead.website,
    industry: lead.industry,
    productCategory: lead.product_category,
    businessType: lead.business_type,
    employees: lead.employees,
    revenue: lead.revenue,
    yearFounded: lead.year_founded?.toString() || "N/A",
    bbbRating: lead.bbb_rating,
    street: lead.street,
    city: lead.city,
    state: lead.state,
    companyPhone: lead.company_phone,
    companyLinkedin: lead.company_linkedin,
    ownerFirstName: lead.owner_first_name,
    ownerLastName: lead.owner_last_name,
    ownerTitle: lead.owner_title,
    ownerEmail: lead.owner_email,
    ownerPhoneNumber: lead.owner_phone_number,
    ownerLinkedin: lead.owner_linkedin,
    source: lead.source,
    sourceType: lead.source_type,
  });
  const [dbOnlyMode, setDbOnlyMode] = useState(true);
  const [fromDatabaseLeads, setFromDatabaseLeads] = useState<string[]>([]); // lowercase names
  const { enrichedCompanies, setEnrichedCompanies } = useEnrichment();
  
  const handleStartEnrichment = async (
    forceScrape = false,
    overrideCompanies: any[] | null = null
  ) => {
    const user = JSON.parse(sessionStorage.getItem("user") || "{}");
    const user_id = user.id || "";
    setLoading(true);

    if (!forceScrape) {
      setDbEnrichedCompanies([]);
      setScrapedEnrichedCompanies([]);
    }

    try {
      const selected = overrideCompanies ?? normalizedLeads.filter(c =>
        selectedCompanies.includes(c.id)
      );
      const lead_ids = selected.map(c => c.lead_id).filter(Boolean);
      const queryString = lead_ids.join(",");

      // ✅ Step 1: Check credits
      try {
        const { data: subscriptionInfo } = await axios.get(`${DATABASE_URL}/user/subscription_info`, {
          withCredentials: true
        });

        const availableCredits = subscriptionInfo?.subscription?.credits_remaining ?? 0;
        const requiredCredits = selected.length;

        if (availableCredits < requiredCredits) {
          alert("❌ You don't have enough credits to enrich these companies. Please upgrade or deselect some leads.");
          setLoading(false);
          return;
        }
      } catch (checkErr) {
        console.error("❌ Failed to verify subscription:", checkErr);
        alert("Failed to verify your subscription. Please try again later.");
        setLoading(false);
        return;
      }

      let existingNames = new Set<string>();
      let dbLeads: any[] = [];

      if (queryString) {
        const { data: dbRes } = await axios.get(
          `${DATABASE_URL}/leads/multiple?lead_ids=${queryString}`,
          { headers: { "Content-Type": "application/json" } }
        );
        dbLeads = dbRes.results || [];
        existingNames = new Set(dbLeads.map((l: any) => l.company?.toLowerCase()));
        setFromDatabaseLeads(Array.from(existingNames));
      }

      // ✅ Step 2: Deduct credits for ALL selected leads
      for (const lead of selected) {
        const lead_id = lead.lead_id;
        if (!lead_id) continue;
        try {
          await axios.post(`${DATABASE_URL}/user/deduct_credit/${lead_id}`, {}, {
            withCredentials: true
          });
        } catch (deductErr) {
          console.error(`❌ Credit deduction failed for lead ${lead_id}`, deductErr);
          continue;
        }
      }

      // ✅ Step 3: Show DB leads (if not force or override)
      if (!forceScrape && !overrideCompanies) {
        const tealRows = dbLeads.map(lead =>
          toCamelCase({ ...lead, source_type: "database" })
        );
        setDbEnrichedCompanies(tealRows);
        setShowResults(true);

        const payload = dbLeads
          .filter(l => !!l.lead_id)
          .map(l => ({ ...l, user_id }));

        if (payload.length) {
          try {
            await axios.post(
              `${DATABASE_URL}/upload_leads`,
              JSON.stringify(payload),
              { headers: { "Content-Type": "application/json" } }
            );

            for (const lead of payload) {
              await axios.post(
                `${DATABASE_URL}/leads/drafts`,
                {
                  lead_id: lead.lead_id,
                  draft_data: lead,
                  change_summary: "Restored from DB"
                },
                {
                  headers: { "Content-Type": "application/json" },
                  withCredentials: true
                }
              );
            }
          } catch (err) {
            console.error("❌ Upload or draft creation for DB leads failed:", err);
          }
        }
      }

      // ✅ Step 4: Proceed with scraping only for those not in DB
      const toScrape = forceScrape
        ? selected
        : selected.filter(c => !existingNames.has(c.company.toLowerCase()));

      for (const company of toScrape) {
        try {
          const lead_id = company.lead_id || "";

          const headers = { headers: { "Content-Type": "application/json" } };

          const growjo = (
            await axios.post(
              `${BACKEND_URL}/scrape-growjo-single`,
              { company: company.company },
              headers
            )
          ).data;

          const domain = normalizeWebsite(growjo.company_website || company.website);
          const [apolloRes, personRes] = await Promise.all([
            axios.post(`${BACKEND_URL}/apollo-scrape-single`, { domain }, headers),
            axios.post(`${BACKEND_URL}/find-best-person-single`, { domain }, headers),
          ]);
          const apollo = apolloRes.data || {};
          const person = personRes.data || {};

          const entry = buildEnrichedCompany(company, growjo, apollo, person);

          const normalizeValue = (v: any) => {
            const s = (v ?? "").toString().trim().toLowerCase();
            const isBad =
              ["", "na", "n/a", "none", "not", "found", "not found"].includes(s) ||
              (/^[a-z\*]+@[^ ]+\.[a-z]+$/.test(s) && s.includes("*"));
            return isBad ? "N/A" : v.toString().trim();
          };

          const validLead = {
            user_id,
            lead_id,
            company: normalizeValue(entry.company),
            website: normalizeValue(entry.website),
            industry: normalizeValue(entry.industry),
            product_category: normalizeValue(entry.productCategory),
            business_type: normalizeValue(entry.businessType),
            employees: typeof entry.employees === "number" ? entry.employees : parseInt(entry.employees) || 0,
            revenue: normalizeValue(entry.revenue),
            year_founded: typeof entry.yearFounded === "number" ? entry.yearFounded : parseInt(entry.yearFounded) || 0,
            bbb_rating: normalizeValue(entry.bbbRating),
            street: normalizeValue(entry.street),
            city: normalizeValue(entry.city),
            state: normalizeValue(entry.state),
            company_phone: normalizeValue(entry.companyPhone),
            company_linkedin: normalizeValue(entry.companyLinkedin),
            owner_first_name: normalizeValue(entry.ownerFirstName),
            owner_last_name: normalizeValue(entry.ownerLastName),
            owner_title: normalizeValue(entry.ownerTitle),
            owner_linkedin: normalizeValue(entry.ownerLinkedin),
            owner_phone_number: normalizeValue(entry.ownerPhoneNumber),
            owner_email: normalizeValue(entry.ownerEmail),
            source: normalizeValue(entry.source),
          };

          try {
            await axios.post(
              `${DATABASE_URL}/upload_leads`,
              JSON.stringify([validLead]),
              { headers: { "Content-Type": "application/json" } }
            );
          } catch (uploadErr) {
            console.error("❌ Failed to upload lead:", validLead, uploadErr);
          }

          try {
            await axios.post(
              `${DATABASE_URL}/leads/drafts`,
              {
                lead_id: validLead.lead_id,
                draft_data: validLead,
                change_summary: "Initial enrichment draft",
              },
              {
                headers: { "Content-Type": "application/json" },
                withCredentials: true,
              }
            );
          } catch (draftErr: any) {
            console.error(
              "❌ Failed to create draft:",
              draftErr.response?.data || draftErr.message
            );
          }

          const yellowRow = toCamelCase({
            ...validLead,
            source_type: "scraped",
          });

          setScrapedEnrichedCompanies((prev) => [...prev, yellowRow]);
          await new Promise((r) => setTimeout(r, 150));
        } catch (err) {
          console.error(`❌ Failed enriching ${company.company}`, err);
        }
      }

      if (forceScrape) {
        setDbEnrichedCompanies([]);
      }

      setShowResults(true);
    } catch (err) {
      console.error("Enrichment failed:", err);
      stopProgressSimulation(0);
    } finally {
      stopProgressSimulation(100);
      setLoading(false);
    }
  };
  
  










  return (
    
    <div className="space-y-6">
      <Button
        onClick={handleBack}
        className="text-sm text-blue-600 hover:underline mb-4"
      >
        Back
      </Button>
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
                  Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, sortedFilteredLeads.length)} of {sortedFilteredLeads.length} results for {searchCriteria.industry} in {searchCriteria.location}
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

            <div className="w-full overflow-x-auto rounded-md border">
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
                        currentItems.map((company) => (
                          <TableRow key={company.id ?? `${company.company}-${Math.random()}`}>
                            <TableCell>
                              <Checkbox
                                checked={selectedCompanies.includes(company.id)}
                                onCheckedChange={() => handleSelectCompany(company.id)}
                                aria-label={`Select ${company.company}`}
                              />
                            </TableCell>
                            <TableCell className="font-medium">{company.company}</TableCell>
                            <TableCell>{company.industry}</TableCell>
                            <TableCell>{company.street}</TableCell>
                            <TableCell>{company.city}</TableCell>
                            <TableCell>{company.state}</TableCell>
                            <TableCell>{company.bbb_rating}</TableCell>
                            <TableCell>{company.business_phone}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                {company.website ? cleanUrlForDisplay(company.website) : "N/A"}
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

                      {/* {loading && (
                      <TableRow key="loading-row">
                        <TableCell colSpan={9} className="text-center py-8">
                          <div className="flex justify-center">
                            <Loader />
                          </div>
                          <div className="mt-4 text-sm text-muted-foreground">Scraping and enriching data… please wait</div>
                        </TableCell>
                      </TableRow>
                    )} */}

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
                  onClick={() => {
                    setMergedView(false);
                    handleStartEnrichment(false);
                  }}
                  disabled={selectedCompanies.length === 0 || loading}
                >
                  {loading ? "Enriching..." : "Start Enrichment"}
                </Button>
              </div>
            </div>

            {/* Results section */}
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex flex-col items-center py-8">
          <Loader />
          <p className="mt-4 text-sm text-muted-foreground">
            Scraping and enriching data… please wait
          </p>
        </div>
      ) : !mergedView ? (
        <div className="mt-6 space-y-8">
          {/* ── DATABASE RESULTS ── */}
          {dbEnrichedCompanies.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-2">Fetched from Database</h2>
              <EnrichmentResults
                enrichedCompanies={dbEnrichedCompanies}
                rowClassName={() => "bg-teal-50"}
              />

              {/* … re-enrich button … */}
              {fromDatabaseLeads.length > 0 && (
                <div className="mt-3 flex justify-end">
                  <Button
                    variant="destructive"
                    onClick={async () => {
                      // switch off merged view
                      setMergedView(false);
                      // re-select only the DB companies
                      const toReselect = normalizedLeads.filter(c =>
                        fromDatabaseLeads.includes(c.company.toLowerCase())
                      );
                      setSelectedCompanies(toReselect.map(c => c.id));
                      await handleStartEnrichment(true, toReselect);
                    }}
                  >
                    Re-enrich those companies
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* ── SCRAPED RESULTS ── */}
          {scrapedEnrichedCompanies.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-2">Freshly Scraped</h2>
              <EnrichmentResults
                enrichedCompanies={scrapedEnrichedCompanies}
                rowClassName={() => "bg-yellow-50"}
              />
            </div>
          )}

          {/* switch to merged only when user explicitly clicks */}
          <div className="flex justify-center">
            <Button onClick={() => setMergedView(true)}>
              Show Combined Table
            </Button>
          </div>
        </div>
      ) : (
        /* ── MERGED VIEW ── */
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">All Enriched Results</h2>
          <EnrichmentResults
            enrichedCompanies={[
              ...dbEnrichedCompanies,
              ...scrapedEnrichedCompanies,
            ]}
          />
        </div>
      )}
      <div className="flex justify-end mb-4">
        <Button
          onClick={() => {
            sessionStorage.removeItem("leads");
            sessionStorage.removeItem("enrichedResults");
            router.push("/dashboard");
          }}
        >
          Finish and Go Back to Home
        </Button>
      </div>
    </div>
  )
}