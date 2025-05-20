"use server"

// This is a mock implementation for demo purposes
// In a real application, you would connect to a database

const leads = []

export async function submitLeadForm(formData) {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 1000))

  // Add timestamp
  const newLead = {
    id: Date.now().toString(),
    ...formData,
    createdAt: new Date().toISOString(),
  }

  // Add to our mock database
  leads.push(newLead)

  return { success: true }
}

export async function getLeads() {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 500))

  return leads
}
