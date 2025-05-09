"use client";
import { LeadsProvider } from "./LeadsProvider";
import mockResults from "./mockResults"; // or your real initial data

export default function ClientRoot({ children }: { children: React.ReactNode }) {
  return (
    <LeadsProvider initialLeads={mockResults}>
      {children}
    </LeadsProvider>
  );
}
