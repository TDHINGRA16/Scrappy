// ========================================
// Scraping Form Component - Redesigned with Animations
// ========================================

"use client";

import { useState, FormEvent, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Confetti from "react-confetti";
import { 
  Search, 
  MapPin, 
  Target, 
  Sparkles, 
  Loader2,
  Zap,
  CheckCircle2
} from "lucide-react";
import { showToast } from "@/lib/toast";
import { cn } from "@/lib/utils";
import type { ScrapingFormData } from "@/types";

interface ScrapingFormProps {
  onSuccess?: () => void;
  onQueryChange?: (query: string) => void;
  startScrapingAsync: (params: { search_query: string; target_count?: number; headless?: boolean }) => Promise<{ scrape_id: string } | null>;
  isLoading: boolean;
  progress: { status: string; currentCount: number; targetCount: number; message: string };
}

// ========================================
// Animated Input Component
// ========================================

interface AnimatedInputProps {
  label: string;
  icon: React.ReactNode;
  placeholder: string;
  value: string | number;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  helperText?: string;
  type?: string;
  min?: number;
  max?: number;
}

function AnimatedInput({
  label,
  icon,
  placeholder,
  value,
  onChange,
  error,
  helperText,
  type = "text",
  min,
  max,
}: AnimatedInputProps) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-1.5"
    >
      <label className="block text-sm font-medium text-neutral-700">
        {label}
      </label>
      <div className="relative">
        <div className={cn(
          "absolute left-3 top-1/2 -translate-y-1/2 transition-colors duration-200",
          isFocused ? "text-primary-500" : "text-neutral-400"
        )}>
          {icon}
        </div>
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          min={min}
          max={max}
          className={cn(
            "w-full pl-10 pr-4 py-3 rounded-xl border-2 transition-all duration-200",
            "text-neutral-900 placeholder:text-neutral-400",
            "focus:outline-none focus:ring-0",
            isFocused
              ? "border-primary-500 bg-primary-50/30 shadow-sm shadow-primary-500/10"
              : "border-neutral-200 bg-white hover:border-neutral-300",
            error && "border-error-500 bg-error-50/30"
          )}
        />
        {/* Focus glow effect */}
        <AnimatePresence>
          {isFocused && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="absolute inset-0 rounded-xl border-2 border-primary-400/50 pointer-events-none"
              style={{ zIndex: -1 }}
            />
          )}
        </AnimatePresence>
      </div>
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-error-600"
        >
          {error}
        </motion.p>
      )}
      {helperText && !error && (
        <p className="text-sm text-neutral-500">{helperText}</p>
      )}
    </motion.div>
  );
}

// ========================================
// Quick Select Button
// ========================================

interface QuickSelectProps {
  label: string;
  isSelected?: boolean;
  onClick: () => void;
  delay?: number;
}

function QuickSelect({ label, isSelected, onClick, delay = 0 }: QuickSelectProps) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={cn(
        "px-3 py-1.5 text-xs font-medium rounded-full transition-all duration-200",
        isSelected
          ? "bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-sm shadow-primary-500/25"
          : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
      )}
    >
      {label}
    </motion.button>
  );
}

// ========================================
// Main Scraping Form
// ========================================

