// ========================================
// Dashboard Page (Main Scraper) - Redesigned with Animations
// ========================================

"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import gsap from "gsap";
import {
  Users,
  Phone,
  Globe,
  Clock,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  X,
  Zap,
  TrendingUp,
  Activity,
  Shield,
  Database
} from "lucide-react";
import { ScrapingForm } from "@/components/scraping/ScrapingForm";
import { ResultsTable } from "@/components/scraping/ResultsTable";
import { ProgressBar } from "@/components/scraping/ProgressBar";
import { ScrapeProgress } from "@/components/scraping";
import { useScraping } from "@/hooks/useScraping";
import { useAuth } from "@/hooks/useAuth";
import { useGoogleSheets } from "@/hooks/useGoogleSheets";
import { apiClient } from "@/lib/api-client";
import { showToast } from "@/lib/toast";
import { AnimatedCard } from "@/components/ui/animated-card";
import { AnimatedButton } from "@/components/ui/animated-button";
import { CounterAnimation } from "@/components/animations/scroll-reveal";
import { cn } from "@/lib/utils";

// ========================================
// Animated Stats Card Component
// ========================================

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: "primary" | "success" | "warning" | "secondary";
  suffix?: string;
  delay?: number;
}

function StatCard({ title, value, icon, color, suffix = "", delay = 0 }: StatCardProps) {
  const colorStyles = {
    primary: "from-primary-500 to-primary-600 shadow-primary-500/25",
    success: "from-success-500 to-success-600 shadow-success-500/25",
    warning: "from-warning-500 to-warning-600 shadow-warning-500/25",
    secondary: "from-secondary-500 to-secondary-600 shadow-secondary-500/25",
  };

  const iconBgStyles = {
    primary: "bg-primary-100 text-primary-600",
    success: "bg-success-100 text-success-600",
    warning: "bg-warning-100 text-warning-600",
    secondary: "bg-secondary-100 text-secondary-600",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.5,
        delay,
        type: "spring",
        stiffness: 100
      }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="group"
    >
      <div className="relative bg-white rounded-2xl border border-neutral-200/60 p-6 shadow-sm hover:shadow-lg hover:shadow-neutral-200/50 transition-all duration-300 overflow-hidden">
        {/* Gradient accent line */}
        <div className={cn(
          "absolute top-0 left-0 right-0 h-1 bg-gradient-to-r",
          colorStyles[color]
        )} />

        {/* Background glow on hover */}
        <div className={cn(
          "absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity duration-300 bg-gradient-to-br",
          colorStyles[color]
        )} />

        <div className="relative flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-neutral-500 mb-1">{title}</p>
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold text-neutral-900">
                <CounterAnimation end={value} duration={1.5} delay={delay + 0.3} />
              </span>
              {suffix && (
                <span className="text-sm text-neutral-500">{suffix}</span>
              )}
            </div>
          </div>
          <div className={cn(
            "p-3 rounded-xl transition-transform duration-300 group-hover:scale-110",
            iconBgStyles[color]
          )}>
            {icon}
          </div>
        </div>

        {/* Sparkle effect on hover */}
        <motion.div
          className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100"
          initial={{ scale: 0, rotate: -45 }}
          whileHover={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Sparkles className="w-4 h-4 text-neutral-300" />
        </motion.div>
      </div>
    </motion.div>
  );
}

// ========================================
// Status Badge Component
// ========================================

interface StatusBadgeProps {
  status: "checking" | "online" | "offline";
}

function StatusBadge({ status }: StatusBadgeProps) {
  const config = {
    checking: {
      color: "bg-warning-500",
      text: "Connecting...",
      animate: true,
    },
    online: {
      color: "bg-success-500",
      text: "Online",
      animate: false,
    },
    offline: {
      color: "bg-error-500",
      text: "Offline",
      animate: false,
    },
  };

  const { color, text, animate } = config[status];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="inline-flex items-center gap-2 px-3 py-1.5 bg-neutral-100 rounded-full"
    >
      <span className={cn(
        "w-2 h-2 rounded-full",
        color,
        animate && "animate-pulse"
      )} />
      <span className="text-sm font-medium text-neutral-600">
        Backend: {text}
      </span>
    </motion.div>
  );
}

