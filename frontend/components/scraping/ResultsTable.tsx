// ========================================
// Results Table Component - Redesigned with Animations
// ========================================

"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Download, 
  FileJson, 
  FileSpreadsheet, 
  MessageSquare, 
  ExternalLink,
  Phone as PhoneIcon,
  Star,
  MapPin,
  Check,
  X,
  ChevronUp,
  ChevronDown,
  Search
} from "lucide-react";
import { Button, TableSkeleton } from "@/components/common";
import { BulkMessaging } from "@/components/integrations";
import { AnimatedCard } from "@/components/ui";
import { AnimatedButton } from "@/components/ui/animated-button";
import { EmptyState } from "@/components/ui/empty-state";
import { tableAnimations } from "@/lib/animations";
import { truncate, formatPhone, exportToCSV, exportToJSON } from "@/lib/utils";
import { showToast } from "@/lib/toast";
import { useGoogleSheets, useWhatsApp } from "@/hooks";
import type { Lead } from "@/types";

interface ResultsTableProps {
  leads: Lead[];
  isLoading?: boolean;
  onSaveToSheets?: () => void;
  isSaving?: boolean;
}

export function ResultsTable({
  leads,
  isLoading = false,
  onSaveToSheets,
  isSaving = false,
}: ResultsTableProps) {
  const tableRef = useRef<HTMLTableElement>(null);
  const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<keyof Lead | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [showSaveSuccess, setShowSaveSuccess] = useState(false);
  const [saveResult, setSaveResult] = useState<{ url: string; count: number } | null>(null);
  const [showBulkMessaging, setShowBulkMessaging] = useState(false);
  
  // Google Sheets hook
  const { 
    status: googleStatus, 
    isSaving: isGoogleSaving, 
    error: googleError,
    saveToSheets 
  } = useGoogleSheets();

  // WhatsApp hook
  const { status: whatsAppStatus } = useWhatsApp();

  useEffect(() => {
    if (leads.length > 0 && tableRef.current) {
      const rows = tableRef.current.querySelectorAll("tbody tr") as NodeListOf<HTMLElement>;
      tableAnimations.rowsIn(rows);
    }
  }, [leads]);

  if (isLoading) {
    return <TableSkeleton rows={10} columns={6} />;
  }

  if (leads.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <EmptyState
          icon={Search}
          title="No leads yet"
          description="Start a scraping job to see your leads appear here. Results will update in real-time as they're found."
        />
      </motion.div>
    );
  }

  const handleSort = (field: keyof Lead) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const sortedLeads = [...leads].sort((a, b) => {
    if (!sortField) return 0;
    const aValue = a[sortField];
    const bValue = b[sortField];

    // Handle null/undefined values - push them to the end
    if (aValue == null && bValue == null) return 0;
    if (aValue == null) return 1;
    if (bValue == null) return -1;

    const comparison = aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
    return sortDirection === "asc" ? comparison : -comparison;
  });

  const toggleSelect = (placeId: string) => {
    const newSelected = new Set(selectedLeads);
    if (newSelected.has(placeId)) {
      newSelected.delete(placeId);
    } else {
      newSelected.add(placeId);
    }
    setSelectedLeads(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedLeads.size === leads.length) {
      setSelectedLeads(new Set());
    } else {
      setSelectedLeads(new Set(leads.map((l) => l.place_id)));
    }
  };

  const handleExportCSV = () => {
    const toExport =
      selectedLeads.size > 0
        ? leads.filter((l) => selectedLeads.has(l.place_id))
        : leads;
    exportToCSV(toExport, `leads-${Date.now()}`);
  };

  const handleExportJSON = () => {
    const toExport =
      selectedLeads.size > 0
        ? leads.filter((l) => selectedLeads.has(l.place_id))
        : leads;
    exportToJSON(toExport, `leads-${Date.now()}`);
  };

  const handleSaveToGoogleSheets = async () => {
    const leadsToSave = selectedLeads.size > 0 
      ? leads.filter((l) => selectedLeads.has(l.place_id))
      : leads;
    
    const result = await saveToSheets(leadsToSave);
    
    if (result?.success) {
      setSaveResult({
        url: result.spreadsheet_url,
        count: result.rows_added
      });
      setShowSaveSuccess(true);
      
      // Auto-hide after 5 seconds
      setTimeout(() => {
        setShowSaveSuccess(false);
        setSaveResult(null);
      }, 5000);
    }
  };

  return (
    <AnimatedCard className="overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-neutral-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-neutral-50/50 to-transparent">
        <div>
          <h3 className="text-lg font-semibold text-neutral-900 flex items-center gap-2">
            Scraped Leads
            <span className="px-2 py-0.5 text-xs font-bold bg-gradient-to-r from-primary-500 to-secondary-500 text-white rounded-full">
              {leads.length}
            </span>
          </h3>
          <p className="text-sm text-neutral-500">
            {selectedLeads.size > 0 && `${selectedLeads.size} selected • `}
            Click headers to sort
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <AnimatedButton variant="outline" size="sm" onClick={handleExportCSV}>
            <Download className="w-4 h-4 mr-1.5" />
            CSV
          </AnimatedButton>
          <AnimatedButton variant="outline" size="sm" onClick={handleExportJSON}>
            <FileJson className="w-4 h-4 mr-1.5" />
            JSON
          </AnimatedButton>
          {/* Google Sheets Integration Button */}
          {googleStatus?.connected ? (
            <AnimatedButton
              size="sm"
              onClick={handleSaveToGoogleSheets}
              loading={isGoogleSaving}
              disabled={isGoogleSaving}
              className="bg-green-600 hover:bg-green-700 border-green-600"
            >
              <FileSpreadsheet className="w-4 h-4 mr-1.5" />
              {isGoogleSaving ? "Saving..." : "Sheets"}
            </AnimatedButton>
          ) : (
            <AnimatedButton
              size="sm"
              variant="outline"
              onClick={() => window.location.href = "/dashboard/settings"}
              title="Connect Google Sheets in Settings"
            >
              <FileSpreadsheet className="w-4 h-4 mr-1.5 text-neutral-400" />
              Connect
            </AnimatedButton>
          )}
          {/* WhatsApp Button */}
          {(whatsAppStatus?.connected || whatsAppStatus?.has_shared_access) ? (
            <AnimatedButton
              size="sm"
              onClick={() => setShowBulkMessaging(true)}
              className="bg-green-500 hover:bg-green-600 border-green-500"
            >
              <MessageSquare className="w-4 h-4 mr-1.5" />
              WhatsApp
            </AnimatedButton>
          ) : (
            <AnimatedButton
              size="sm"
              variant="outline"
              onClick={() => window.location.href = "/dashboard/settings"}
              title="Connect WhatsApp in Settings"
            >
              <MessageSquare className="w-4 h-4 mr-1.5 text-neutral-400" />
              Connect
            </AnimatedButton>
          )}
          {onSaveToSheets && (
            <AnimatedButton
              size="sm"
              onClick={onSaveToSheets}
              loading={isSaving}
              disabled={isSaving}
            >
              Save to Sheets
            </AnimatedButton>
          )}
        </div>
      </div>

      {/* Bulk Messaging Modal */}
      <AnimatePresence>
        {showBulkMessaging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-lg mx-4"
            >
              <BulkMessaging
                leads={selectedLeads.size > 0 
                  ? leads.filter((l) => selectedLeads.has(l.place_id))
                  : leads
                }
                onClose={() => setShowBulkMessaging(false)}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Success Toast */}
      <AnimatePresence>
        {showSaveSuccess && saveResult && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mx-6 my-4 p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                <Check className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="font-semibold text-green-800">
                  Saved {saveResult.count} leads to Google Sheets!
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <a
                href={saveResult.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 text-sm font-medium text-green-700 bg-green-100 rounded-lg hover:bg-green-200 transition-colors flex items-center gap-1.5"
              >
                <ExternalLink className="w-4 h-4" />
                Open Sheet
              </a>
              <button
                onClick={() => setShowSaveSuccess(false)}
                className="p-2 text-green-500 hover:text-green-700 hover:bg-green-100 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Google Error Toast */}
      <AnimatePresence>
        {googleError && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mx-6 my-4 p-4 bg-red-50 border border-red-200 rounded-xl"
          >
            <p className="text-sm text-red-600 font-medium">{googleError}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <div className="overflow-x-auto">
        <table ref={tableRef} className="w-full">
          <thead className="bg-neutral-50/50">
            <tr>
              <th className="px-4 py-3.5 w-12">
                <input
                  type="checkbox"
                  checked={selectedLeads.size === leads.length}
                  onChange={toggleSelectAll}
                  className="w-4 h-4 text-primary-600 rounded-md border-neutral-300 focus:ring-primary-500 cursor-pointer"
                />
              </th>
              <th
                className="px-4 py-3.5 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider cursor-pointer hover:text-neutral-700 transition-colors group"
                onClick={() => handleSort("name")}
              >
                <div className="flex items-center gap-1">
                  Name
                  {sortField === "name" && (
                    sortDirection === "asc" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                  )}
                </div>
              </th>
              <th
                className="px-4 py-3.5 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider cursor-pointer hover:text-neutral-700 transition-colors"
                onClick={() => handleSort("phone")}
              >
                <div className="flex items-center gap-1">
                  Phone
                  {sortField === "phone" && (
                    sortDirection === "asc" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                  )}
                </div>
              </th>
              <th className="px-4 py-3.5 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                Website
              </th>
              <th
                className="px-4 py-3.5 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider cursor-pointer hover:text-neutral-700 transition-colors"
                onClick={() => handleSort("rating")}
              >
                <div className="flex items-center gap-1">
                  Rating
                  {sortField === "rating" && (
                    sortDirection === "asc" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                  )}
                </div>
              </th>
              <th className="px-4 py-3.5 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                Address
              </th>
              <th className="px-4 py-3.5 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {sortedLeads.map((lead, index) => (
              <motion.tr
                key={lead.place_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.02 }}
                className="hover:bg-neutral-50/50 transition-colors group"
              >
                <td className="px-4 py-3.5">
                  <input
                    type="checkbox"
                    checked={selectedLeads.has(lead.place_id)}
                    onChange={() => toggleSelect(lead.place_id)}
                    className="w-4 h-4 text-primary-600 rounded-md border-neutral-300 focus:ring-primary-500 cursor-pointer"
                  />
                </td>
                <td className="px-4 py-3.5">
                  <div className="font-medium text-neutral-900">
                    {truncate(lead.name, 30)}
                  </div>
                  {lead.category && (
                    <div className="text-xs text-neutral-500 mt-0.5">{lead.category}</div>
                  )}
                </td>
                <td className="px-4 py-3.5 text-sm">
                  {lead.phone ? (
                    <a
                      href={`tel:${lead.phone}`}
                      className="inline-flex items-center gap-1.5 text-primary-600 hover:text-primary-700 font-medium transition-colors"
                    >
                      <PhoneIcon className="w-3.5 h-3.5" />
                      {formatPhone(lead.phone)}
                    </a>
                  ) : (
                    <span className="text-neutral-400">N/A</span>
                  )}
                </td>
                <td className="px-4 py-3.5 text-sm">
                  {lead.website ? (
                    <a
                      href={lead.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 font-medium transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      Visit
                    </a>
                  ) : (
                    <span className="text-neutral-400">N/A</span>
                  )}
                </td>
                <td className="px-4 py-3.5">
                  {lead.rating ? (
                    <div className="flex items-center gap-1.5">
                      <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                      <span className="text-sm font-medium text-neutral-700">
                        {lead.rating}
                      </span>
                      {lead.reviews_count && (
                        <span className="text-xs text-neutral-500">
                          ({lead.reviews_count})
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-neutral-400 text-sm">N/A</span>
                  )}
                </td>
                <td className="px-4 py-3.5 text-sm text-neutral-600 max-w-xs">
                  {lead.address ? (
                    <div className="flex items-start gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-neutral-400 flex-shrink-0 mt-0.5" />
                      <span className="truncate">{lead.address}</span>
                    </div>
                  ) : (
                    <span className="text-neutral-400">N/A</span>
                  )}
                </td>
                <td className="px-4 py-3.5">
                  <a
                    href={lead.href || lead.google_maps_url || `https://www.google.com/maps/place/?q=place_id:${lead.place_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
                  >
                    <MapPin className="w-3.5 h-3.5" />
                    Map
                  </a>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </AnimatedCard>
  );
}

export default ResultsTable;
