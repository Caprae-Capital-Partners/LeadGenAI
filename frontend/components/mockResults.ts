import type { Lead } from "./LeadsProvider";

const mockResults: Lead[] = [
  {
    id: 1,
    company: "Acme Inc",
    website: "acme.com",
    industry: "Software & Technology",
    street: "123 Tech Blvd",
    city: "San Francisco",
    state: "CA",
    bbb_rating: "A+",
    business_phone: "+1 (555) 123-4567",
  },
  // ...add more mock leads as needed
];

export default mockResults;