// ========================================
// Main Dashboard Page
// ========================================

export default function DashboardPage() {
  const pageRef = useRef<HTMLDivElement>(null);
  const { token } = useAuth();
  const {
    leads,
    isLoading,
    progress,
    error,
    lastScrapeResult,
    scrapeId,
    clearError,
    handleAsyncComplete,
    handleAsyncError,
    startScrapingAsync,
  } = useScraping();

  const { saveToSheets: saveToGoogleSheets } = useGoogleSheets();

  // Debug: log leads state changes
  useEffect(() => {
    console.log('[Dashboard] leads state changed:', leads?.length || 0, 'items');
    if (leads?.length > 0) {
      console.log('[Dashboard] First lead:', leads[0]);
    }
  }, [leads]);

  // Debug: log scrapeId and isLoading changes
  useEffect(() => {
    console.log('[Dashboard] scrapeId:', scrapeId, 'isLoading:', isLoading);
  }, [scrapeId, isLoading]);

  const [isSaving, setIsSaving] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("online");
  const [currentQuery, setCurrentQuery] = useState<string>("");
  const [seenPlacesCount, setSeenPlacesCount] = useState<number>(0);

  // Page entrance animation
  useEffect(() => {
    if (pageRef.current) {
      gsap.fromTo(
        pageRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }
      );
    }
  }, []);



  // Fetch seen places count for dedup display
  useEffect(() => {
    const fetchSeenPlaces = async () => {
      if (!token) return;
      try {
        const response = await apiClient.getSeenPlacesCount(token);
        if (response.data) {
          setSeenPlacesCount(response.data.seen_places_count);
        }
      } catch (error) {
        console.error("Failed to fetch seen places:", error);
      }
    };
    fetchSeenPlaces();
  }, [token, leads]); // Refresh when new leads are scraped

  const handleSaveToSheets = async () => {
    setIsSaving(true);
    showToast.loading("Saving to Google Sheets...");

    // Use integration service with query name
    // Use currentQuery as fallback if lastScrapeResult is cleared/not available
    const queryName = lastScrapeResult?.query || currentQuery;
    const result = await saveToGoogleSheets(leads, queryName);

    setIsSaving(false);
    showToast.dismiss();

    if (result) {
      showToast.success(`Successfully saved ${result.rows_added} leads to Google Sheets!`);
    } else {
      showToast.error("Failed to save to Google Sheets. Please ensure you have connected your account.");
    }
  };

  return (
    <div ref={pageRef} className="min-h-screen">
      {/* Error Alert */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className="mb-6 bg-error-50 border border-error-200 text-error-700 px-4 py-3 rounded-xl flex items-center justify-between shadow-sm"
          >
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-error-500" />
              <span className="font-medium">{error}</span>
            </div>
            <button
              onClick={clearError}
              className="p-1 hover:bg-error-100 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl shadow-lg shadow-primary-500/25">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-neutral-900 to-neutral-600 bg-clip-text text-transparent">
                Lead Scraper
              </h1>
            </div>
            <p className="text-neutral-500 ml-[52px]">
              Extract high-quality business leads from Google Maps
            </p>
          </div>

        </div>
      </motion.div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <StatCard
          title="Leads Found"
          value={leads.length}
          icon={<Users className="w-5 h-5" />}
          color="primary"
          delay={0}
        />
        <StatCard
          title="With Phone"
          value={leads.filter((l) => l.phone).length}
          icon={<Phone className="w-5 h-5" />}
          color="success"
          delay={0.1}
        />
        <StatCard
          title="With Website"
          value={leads.filter((l) => l.website).length}
          icon={<Globe className="w-5 h-5" />}
          color="secondary"
          delay={0.2}
        />
        <StatCard
          title="Scrape Time"
          value={Math.round(lastScrapeResult?.scrape_time_seconds || 0)}
          icon={<Clock className="w-5 h-5" />}
          color="warning"
          suffix="sec"
          delay={0.3}
        />
        <StatCard
          title="Dedup Database"
          value={seenPlacesCount}
          icon={<Shield className="w-5 h-5" />}
          color="success"
          delay={0.4}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scraping Form Column */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="lg:col-span-1 space-y-6"
        >
          {/* Scraping Form Card */}
          <AnimatedCard variant="elevated" padding="none" className="overflow-hidden">
            <div className="bg-gradient-to-r from-primary-500 to-secondary-500 p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                  <Activity className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-white">New Scrape</h2>
                  <p className="text-sm text-white/80">Configure your search</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              <ScrapingForm
                onQueryChange={setCurrentQuery}
                startScrapingAsync={startScrapingAsync}
                isLoading={isLoading}
                progress={progress}
              />
            </div>
          </AnimatedCard>

          {/* Fallback Progress Card for non-async scraping (when scrapeId not available) */}
          <AnimatePresence>
            {isLoading && !scrapeId && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <AnimatedCard variant="bordered" className="overflow-hidden">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-primary-100 rounded-lg">
                      <TrendingUp className="w-5 h-5 text-primary-600 animate-pulse" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-neutral-900">Scraping in Progress</h3>
                      <p className="text-sm text-neutral-500">Please wait...</p>
                    </div>
                  </div>
                  <ProgressBar progress={progress} />
                </AnimatedCard>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Quick Tips Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <div className="bg-gradient-to-br from-neutral-50 to-neutral-100/50 rounded-2xl border border-neutral-200/60 p-5">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-secondary-500" />
                <h3 className="font-semibold text-neutral-700">Pro Tips</h3>
              </div>
              <ul className="space-y-2 text-sm text-neutral-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-success-500 mt-0.5 flex-shrink-0" />
                  <span>Be specific with your search query for better results</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-success-500 mt-0.5 flex-shrink-0" />
                  <span>Include city or region for local businesses</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-success-500 mt-0.5 flex-shrink-0" />
                  <span>Export to Google Sheets for easy sharing</span>
                </li>
              </ul>
            </div>
          </motion.div>
        </motion.div>

        {/* Results Table Column - Show Progress during scraping, Results when done */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="lg:col-span-2"
        >
          <AnimatePresence mode="wait">
            {/* Show Progress Component when scraping is in progress */}
            {scrapeId && isLoading ? (
              <motion.div
                key="progress"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
              >
                <AnimatedCard variant="elevated" className="overflow-hidden">
                  <ScrapeProgress
                    scrapeId={scrapeId}
                    query={currentQuery}
                    onComplete={(results) => {
                      handleAsyncComplete(results);
                      showToast.success(`Found ${results.length} leads!`);
                    }}
                    onError={(errorMsg) => {
                      handleAsyncError(errorMsg);
                      showToast.error(errorMsg);
                    }}
                  />
                </AnimatedCard>
              </motion.div>
            ) : (
              /* Show Results Table when scraping is complete or idle */
              <motion.div
                key="results"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
              >
                <AnimatedCard variant="elevated" padding="none" className="overflow-hidden">
                  <div className="border-b border-neutral-200 bg-neutral-50/50 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-success-100 rounded-lg">
                          <Users className="w-5 h-5 text-success-600" />
                        </div>
                        <div>
                          <h2 className="text-lg font-semibold text-neutral-900">Results</h2>
                          <p className="text-sm text-neutral-500">
                            {leads.length > 0
                              ? `${leads.length} leads found`
                              : "No leads yet - start scraping!"}
                          </p>
                        </div>
                      </div>
                      {leads.length > 0 && (
                        <AnimatedButton
                          onClick={handleSaveToSheets}
                          loading={isSaving}
                          size="sm"
                          variant="primary"
                          glow
                        >
                          Save to Sheets
                        </AnimatedButton>
                      )}
                    </div>
                  </div>
                  <div className="p-4">
                    <ResultsTable
                      leads={leads}
                      isLoading={false}
                      onSaveToSheets={handleSaveToSheets}
                      isSaving={isSaving}
                    />
                  </div>
                </AnimatedCard>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
