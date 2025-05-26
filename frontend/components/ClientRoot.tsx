"use client";
import * as React from "react";
import { LeadsProvider } from "./LeadsProvider";

export default function ClientRoot({ children }: { children: React.ReactNode }) {
  return (
    <LeadsProvider>{children}</LeadsProvider>
  );
}
