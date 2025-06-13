"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
// import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip as RechartTooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line,
  Legend,
  ResponsiveContainer,
} from "recharts";

import { Header } from "@/components/header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import {
  Search,
  Download,
  ArrowLeft,
  Filter,
  X,
  ExternalLink,
} from "lucide-react";
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
import axios from "axios";
import useEmailVerificationGuard from "@/hooks/useEmailVerificationGuard";
import Notif from "@/components/ui/notif";
import Popup from "@/components/ui/popup";
import { SortDropdown } from "@/components/ui/sort-dropdown";

import { redirect } from "next/navigation";
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL;
const DATABASE_URL_NOAPI = DATABASE_URL?.replace(/\/api\/?$/, "");
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL_P2;
// export default function Home() {
//   redirect('/auth');
// }
export default function Home() {
  const { showPopup, handleClose } = useEmailVerificationGuard();
  const user =
    typeof window !== "undefined"
      ? JSON.parse(sessionStorage.getItem("user") || "{}")
      : {};
  const userTier = user?.tier || "free";
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
  const [showCookieWarning, setShowCookieWarning] = useState(false);
  const [hasSorted, setHasSorted] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);


  const router = useRouter();
  const handleSave = async (index) => {
    // Helper to convert camelCase keys into snake_case
    const toSnake = (str) => str.replace(/([A-Z])/g, "_$1").toLowerCase();

    // Given a plain object with camelCase keys, return a new object
    // whose keys are all snake_case.
    const normalizeKeys = (obj) => {
      const result = {};
      for (const [k, v] of Object.entries(obj)) {
        result[toSnake(k)] = v;
      }
      return result;
    };

    try {
      const lead = editedRows[index];
      const leadId = lead.lead_id || lead.id;
      const originalDraftId = lead.draft_id;

      // Normalize the edited fields so that every key is snake_case:
      const normalizedLead = normalizeKeys(lead);
      // Always include user_id in snake_case:
      normalizedLead.user_id = user.id;

      // 1) Always call POST first
      const postResponse = await axios.post(
        `${DATABASE_URL_NOAPI}/leads/${leadId}/edit`,
        normalizedLead,
        { withCredentials: true }
      );
      showNotification("Draft POST called successfully", "success");

      // If the POST returned a new draft_id, use it; otherwise keep originalDraftId
      const newDraftId = postResponse.data?.draft?.draft_id;
      const actualDraftId = newDraftId || originalDraftId;

      // 2) Now call PUT to update that draft
      const payload = {
        draft_data: normalizedLead,
        change_summary: "Updated from homepage",
        phase: "draft",
        status: "pending",
      };

      await axios.put(
        `${DATABASE_URL}/leads/drafts/${actualDraftId}`,
        payload,
        { withCredentials: true }
      );
      showNotification("Draft updated successfully", "success");

      // Reflect changes in local state (ensure draft_id is set)
      const updated = [...scrapingHistory];
      updated[index] = {
        ...lead,
        draft_id: actualDraftId,
        updated: new Date().toLocaleString(),
      };
      setScrapingHistory(updated);
      setEditedRows(updated);
      setEditingRowIndex(null);
    } catch (err) {
      console.error("❌ Error saving row:", err);
      showNotification("Failed to save row.", "error");
    }
  };

  const handleDiscard = (index) => {
    const resetRow = scrapingHistory[index];
    const updated = [...editedRows];
    updated[index] = resetRow;
    setEditedRows(updated);
    setEditingRowIndex(null);
  };

  const handleFieldChange = (index, field, value) => {
    const updated = [...editedRows];
    updated[index] = {
      ...updated[index],
      [field]: value,
    };
    setEditedRows(updated);
  };

  const [notif, setNotif] = useState({
    show: false,
    message: "",
    type: "success",
  });
  const showNotification = (message, type = "success") => {
    setNotif({ show: true, message, type });

    // Automatically hide after X seconds (let Notif handle it visually)
    // Optional if Notif itself auto-hides — but helpful as backup
    setTimeout(() => {
      setNotif((prev) => ({ ...prev, show: false }));
    }, 3500);
  };

  const [editingRowIndex, setEditingRowIndex] = useState(null);

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

  //

  const ExpandableCell = ({ text }) => {
    const [expanded, setExpanded] = useState(false);
    const isLong = text.length > 100;

    if (!isLong) return <span>{text}</span>;

    return (
      <div className="whitespace-pre-wrap">
        <span>{expanded ? text : text.slice(0, 30) + "... "}</span>
        <button
          className="text-blue-500 hover:underline text-xs ml-1"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      </div>
    );
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
      const requiredCredits = currentItems.length;

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

      handleExportCSV(currentItems, "enriched_results.csv");
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

  const [scrapingHistory, setScrapingHistory] = useState([]);

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
      ...currentItems.map((row) =>
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

  const [editedRows, setEditedRows] = useState([...scrapingHistory]);
  // duplicate of original data
  // Example pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);

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

  // Derive indexes for slicing the filtered data
  const totalPages = Math.ceil(filteredScrapingHistory.length / itemsPerPage);
  const indexOfFirstItem = (currentPage - 1) * itemsPerPage;
  const indexOfLastItem = currentPage * itemsPerPage;
  const currentItems = filteredScrapingHistory.slice(
    indexOfFirstItem,
    indexOfLastItem
  );

  const [selectedCompanies, setSelectedCompanies] = useState([]);

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
    const updatedSelection = selectedCompanies.includes(id)
      ? selectedCompanies.filter((cid) => cid !== id)
      : [...selectedCompanies, id];

    setSelectedCompanies(updatedSelection);

    const visibleIds = scrapingHistory
      .slice(indexOfFirstItem, indexOfLastItem)
      .map((entry) => entry.id);

    setSelectAll(visibleIds.every((id) => updatedSelection.includes(id)));
  };

  // const filteredCompanies = scrapingHistory.slice(
  //   indexOfFirstItem,
  //   indexOfLastItem
  // );

  // Pie Chart: Industry Distribution
  const industryData = Object.entries(
    scrapingHistory.reduce((acc, curr) => {
      const industry = curr.industry || "Unknown";
      acc[industry] = (acc[industry] || 0) + 1;
      return acc;
    }, {})
  ).map(([name, value]) => ({ name, value }));

  // Bar Chart: Companies per City
  const cityData = Object.entries(
    scrapingHistory.reduce((acc, curr) => {
      const city = curr.city || "Unknown";
      acc[city] = (acc[city] || 0) + 1;
      return acc;
    }, {})
  ).map(([name, count]) => ({ name, count }));

  // Line Chart: Weekly Enrichment Trends
  const dateCounts = scrapingHistory.reduce((acc, curr) => {
    const rawDate = curr.created || curr.updated || new Date().toISOString();
    const date =
      rawDate && !isNaN(Date.parse(rawDate))
        ? new Date(rawDate).toISOString().split("T")[0]
        : "";
    acc[date] = (acc[date] || 0) + 1;
    return acc;
  }, {});

  const trendData = Object.entries(dateCounts)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([date, count]) => ({ date, count }));

  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // At the top of Home(), alongside your other handlers:
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
    setEditedRows(sorted); // keep the “edited” mirror in sync
    setCurrentPage(1); // reset pagination to page 1
  };

  useEffect(() => {
    const verifyAndFetchLeads = async () => {
      try {
        setIsCheckingAuth(true);

        // 1. First verify authentication
        const authRes = await fetch(`${DATABASE_URL}/ping-auth`, {
          method: "GET",
          credentials: "include",
        });

        if (!authRes.ok) {
          console.warn("⚠️ Auth check failed, redirecting to login");
          router.push("/auth");
          return;
        }

        console.log("✅ Authentication verified");

        // 2. Fetch drafts data
        const draftsRes = await fetch(`${DATABASE_URL}/leads/drafts`, {
          // Changed endpoint
          method: "GET",
          credentials: "include",
        });

        // Handle non-OK responses
        if (!draftsRes.ok) {
          const errorText = await draftsRes.text();
          console.warn("⚠️ Drafts fetch failed:", {
            status: draftsRes.status,
            statusText: draftsRes.statusText,
            response: errorText,
          });
          return;
        }

        // Safely parse JSON
        let data = [];
        try {
          const responseText = await draftsRes.text();
          data = responseText ? JSON.parse(responseText) : [];
        } catch (parseError) {
          console.error("🚨 Failed to parse drafts response:", parseError);
          return;
        }

        // Transform data with proper error handling
        const parsed = (Array.isArray(data) ? data : []).map((entry) => {
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
        setEditedRows(parsed);
      } catch (error) {
        console.error("🚨 Error in verifyAndFetchLeads:", {
          error: error.message,
          stack: error.stack,
        });
        router.push("/auth");
      } finally {
        setIsCheckingAuth(false);
      }
    };

    verifyAndFetchLeads();
  }, [router]); // Added router to dependency array

  useEffect(() => {
    if (!hasSorted && scrapingHistory.length > 0) {
      handleSortBy("filled", "most");
      setHasSorted(true);
    }
  }, [scrapingHistory, hasSorted]);

  useEffect(() => {
    let isCancelled = false;

    const ensureGrowjoIsRunning = async () => {
      try {
        // 1) Check whether GrowjoScraper is already initialized on the backend
        const statusRes = await axios.get(
          `${BACKEND_URL}/is-growjo-scraper`,
          {}
        );
        if (isCancelled) return;

        const alreadyInitialized = statusRes.data?.initialized;
        if (alreadyInitialized) {
          console.log("🔄 GrowjoScraper already running; skipping init.");
          return;
        }

        // 2) If not initialized, call the init endpoint
        const initRes = await axios.post(
          `${BACKEND_URL}/init-growjo-scraper`,
          {}
        );
        console.log("✅ GrowjoScraper initialized:", initRes.data);
      } catch (err) {
        console.error("❌ Error checking or initializing GrowjoScraper:", err);
      }
    };

    ensureGrowjoIsRunning();

    // We do NOT close here automatically; cleanup is done explicitly on logout or navigation.
    return () => {
      isCancelled = true;
    };
  }, []);

  const [subscriptionInfo, setSubscriptionInfo] = useState(null);

  useEffect(() => {
    const fetchSubscriptionInfo = async () => {
      try {
        const res = await axios.get(`${DATABASE_URL}/user/subscription_info`, {
          withCredentials: true,
          validateStatus: () => true, // let us handle non-2xx responses
        });

        if (
          res.status === 302 ||
          res.status === 401 ||
          res.request?.responseURL?.includes("/auth")
        ) {
          console.warn("⚠️ Blocked by third-party cookies or session timeout");
          setShowCookieWarning(true); // trigger the popup
          return;
        }

        setSubscriptionInfo(res.data);
      } catch (err) {
        console.error("Error fetching subscription info:", err);
        showNotification(
          "Failed to verify your subscription. Please try again later.",
          "error"
        );
      }
    };

    fetchSubscriptionInfo();
  }, []);
  

  const COLORS = [
    "#1EBE8F", // More vibrant Green-Teal
    "#129C91", // Cyan shift, more pop
    "#3BA2D0", // Lighter Cyan-Blue
    "#E67E22", // Orange
    "#FFF4A4", // More vibrant Deep Blue
    "#6175FF", // Strong Violet-Blue
  ];

  return isCheckingAuth ? (
    <div className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm z-50 flex items-center justify-center pointer-events-none">
      <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-yellow-400"></div>
    </div>
  ) : (
    <>
      {/* Email-not-verified popup */}
      <Popup show={showPopup} onClose={handleClose}>
        <div className="text-center flex flex-col items-center justify-center">
          <h2 className="text-lg font-semibold">Account Not Verified</h2>
          <p className="mt-2">
            Your account hasn’t been verified yet. Please check your email for
            the verification link.
          </p>

          {/* Resend Verification Button */}
          <button
            className="mt-4 px-4 py-2 rounded text-white"
            style={{ backgroundColor: "#4a90e2" }}
            onClick={async () => {
              try {
                await fetch(`${DATABASE_URL}/auth/send-verification`, {
                  method: "POST",
                  credentials: "include",
                });
                showNotification(
                  "Verification email resent. Please check your inbox.",
                  "info"
                );
              } catch (err) {
                console.error("Failed to resend verification email:", err);
                showNotification(
                  "Failed to resend verification email.",
                  "error"
                );
              }
            }}
          >
            Resend Verification Link
          </button>

          {/* OK Button */}
          <button
            className="mt-2 px-4 py-2 rounded text-white"
            style={{ backgroundColor: "#7bc3a4" }}
            onClick={handleClose}
          >
            OK
          </button>
        </div>
      </Popup>

      {/* popup for subscription info 302 */}
      <Popup
        show={showCookieWarning}
        onClose={() => {
          setShowCookieWarning(false);
          router.push("/auth");
        }}
        title="Third-Party Cookies Blocked"
        description="Your browser is blocking cookies required to stay logged in. Please enable third-party cookies or allow all cookies."
        confirmText="OK"
      />

      {/* Main app content */}
      <Header />
      <main className="px-20 py-16 space-y-10">
        <div className="text-2xl font-semibold text-foreground text-white">
          Hi, {user.username || "there"}! Are you ready to scrape?
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[
            {
              label: "Total Leads Scraped",
              value: scrapingHistory.length.toLocaleString(),
            },
            {
              label: "Token Usage",
              value:
                subscriptionInfo?.plan?.initial_credits !== undefined &&
                subscriptionInfo?.subscription?.credits_remaining !== undefined
                  ? `${
                      subscriptionInfo.plan.initial_credits -
                      subscriptionInfo.subscription.credits_remaining
                    } / ${subscriptionInfo.plan.initial_credits}`
                  : "N/A",
              change:
                subscriptionInfo?.plan?.initial_credits !== undefined &&
                subscriptionInfo?.subscription?.credits_remaining !== undefined
                  ? `${(
                      ((subscriptionInfo.plan.initial_credits -
                        subscriptionInfo.subscription.credits_remaining) /
                        subscriptionInfo.plan.initial_credits) *
                      100
                    ).toFixed(0)}%`
                  : "0%",
              comparison: "used this month",
            },
            {
              label: "Subscription",
              value: subscriptionInfo?.subscription?.plan_name
                ? `${subscriptionInfo.subscription.plan_name} Plan`
                : "N/A",
              change: "Active",
              comparison: subscriptionInfo?.subscription
                ?.plan_expiration_timestamp
                ? `until ${new Date(
                    subscriptionInfo.subscription.plan_expiration_timestamp
                  ).toLocaleDateString()}`
                : "Expiration unknown",
              action: {
                label: "Upgrade",
                onClick: () => {
                  router.push("/subscription");
                },
              },
            },
          ].map((stat, index) => (
            <Card
              key={index}
              className="relative rounded-2xl border shadow-sm px-6 py-5 flex flex-col justify-between min-h-[12rem]"
            >
              <CardHeader className="pb-2 flex flex-wrap justify-between items-start gap-4">
                <div className="flex-1 min-w-0">
                  <CardDescription className="text-base text-muted-foreground mb-1">
                    {stat.label}
                  </CardDescription>
                  <CardTitle className="text-3xl sm:text-4xl font-extrabold text-foreground leading-snug break-words whitespace-normal">
                    {stat.value}
                  </CardTitle>
                </div>

                {stat.label === "Subscription" && stat.action && (
                  <div className="flex flex-col gap-2">
                    {/* Upgrade Button */}
                    <Button
                      size="sm"
                      className="text-sm px-4 py-1.5 font-semibold w-full"
                      onClick={stat.action.onClick}
                    >
                      {stat.action.label}
                    </Button>

                    {/* Outreach Appointment Button — shown only if allowed */}
                    {subscriptionInfo?.subscription?.is_call_outreach_cust &&
                      !subscriptionInfo?.subscription
                        ?.is_scheduled_for_cancellation &&
                      subscriptionInfo?.subscription?.appointment_used ===
                        false && (
                        <Button
                          size="sm"
                          className="text-sm px-4 py-1.5 font-semibold bg-[#4CAF50] hover:bg-[#3b9441] text-white w-full"
                          onClick={() => {
                            window.open(
                              "https://calendar.app.google/45wvqajrQqNCpdPg6",
                              "_blank"
                            );
                            setShowConfirmModal(true);
                          }}
                        >
                          Outreach Appointment
                        </Button>
                      )}
                  </div>
                )}
              </CardHeader>

              <CardContent className="pt-0 text-[15px] text-blue-500 font-medium">
                <span>{stat.change}</span>{" "}
                <span className="text-muted-foreground">{stat.comparison}</span>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pie Chart */}
          <Card className="p-6 rounded-2xl shadow-sm">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={industryData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                >
                  {industryData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      // fill={`hsl(${(index * 60) % 360}, 70%, 50%)`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <RechartTooltip />
              </PieChart>
            </ResponsiveContainer>
            <p className="text-center mt-2 text-sm text-muted-foreground">
              Industry Distribution
            </p>
          </Card>

          {/* Bar Chart */}
          <Card className="p-6 rounded-2xl shadow-sm">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={cityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartTooltip />
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-center mt-2 text-sm text-muted-foreground">
              Companies by City
            </p>
          </Card>

          {/* Line Chart */}
          <Card className="p-6 rounded-2xl shadow-sm">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <XAxis dataKey="date" />
                <YAxis />
                <RechartTooltip />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#8884d8" />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-center mt-2 text-sm text-muted-foreground">
              Weekly Growth Trend
            </p>
          </Card>
        </div>

        {/* History Table */}
        <div className="mt-10">
          {/* 1. Keep the heading here */}
          <h2 className="text-2xl font-semibold text-foreground mb-2">
            Scraping History
          </h2>

          {/* 2. Table container */}
          <div className="w-full overflow-x-auto rounded-md border">
            {/* 3. Toolbar INSIDE the table wrapper, above the table */}
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
                  onClick={() => setShowFilters((f) => !f)}
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
          {/* Scrollable container with a max height */}
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

                  {/* Remaining Headers */}
                  {[
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
                    "Created Date",
                    "Updated",
                    "Actions",
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
                    <TableCell className="sticky left-[3rem] z-10 bg-inherit px-6 py-2 max-w-[240px] align-top  ">
                      {editingRowIndex === i ? (
                        <input
                          type="text"
                          className="w-full bg-transparent border-b border-muted focus:outline-none text-sm"
                          value={editedRows[i]?.company ?? ""}
                          onChange={(e) =>
                            handleFieldChange(i, "company", e.target.value)
                          }
                        />
                      ) : (
                        <ExpandableCell text={row.company || "N/A"} />
                      )}
                    </TableCell>

                    {/* Remaining Cells */}
                    {[
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
                      "created",
                      "updated",
                    ].map((field) => {
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
                        <TableCell
                          key={field}
                          className="px-6 py-2 max-w-[240px] align-top"
                        >
                          {editingRowIndex === i ? (
                            <input
                              type="text"
                              className="w-full bg-transparent border-b border-muted focus:outline-none text-sm"
                              value={editedRows[i]?.[field] ?? ""}
                              onChange={(e) =>
                                handleFieldChange(i, field, e.target.value)
                              }
                            />
                          ) : isUrl ? (
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
                      );
                    })}

                    {/* Action Column */}
                    <TableCell className="px-6 py-2">
                      {editingRowIndex === i ? (
                        <>
                          <span
                            className="text-green-500 hover:underline cursor-pointer mr-2"
                            onClick={() => handleSave(i)}
                          >
                            Save
                          </span>
                          <span
                            className="text-red-500 hover:underline cursor-pointer"
                            onClick={() => handleDiscard(i)}
                          >
                            Discard
                          </span>
                        </>
                      ) : (
                        <span
                          className="text-blue-500 hover:underline cursor-pointer mr-2"
                          onClick={() => setEditingRowIndex(i)}
                        >
                          Edit
                        </span>
                      )}
                    </TableCell>
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
        <div className="flex justify-end mt-3 gap-3">
          <Notif
            show={notif.show}
            message={notif.message}
            type={notif.type}
            onClose={() => setNotif((prev) => ({ ...prev, show: false }))}
          />
        </div>
      </main>
      {showConfirmModal && (
        <Popup show={true} onClose={() => setShowConfirmModal(false)}>
          <div className="text-center">
            <h2 className="text-lg font-semibold mb-2">
              Have you scheduled your appointment?
            </h2>
            <p className="mb-4 text-sm text-muted-foreground">
              You can only do this once, so please confirm.
            </p>
            <div className="flex justify-center gap-4">
              <Button
                variant="outline"
                onClick={() => setShowConfirmModal(false)}
              >
                No
              </Button>
              <Button
                className="bg-green-600 hover:bg-green-700 text-white"
                onClick={async () => {
                  try {
                    const res = await fetch(
                      `${DATABASE_URL}/subscription/confirm_appointment`,
                      {
                        method: "POST",
                        credentials: "include",
                      }
                    );
                    if (res.ok) {
                      setShowConfirmModal(false);
                      showNotification("Appointment confirmed!", "success");
                    } else {
                      showNotification(
                        "Failed to confirm appointment",
                        "error"
                      );
                    }
                  } catch (err) {
                    console.error("Error confirming appointment:", err);
                    showNotification("Unexpected error", "error");
                  }
                }}
              >
                Yes, I Did
              </Button>
            </div>
          </div>
        </Popup>
      )}
    </>
  );
}