export function ScrapingForm({ onSuccess, onQueryChange, startScrapingAsync, isLoading, progress }: ScrapingFormProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  const [formData, setFormData] = useState<ScrapingFormData>({
    search_query: "",
    location: "",
    target_count: 50,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Get window size for confetti
  useEffect(() => {
    const updateSize = () => {
      setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    };
    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.search_query.trim()) {
      newErrors.search_query = "Search query is required";
      showToast.error("Please enter a search query");
    }

    if (formData.target_count < 1 || formData.target_count > 500) {
      newErrors.target_count = "Target count must be between 1 and 500";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    console.log("[ScrapingForm] Form submitted");

    if (!validate()) {
      console.log("[ScrapingForm] Validation failed");
      return;
    }

    const searchQuery = formData.location
      ? `${formData.search_query} in ${formData.location}`
      : formData.search_query;

    console.log("[ScrapingForm] Starting scrape with query:", searchQuery);
    showToast.loading("Starting scrape...");
    
    // Notify parent of query change
    if (onQueryChange) {
      onQueryChange(searchQuery);
    }

    // Use async scraping with progress tracking
    const result = await startScrapingAsync({
      search_query: searchQuery,
      target_count: formData.target_count,
      headless: true,
    });

    console.log("[ScrapingForm] Async scraping result:", result);

    showToast.dismiss();

    if (result) {
      // Scrape started successfully - progress will be shown via ScrapeProgress component
      showToast.success(`Scrape started! Tracking progress...`);
      if (onSuccess) onSuccess();
    }
  };

  const popularSearches = [
    { label: "Restaurants", icon: "🍽️" },
    { label: "Hotels", icon: "🏨" },
    { label: "Dentists", icon: "🦷" },
    { label: "Gyms", icon: "💪" },
    { label: "Real Estate", icon: "🏠" },
    { label: "Lawyers", icon: "⚖️" },
  ];

  const targetCounts = [25, 50, 100, 200];

  return (
    <>
      {/* Confetti Effect */}
      {showConfetti && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={200}
          gravity={0.3}
          colors={["#3b82f6", "#a855f7", "#22c55e", "#eab308", "#ef4444"]}
        />
      )}

      <form
        ref={formRef}
        onSubmit={handleSubmit}
        className="space-y-5"
      >
        {/* Search Query */}
        <AnimatedInput
          label="Search Query"
          icon={<Search className="w-4 h-4" />}
          placeholder="e.g., Restaurants, Dentists, Gyms"
          value={formData.search_query}
          onChange={(e) =>
            setFormData({ ...formData, search_query: e.target.value })
          }
          error={errors.search_query}
        />

        {/* Popular Searches */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex flex-wrap gap-2"
        >
          {popularSearches.map((search, index) => (
            <QuickSelect
              key={search.label}
              label={`${search.icon} ${search.label}`}
              isSelected={formData.search_query === search.label}
              onClick={() => setFormData({ ...formData, search_query: search.label })}
              delay={0.1 + index * 0.05}
            />
          ))}
        </motion.div>

        {/* Location */}
        <AnimatedInput
          label="Location (optional)"
          icon={<MapPin className="w-4 h-4" />}
          placeholder="e.g., New York, Los Angeles, Miami"
          value={formData.location}
          onChange={(e) =>
            setFormData({ ...formData, location: e.target.value })
          }
          helperText="Leave empty for general search"
        />

        {/* Target Count */}
        <AnimatedInput
          label="Target Count"
          icon={<Target className="w-4 h-4" />}
          placeholder="50"
          type="number"
          min={1}
          max={500}
          value={formData.target_count}
          onChange={(e) =>
            setFormData({
              ...formData,
              target_count: parseInt(e.target.value) || 50,
            })
          }
          error={errors.target_count}
        />

        {/* Target Count Quick Select */}
        <div className="flex gap-2">
          {targetCounts.map((count, index) => (
            <QuickSelect
              key={count}
              label={count.toString()}
              isSelected={formData.target_count === count}
              onClick={() => setFormData({ ...formData, target_count: count })}
              delay={0.1 + index * 0.05}
            />
          ))}
        </div>

        {/* Submit Button */}
        <motion.button
          type="submit"
          disabled={isLoading}
          whileHover={{ scale: isLoading ? 1 : 1.02 }}
          whileTap={{ scale: isLoading ? 1 : 0.98 }}
          className={cn(
            "w-full relative overflow-hidden rounded-xl py-3.5 px-6 font-semibold text-white transition-all duration-300",
            "bg-gradient-to-r from-primary-500 via-primary-600 to-secondary-500",
            "shadow-lg shadow-primary-500/25",
            "hover:shadow-xl hover:shadow-primary-500/30",
            "disabled:opacity-70 disabled:cursor-not-allowed",
            "group"
          )}
        >
          {/* Shimmer effect */}
          <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          
          <span className="relative flex items-center justify-center gap-2">
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>{progress.message || "Scraping..."}</span>
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                <span>Start Scraping</span>
              </>
            )}
          </span>
        </motion.button>

        {/* Progress Status */}
        <AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="bg-primary-50 rounded-xl p-4 border border-primary-200">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-1.5 bg-primary-100 rounded-lg">
                    <Sparkles className="w-4 h-4 text-primary-600 animate-pulse" />
                  </div>
                  <span className="text-sm font-medium text-primary-900">
                    {progress.message}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-primary-700">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>
                    {progress.currentCount} / {progress.targetCount} leads found
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </form>
    </>
  );
}

export default ScrapingForm;
