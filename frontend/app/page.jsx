"use client";

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

export default function Home() {
  return (
    <>
      <Header />
      <main className="px-20 py-16 space-y-10">
        <div className="text-2xl font-semibold text-foreground text-white">
          Hi, Rafi 👋 Are you ready to scrape?
        </div>
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              label: "Total leads scraped",
              value: "12,340",
              change: "+4.5%",
              comparison: "vs last month",
            },
            {
              label: "Token usage",
              value: "89,231",
              change: "+3.1%",
              comparison: "vs last month",
            },
            {
              label: "Active enrichments",
              value: "312",
              change: "-2.3%",
              comparison: "vs last month",
            },
            {
              label: "Avg. response time",
              value: "1.4s",
              change: "-6.2%",
              comparison: "vs last month",
            },
          ].map((stat, index) => (
            <Card key={index} className="rounded-2xl shadow-sm border">
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
              </CardContent>
            </Card>
          ))}
        </div>

        {/* History Table */}
        <div className="mt-10">
          <h2 className="text-lg font-semibold mb-4">Scraping History</h2>
          <div className="w-full overflow-x-auto rounded-md border">
            <div className="min-w-fit">
              <Table className="min-w-full">
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs break-words max-w-[160px] px-2 py-1">
                      Date
                    </TableHead>
                    <TableHead className="text-xs break-words max-w-[180px] px-2 py-1">
                      Industry
                    </TableHead>
                    <TableHead className="text-xs break-words max-w-[160px] px-2 py-1">
                      Location
                    </TableHead>
                    <TableHead className="text-xs break-words max-w-[200px] px-2 py-1">
                      Source
                    </TableHead>
                    <TableHead className="text-xs break-words max-w-[200px] px-2 py-1">
                      Leads Found
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[
                    {
                      date: "2025-05-23",
                      industry: "SaaS",
                      location: "San Francisco, CA",
                      source: "Database",
                      leads: 45,
                    },
                    {
                      date: "2025-05-22",
                      industry: "Healthcare",
                      location: "Austin, TX",
                      source: "Scraper",
                      leads: 91,
                    },
                    {
                      date: "2025-05-21",
                      industry: "Finance",
                      location: "Chicago, IL",
                      source: "Database",
                      leads: 63,
                    },
                  ].map((entry, i) => (
                    <TableRow key={i}>
                      <TableCell className="max-w-[160px] break-words whitespace-pre-wrap text-sm align-top px-3 py-2">
                        {entry.date}
                      </TableCell>
                      <TableCell className="max-w-[180px] break-words whitespace-pre-wrap text-sm align-top px-3 py-2">
                        {entry.industry}
                      </TableCell>
                      <TableCell className="max-w-[160px] break-words whitespace-pre-wrap text-sm align-top px-3 py-2">
                        {entry.location}
                      </TableCell>
                      <TableCell className="max-w-[200px] break-words whitespace-pre-wrap text-sm align-top px-3 py-2">
                        {entry.source}
                      </TableCell>
                      <TableCell className="max-w-[200px] break-words whitespace-pre-wrap text-sm align-top px-3 py-2">
                        {entry.leads}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
