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

import Notif from "@/components/ui/notif";

import { redirect } from "next/navigation";
const DATABASE_URL = process.env.NEXT_PUBLIC_DATABASE_URL;
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL_P2;
// export default function Home() {
//   redirect('/auth');
// }
export default function Home() {
  const user =
    typeof window !== "undefined"
      ? JSON.parse(sessionStorage.getItem("user") || "{}")
      : {};
  const userTier = user?.tier || "free";

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
        `https://data.capraeleadseekers.site/leads/${leadId}/edit`,
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
        `https://data.capraeleadseekers.site/api/leads/drafts/${actualDraftId}`,
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
    // 1) Read the user’s role from session storage
    const stored = sessionStorage.getItem("user");
    const currentUser = stored ? JSON.parse(stored) : {};
    const role = currentUser.role || "";

    // 2) If they’re a developer, bypass all checks and export immediately
    if (role === "developer") {
      handleExportCSV(currentItems, "enriched_results.csv");
      return;
    }

    // 3) Otherwise, do the subscription/credits validation
    try {
      const { data: subscriptionInfo } = await axios.get(
        `${DATABASE_URL}/user/subscription_info`,
        { withCredentials: true }
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
    // 1) Read the user’s role
    const stored = sessionStorage.getItem("user");
    const currentUser = stored ? JSON.parse(stored) : {};
    const role = currentUser.role || "";

    // 2) If developer, bypass the subscription check
    if (role === "developer") {
      setShowFilters((prev) => !prev);
      return;
    }

    // 3) Otherwise do the existing plan‐check logic
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

  useEffect(() => {
    const verifyAndFetchLeads = async () => {
      try {
        const authRes = await fetch(
          "https://data.capraeleadseekers.site/api/ping-auth",
          {
            method: "GET",
            credentials: "include",
          }
        );

        if (!authRes.ok) {
          router.push("/auth");
          return;
        }

        console.log("✅ Logged in");

        const draftsRes = await fetch(
          "https://data.capraeleadseekers.site/api/leads/drafts",
          {
            method: "GET",
            credentials: "include",
          }
        );

        if (!draftsRes.ok) {
          console.warn("⚠️ Could not fetch drafts, status:", draftsRes.status);
          return;
        }

        const data = await draftsRes.json();

        const parsed = (data || []).map((entry) => ({
          id: entry.lead_id || entry.id,
          lead_id: entry.lead_id || entry.id,
          draft_id: entry.draft_id,
          company: entry.draft_data?.company || "N/A",
          website: entry.draft_data?.website || "",
          industry: entry.draft_data?.industry || "",
          productCategory: entry.draft_data?.product_category || "",
          businessType: entry.draft_data?.business_type || "",
          employees: entry.draft_data?.employees || "",
          revenue: entry.draft_data?.revenue || "",
          yearFounded: entry.draft_data?.year_founded?.toString() || "",
          bbbRating: entry.draft_data?.bbb_rating || "",
          street: entry.draft_data?.street || "",
          city: entry.draft_data?.city || "",
          state: entry.draft_data?.state || "",
          companyPhone: entry.draft_data?.company_phone || "",
          companyLinkedin: entry.draft_data?.company_linkedin || "",
          ownerFirstName: entry.draft_data?.owner_first_name || "",
          ownerLastName: entry.draft_data?.owner_last_name || "",
          ownerTitle: entry.draft_data?.owner_title || "",
          ownerLinkedin: entry.draft_data?.owner_linkedin || "",
          ownerPhoneNumber: entry.draft_data?.owner_phone_number || "",
          ownerEmail: entry.draft_data?.owner_email || "",
          source: entry.draft_data?.source || "",
          created: entry.created_at
            ? new Date(entry.created_at).toLocaleString()
            : "N/A",
          updated: entry.updated_at
            ? new Date(entry.updated_at).toLocaleString()
            : "N/A",
          sourceType: "database",
        }));

        setScrapingHistory(parsed);
        setEditedRows(parsed);
      } catch (error) {
        console.error("🚨 Error verifying auth or fetching drafts:", error);
        router.push("/auth");
      } finally {
        setIsCheckingAuth(false);
      }
    };

    verifyAndFetchLeads();
  }, []);

  useEffect(() => {
    let isCancelled = false;

    const ensureGrowjoIsRunning = async () => {
      try {
        // 1) Check whether GrowjoScraper is already initialized on the backend
        const statusRes = await axios.get(`${BACKEND_URL}/is-growjo-scraper`, {
          
        });
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
        });

        setSubscriptionInfo(res.data);
      } catch (err) {
        console.error("Error fetching subscription info:", err);
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
      <Header />
      <main className="px-20 py-16 space-y-10">
        <div className="text-2xl font-semibold text-foreground text-white">
          Hi, {user.username || "there"} 👋 Are you ready to scrape?
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
                link: "/subscription",
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
                  <CardTitle className="text-3xl sm:text-4xl font-extrabold text-foreground leading-snug truncate">
                    {stat.value}
                  </CardTitle>
                </div>

                {stat.label === "Subscription" && stat.action && (
                  <div className="flex-none">
                    <a href={stat.action.link}>
                      <Button
                        size="sm"
                        className="text-sm px-4 py-1.5 font-semibold"
                      >
                        {stat.action.label}
                      </Button>
                    </a>
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
          <div className="flex items-center justify-between mb-4">
            <div className="text-2xl font-semibold text-foreground text-white">
              Scraping History
            </div>
            {/* <button
              onClick={null} // implement this function
              className="bg-[#fad945] text-black font-medium px-6 py-2 rounded hover:bg-[#fff1b2] transition"
            >
              Export CSV
            </button> */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleToggleFiltersWithCheck()}
                className="bg-[#fad945] text-black font-medium px-6 py-2 rounded hover:bg-[#fff1b2] transition"
              >
                <Filter className="h-4 w-4 mr-2" />
                {showFilters ? "Hide Filters" : "Show Filters"}
              </Button>
              <button
                onClick={handleExportCSVWithCredits}
                className="bg-[#fad945] text-black font-medium px-6 py-2 rounded hover:bg-[#fff1b2] transition"
              >
                Export CSV
              </button>
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
          <div className="w-full overflow-x-auto rounded-md border">
            <Table className="min-w-full text-sm">
              <thead className="bg-[#7ac2a4] text-black text-opacity-100">
                <TableRow>
                  <TableHead className="px-6 py-2">
                    <TableHead className="px-6 py-2">
                      <Checkbox
                        checked={selectAll}
                        onCheckedChange={handleSelectAll}
                      />
                    </TableHead>
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Company
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Website
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Industry
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Product/Service Category
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Business Type (B2B, B2B2C)
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Employees Count
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Revenue
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Year Founded
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    BBB Rating
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Street
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    City
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    State
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Company Phone
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Company LinkedIn
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Owner's First Name
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Owner's Last Name
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Owner's Title
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Owner's LinkedIn
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Owner's Phone Number
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Owner's Email
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Source
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Created Date
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Updated
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-black text-opacity-100 px-6 py-2">
                    Actions
                  </TableHead>
                </TableRow>
              </thead>
              <tbody>
                {currentItems.map((row, i) => (
                  <TableRow key={i} className="border-t">
                    <TableCell className="px-6 py-2">
                      <Checkbox
                        checked={selectedCompanies.includes(row.id)}
                        onCheckedChange={() => handleSelectCompany(row.id)}
                      />
                    </TableCell>
                    {[
                      "company",
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
                    {/* // Edit/Save/Discard action buttons: */}
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
                  <SelectTrigger className="w-[120px] bg-[#7ac2a4] text-black font-medium rounded-md hover:bg-[#6bb293]">
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
                        onClick={() =>
                          setCurrentPage((p) => Math.max(p - 1, 1))
                        }
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
                                  ? "bg-[#7ac2a4] text-black" // active teal background
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
    </>
  );
}
