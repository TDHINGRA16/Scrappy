// ========================================
// Utility Functions
// ========================================

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Lead, ExportOptions } from "@/types";

// Tailwind class merge utility
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format date helper
export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

// Format phone number
export function formatPhone(phone: string | null): string {
  if (!phone) return "N/A";
  // Remove non-digits
  const cleaned = phone.replace(/\D/g, "");
  // Format as (XXX) XXX-XXXX for US numbers
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  return phone;
}

// Truncate text
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + "...";
}

// Export leads to CSV
export function exportToCSV(leads: Lead[], filename = "leads"): void {
  const headers = [
    "Name",
    "Phone",
    "Email",
    "Website",
    "Address",
    "Rating",
    "Reviews",
    "Category",
    "Google Maps URL",
  ];

  const rows = leads.map((lead) => [
    lead.name || "",
    lead.phone || "",
    lead.email || "",
    lead.website || "",
    lead.address || "",
    lead.rating?.toString() || "",
    lead.reviews_count?.toString() || "",
    lead.category || "",
    lead.google_maps_url || lead.href || "",
  ]);

  const csvContent = [
    headers.join(","),
    ...rows.map((row) =>
      row.map((cell) => `"${String(cell || "").replace(/"/g, '""')}"`).join(",")
    ),
  ].join("\n");

  downloadFile(csvContent, `${filename}.csv`, "text/csv");
}

// Export leads to JSON
export function exportToJSON(leads: Lead[], filename = "leads"): void {
  const jsonContent = JSON.stringify(leads, null, 2);
  downloadFile(jsonContent, `${filename}.json`, "application/json");
}

// Generic export function
export function exportLeads(leads: Lead[], options: ExportOptions): void {
  const { format, filename = "leads" } = options;

  switch (format) {
    case "csv":
      exportToCSV(leads, filename);
      break;
    case "json":
      exportToJSON(leads, filename);
      break;
    default:
      console.error(`Unsupported export format: ${format}`);
  }
}

// Download file helper
function downloadFile(content: string, filename: string, type: string): void {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Debounce function
export function debounce<T extends (...args: Parameters<T>) => ReturnType<T>>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// Sleep utility
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Calculate scraping progress percentage
export function calculateProgress(current: number, target: number): number {
  if (target <= 0) return 0;
  return Math.min(Math.round((current / target) * 100), 100);
}

// Validate email
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Generate unique ID
export function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}
