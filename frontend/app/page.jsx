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

import { redirect } from "next/navigation";

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
  const [cityFilter, setCityFilter] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [selectAll, setSelectAll] = useState(false);
  const router = useRouter();
  const handleSave = () => {
    // Commit the edits to the main scrapingHistory state
    setScrapingHistory(editedRows);
    setIsEditing(false);
    console.log("Saved edits:", editedRows);
  };
  const handleDiscard = () => {
    setEditedRows(scrapingHistory); // Reset edits to the original state
    setIsEditing(false); // Exit edit mode
    console.log("Changes discarded.");
  };

  const [showFilters, setShowFilters] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
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
      "Created",
      "Updated",
    ];

    const csvContent = [
      headers.join(","), // Header row
      ...scrapingHistory.map((row) =>
        headers.map((h) => `"${row[toCamelCaseKeys(h)] || ""}"`).join(",")
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

  const [editedRows, setEditedRows] = useState(scrapingHistory); // duplicate of original data
  // Example pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);

  // Derive indexes for slicing the filtered data
  const totalPages = Math.ceil(scrapingHistory.length / itemsPerPage);
  const indexOfFirstItem = (currentPage - 1) * itemsPerPage;
  const indexOfLastItem = currentPage * itemsPerPage;
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
    const date = new Date(rawDate).toISOString().split("T")[0];
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
          created: entry.created || "",
          updated: entry.updated || "",
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

  const [subscriptionInfo, setSubscriptionInfo] = useState(null);

  useEffect(() => {
    const fetchSubscriptionInfo = async () => {
      try {
        const existing = sessionStorage.getItem("subscriptionInfo");
        if (existing) {
          setSubscriptionInfo(JSON.parse(existing));
          return;
        }

        const res = await fetch(
          "https://data.capraeleadseekers.site/api/user/subscription_info",
          {
            method: "GET",
            credentials: "include",
          }
        );

        if (!res.ok) {
          console.warn("⚠️ Failed to fetch subscription info:", res.status);
          return;
        }

        const data = await res.json();
        sessionStorage.setItem("subscriptionInfo", JSON.stringify(data));
        setSubscriptionInfo(data);
      } catch (err) {
        console.error("Error fetching subscription info:", err);
      }
    };

    fetchSubscriptionInfo();
  }, []);
  

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

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[
            {
              label: "Total Leads Scraped",
              value: scrapingHistory.length.toLocaleString(),
              change: "+0%", // Optionally compute later
              comparison: "total enriched leads",
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
              className="rounded-2xl border shadow-sm transition duration-200 transform hover:scale-105 hover:shadow-[0_4px_20px_0_rgba(122,194,164,0.5)]"
            >
              <CardHeader className="pb-2">
                <CardDescription className="text-sm text-muted-foreground">
                  {stat.label}
                </CardDescription>
                <CardTitle className="text-2xl font-bold text-foreground">
                  {stat.value}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 text-sm text-blue-600">
                <span>{stat.change}</span>{" "}
                <span className="text-muted-foreground">{stat.comparison}</span>
                {/* Show "Upgrade" button only if this stat has an action */}
                {stat.action && (
                  <div className="mt-3">
                    <a href={stat.action.link}>
                      <Button size="sm" variant="outline">
                        {stat.action.label}
                      </Button>
                    </a>
                  </div>
                )}
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
                      fill={`hsl(${(index * 60) % 360}, 70%, 50%)`}
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
                onClick={() => setShowFilters(!showFilters)}
                className="bg-[#fad945] text-black font-medium px-6 py-2 rounded hover:bg-[#fff1b2] transition"
              >
                <Filter className="h-4 w-4 mr-2" />
                {showFilters ? "Hide Filters" : "Show Filters"}
              </Button>
              <button
                onClick={handleExportCSV}
                className="bg-[#fad945] text-black font-medium px-6 py-2 rounded hover:bg-[#fff1b2] transition"
              >
                Export CSV
              </button>
            </div>
          </div>
          {showFilters && (
            <div className="flex flex-wrap gap-4 my-4">
              <Input placeholder="Industry" className="w-[240px]" />
              <Input
                placeholder="Product/Service Category"
                className="w-[240px]"
              />
              <Input placeholder="Business Type" className="w-[240px]" />
              <Input placeholder="Employees Count" className="w-[240px]" />
              <Input placeholder="Revenue" className="w-[240px]" />
              <Input placeholder="Year Founded" className="w-[240px]" />
              <Input placeholder="BBB Rating" className="w-[240px]" />
              <Input placeholder="City" className="w-[240px]" />
              <Input placeholder="State" className="w-[240px]" />
              <Input placeholder="Source" className="w-[240px]" />
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
                {scrapingHistory.map((row, i) => (
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
                          {isEditing ? (
                            <input
                              type="text"
                              className="w-full bg-transparent border-b border-muted focus:outline-none text-sm"
                              value={rawValue ?? ""}
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

                    <TableCell className="px-6 py-2">
                      {!isEditing ? (
                        <span
                          className="text-blue-500 hover:underline cursor-pointer mr-2"
                          onClick={() => setIsEditing(true)}
                        >
                          Edit
                        </span>
                      ) : (
                        <>
                          <span
                            className="text-green-500 hover:underline cursor-pointer mr-2"
                            onClick={handleSave}
                          >
                            Save
                          </span>
                          <span
                            className="text-red-500 hover:underline cursor-pointer"
                            onClick={handleDiscard}
                          >
                            Discard
                          </span>
                        </>
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
          {isEditing ? (
            <>
              <button
                onClick={() => {
                  setEditedRows(scrapingHistory); // reset
                  setIsEditing(false);
                }}
                className="bg-red-500 text-white px-6 py-2 rounded hover:bg-red-600"
              >
                Discard Changes
              </button>
              <button
                onClick={() => {
                  // Save edited rows to original state or call API
                  console.log("Saved:", editedRows);
                  setIsEditing(false);
                }}
                className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600"
              >
                Save Changes
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="bg-[#7ac2a4] text-black px-6 py-2 rounded hover:bg-[#6bb293]"
            >
              Edit
            </button>
          )}
        </div>
      </main>
    </>
  );
}
