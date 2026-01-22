// ========================================
// History Page - Redesigned with Animations
// ========================================

"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  History, Clock, Search, Calendar, Download, Filter, 
  ExternalLink, FileSpreadsheet, AlertCircle, CheckCircle,
  ChevronLeft, ChevronRight, TrendingUp, XCircle
} from "lucide-react";
import { AnimatedCard } from "@/components/ui";
import { AnimatedButton } from "@/components/ui/animated-button";
import { EmptyState } from "@/components/ui/empty-state";
import { usePageTransition } from "@/hooks/useAnimation";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/lib/api-client";

interface HistoryItem {
  id: string;
  query: string;
  total_found: number;
  new_results: number;
  skipped_duplicates: number;
  time_taken: number;
  sheet_url: string | null;
  sheet_id: string | null;
  status: string;
  error: string | null;
  date: string;
  completed_at: string | null;
}

interface UserStats {
  total_unique_businesses: number;
  total_scrapes: number;
  total_results_collected: number;
  total_duplicates_skipped: number;
  dedup_efficiency: number;
  total_time_saved_minutes: number;
}

export default function HistoryPage() {
  const pageRef = usePageTransition();
  const { token } = useAuth();
  
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);
  
  const LIMIT = 10;

  useEffect(() => {
    if (token) {
      fetchHistory();
      fetchStats();
    }
  }, [token, page]);

  const fetchHistory = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await apiClient.getHistory(token, LIMIT, page * LIMIT);
      if (response.data) {
        setHistory(response.data.history);
        setHasMore(response.data.has_more);
        setTotal(response.data.total);
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    if (!token) return;
    
    try {
      const response = await apiClient.getUserStats(token);
      if (response.data) {
        setStats(response.data);
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const filteredHistory = history.filter(item => 
    item.query.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div ref={pageRef}>
      {/* Page Header */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl">
            <History className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-neutral-900 to-neutral-600 bg-clip-text text-transparent">
            Scraping History
          </h1>
        </div>
        <p className="text-neutral-500">
          View your past scraping sessions and results
        </p>
      </motion.div>

      {/* Stats Cards */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
        >
          <AnimatedCard className="p-4">
            <div className="text-sm text-neutral-500 mb-1">Total Scrapes</div>
            <div className="text-2xl font-bold text-neutral-900">{stats.total_scrapes}</div>
          </AnimatedCard>
          <AnimatedCard className="p-4">
            <div className="text-sm text-neutral-500 mb-1">Unique Businesses</div>
            <div className="text-2xl font-bold text-primary-600">{stats.total_unique_businesses.toLocaleString()}</div>
          </AnimatedCard>
          <AnimatedCard className="p-4">
            <div className="text-sm text-neutral-500 mb-1">Duplicates Skipped</div>
            <div className="text-2xl font-bold text-secondary-600">{stats.total_duplicates_skipped.toLocaleString()}</div>
          </AnimatedCard>
          <AnimatedCard className="p-4">
            <div className="text-sm text-neutral-500 mb-1">Time Saved</div>
            <div className="text-2xl font-bold text-green-600">{stats.total_time_saved_minutes.toFixed(0)} min</div>
          </AnimatedCard>
        </motion.div>
      )}

      {/* Filter Bar */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6"
      >
        <AnimatedCard className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                <input
                  type="text"
                  placeholder="Search history..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-neutral-50 border border-neutral-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all"
                />
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-neutral-500">
              Total: {total} sessions
            </div>
          </div>
        </AnimatedCard>
      </motion.div>

      {/* History List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        {loading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <AnimatedCard key={i} className="p-4 animate-pulse">
                <div className="h-6 bg-neutral-200 rounded w-1/3 mb-3" />
                <div className="h-4 bg-neutral-100 rounded w-2/3" />
              </AnimatedCard>
            ))}
          </div>
        ) : filteredHistory.length === 0 ? (
          <EmptyState
            icon={Clock}
            title="No history yet"
            description="Your scraping history will appear here after you run your first scraping job. Start scraping to see your results!"
            actionLabel="Start Scraping"
            actionHref="/dashboard"
          />
        ) : (
          <div className="space-y-4">
            <AnimatePresence>
              {filteredHistory.map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <AnimatedCard className="p-5 hover:shadow-md transition-shadow">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      {/* Left: Query Info */}
                      <div className="flex-1 min-w-[200px]">
                        <div className="flex items-center gap-2 mb-2">
                          {item.status === "completed" ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-500" />
                          )}
                          <span className="font-semibold text-neutral-900">{item.query}</span>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-sm text-neutral-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            {formatDate(item.date)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5" />
                            {formatDuration(item.time_taken)}
                          </span>
                        </div>
                      </div>

                      {/* Center: Stats */}
                      <div className="flex items-center gap-6 text-sm">
                        <div className="text-center">
                          <div className="font-bold text-lg text-primary-600">{item.new_results}</div>
                          <div className="text-neutral-500 text-xs">New</div>
                        </div>
                        <div className="text-center">
                          <div className="font-bold text-lg text-secondary-600">{item.skipped_duplicates}</div>
                          <div className="text-neutral-500 text-xs">Skipped</div>
                        </div>
                        <div className="text-center">
                          <div className="font-bold text-lg text-neutral-600">{item.total_found}</div>
                          <div className="text-neutral-500 text-xs">Found</div>
                        </div>
                      </div>

                      {/* Right: Actions */}
                      <div className="flex items-center gap-2">
                        {item.sheet_url && (
                          <a
                            href={item.sheet_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-sm font-medium"
                          >
                            <FileSpreadsheet className="w-4 h-4" />
                            Open Sheet
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Error Message */}
                    {item.error && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-100 rounded-lg flex items-start gap-2 text-sm text-red-700">
                        <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        {item.error}
                      </div>
                    )}
                  </AnimatedCard>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Pagination */}
            {total > LIMIT && (
              <div className="flex items-center justify-center gap-4 mt-6">
                <AnimatedButton
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </AnimatedButton>
                <span className="text-sm text-neutral-500">
                  Page {page + 1} of {Math.ceil(total / LIMIT)}
                </span>
                <AnimatedButton
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => p + 1)}
                  disabled={!hasMore}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </AnimatedButton>
              </div>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}
