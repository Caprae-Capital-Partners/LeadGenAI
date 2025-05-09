import { Lead } from "@/components/LeadsProvider";
import { createHash } from "crypto";

/**
 * Generates a unique identifier for a lead based on its details
 * @param lead The lead object to generate an ID for
 * @returns A unique string identifier
 */
export function generateLeadId(lead: Lead): string {
  // Combine relevant fields to create a unique string
  const uniqueString = [
    lead.company,
    lead.street,
    lead.city,
    lead.state,
    lead.business_phone,
    lead.website
  ].join('|').toLowerCase();

  // Create a SHA-256 hash of the combined string
  const hash = createHash('sha256');
  hash.update(uniqueString);
  
  // Return the first 12 characters of the hex digest
  return hash.digest('hex').substring(0, 12);
}

/**
 * Adds unique identifiers to an array of leads
 * @param leads Array of leads to process
 * @returns Array of leads with unique identifiers
 */
export function addUniqueIdsToLeads(leads: Lead[]): Lead[] {
  return leads.map(lead => ({
    ...lead,
    id: parseInt(generateLeadId(lead), 16) // Convert hex to number for compatibility
  }));
}