'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Types
interface ProgressStats {
  cards_found: number;
  cards_extracted: number;
  unique_results: number;
  scrolls_done: number;
  max_scrolls: number;
  target_count: number;
  extraction_errors: number;
  time_elapsed: string;
  eta: string;
}

interface SampleResult {
  name: string;
  address?: string;
  phone?: string;
  rating?: number;
  reviews_count?: number;
  category?: string;
}

interface ProgressData {
  scrape_id: string;
  status: 'starting' | 'scrolling' | 'extracting' | 'completed' | 'failed';
  progress_percent: number;
  phase: string;
  stats: ProgressStats;
  preview: SampleResult[];
  sample_result: SampleResult | null;
  error_message?: string;
}

interface ScrapeProgressProps {
  scrapeId: string;
  query: string;
  onComplete: (results: any[]) => void;
  onError: (error: string) => void;
}

// Stat Card Component
const StatCard = ({ 
  title, 
  value, 
  icon, 
  animate = true 
}: { 
  title: string; 
  value: string | number; 
  icon: string;
  animate?: boolean;
}) => (
  <motion.div
    initial={animate ? { scale: 0.8, opacity: 0 } : {}}
    animate={{ scale: 1, opacity: 1 }}
    className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700"
  >
    <div className="flex items-center gap-3">
      <span className="text-2xl">{icon}</span>
      <div>
        <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">{title}</p>
        <motion.p 
          key={value}
          initial={{ scale: 1.2 }}
          animate={{ scale: 1 }}
          className="text-xl font-bold text-gray-900 dark:text-white"
        >
          {value}
        </motion.p>
      </div>
    </div>
  </motion.div>
);

// Business Card Preview Component
const BusinessCardPreview = ({ data }: { data: SampleResult }) => (
  <motion.div
    initial={{ x: 50, opacity: 0 }}
    animate={{ x: 0, opacity: 1 }}
    exit={{ x: -50, opacity: 0 }}
    className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-4 border border-green-200 dark:border-green-800"
  >
    <div className="flex items-start gap-3">
      <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center text-white font-bold text-lg">
        {data.name?.charAt(0) || '?'}
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold text-gray-900 dark:text-white truncate">
          {data.name || 'Unknown Business'}
        </h4>
        {data.category && (
          <p className="text-sm text-gray-500 dark:text-gray-400">{data.category}</p>
        )}
        <div className="flex items-center gap-2 mt-1">
          {data.rating && (
            <span className="text-sm">⭐ {data.rating}</span>
          )}
          {data.reviews_count && (
            <span className="text-xs text-gray-400">({data.reviews_count} reviews)</span>
          )}
        </div>
        {data.address && (
          <p className="text-xs text-gray-400 mt-1 truncate">📍 {data.address}</p>
        )}
      </div>
    </div>
  </motion.div>
);

// Main Progress Component
export default function ScrapeProgress({ 
  scrapeId, 
  query, 
  onComplete, 
  onError 
}: ScrapeProgressProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  
  // Use refs for callbacks to avoid useEffect dependency issues
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  
  // Keep refs updated
  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onComplete, onError]);
  
  // Backend URL - use environment variable or default to localhost
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  // Poll for progress updates
  useEffect(() => {
    if (!scrapeId || !isPolling) return;

    console.log('[ScrapeProgress] Starting polling for scrapeId:', scrapeId);

    const pollProgress = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/scrape/${scrapeId}/progress`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch progress');
        }
        
        const data: ProgressData = await response.json();
        setProgress(data);

        // Handle completion
        if (data.status === 'completed') {
          console.log('[ScrapeProgress] Scrape completed, fetching results...');
          setIsPolling(false);
          // Fetch final results
          const resultsResponse = await fetch(`${backendUrl}/api/scrape/${scrapeId}/results`);
          console.log('[ScrapeProgress] Results response status:', resultsResponse.status);
          
          if (resultsResponse.ok) {
            const resultsData = await resultsResponse.json();
            console.log('[ScrapeProgress] Results received:', resultsData.results?.length || 0, 'items');
            console.log('[ScrapeProgress] First result sample:', resultsData.results?.[0]);
            onCompleteRef.current(resultsData.results || []);
          } else {
            // Use preview results as fallback
            console.log('[ScrapeProgress] Using fallback preview data:', data.preview?.length || 0, 'items');
            onCompleteRef.current(data.preview || []);
          }
        } else if (data.status === 'failed') {
          console.log('[ScrapeProgress] Scrape failed:', data.error_message);
          setIsPolling(false);
          onErrorRef.current(data.error_message || 'Scraping failed');
        }
      } catch (error) {
        console.error('[ScrapeProgress] Polling error:', error);
        // Don't stop polling on temporary errors
      }
    };

    // Initial poll
    pollProgress();

    // Poll every 500ms
    const interval = setInterval(pollProgress, 500);

    return () => {
      console.log('[ScrapeProgress] Cleaning up polling interval');
      clearInterval(interval);
    };
  }, [scrapeId, isPolling, backendUrl]);

  // Loading state
  if (!progress) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full"
        />
        <p className="mt-4 text-gray-500">Starting scrape...</p>
      </div>
    );
  }

  const { status, progress_percent, phase, stats, sample_result } = progress;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-4xl mx-auto"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Scraping &ldquo;{query}&rdquo;
          </h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
            {phase}
          </p>
        </div>
        <motion.div
          className="relative"
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center shadow-lg">
            <span className="text-2xl font-bold text-white">
              {progress_percent}%
            </span>
          </div>
          {status === 'extracting' && (
            <motion.div
              className="absolute inset-0 rounded-full border-4 border-green-400"
              animate={{ scale: [1, 1.2, 1], opacity: [1, 0, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          )}
        </motion.div>
      </div>

      {/* Progress Bar */}
      <div className="relative mb-8">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden shadow-inner">
          <motion.div
            className="h-full bg-gradient-to-r from-green-400 via-emerald-500 to-green-600 relative"
            initial={{ width: 0 }}
            animate={{ width: `${progress_percent}%` }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          >
            {/* Animated shine effect */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
              animate={{ x: ['-100%', '200%'] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            />
            {/* Glow effect */}
            <motion.div
              className="absolute inset-0"
              animate={{ 
                boxShadow: [
                  '0 0 10px rgba(34, 197, 94, 0.3)',
                  '0 0 20px rgba(34, 197, 94, 0.6)',
                  '0 0 10px rgba(34, 197, 94, 0.3)'
                ]
              }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </motion.div>
        </div>
        
        {/* Phase indicators */}
        <div className="flex justify-between mt-2 text-xs text-gray-400">
          <span className={status === 'starting' ? 'text-green-500 font-medium' : ''}>Starting</span>
          <span className={status === 'scrolling' ? 'text-green-500 font-medium' : ''}>Scrolling</span>
          <span className={status === 'extracting' ? 'text-green-500 font-medium' : ''}>Extracting</span>
          <span className={status === 'completed' ? 'text-green-500 font-medium' : ''}>Complete</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard 
          title="Found" 
          value={stats.cards_found} 
          icon="📍" 
        />
        <StatCard 
          title="Extracted" 
          value={stats.cards_extracted} 
          icon="✅" 
        />
        <StatCard 
          title="Time" 
          value={stats.time_elapsed} 
          icon="⏱️" 
        />
        <StatCard 
          title="ETA" 
          value={stats.eta} 
          icon="🔮" 
        />
      </div>

      {/* Additional Stats Row */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard 
          title="Unique Results" 
          value={stats.unique_results} 
          icon="⭐" 
        />
        <StatCard 
          title="Scrolls" 
          value={`${stats.scrolls_done}/${stats.max_scrolls}`} 
          icon="📜" 
        />
        <StatCard 
          title="Errors" 
          value={stats.extraction_errors} 
          icon="⚠️" 
        />
      </div>

      {/* Live Preview */}
      <AnimatePresence mode="wait">
        {sample_result && sample_result.name && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 flex items-center gap-2">
              <motion.span
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                🔴
              </motion.span>
              Latest Business Found
            </h3>
            <BusinessCardPreview data={sample_result} />
          </div>
        )}
      </AnimatePresence>

      {/* Preview List */}
      {progress.preview && progress.preview.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
            Preview ({progress.preview.length} results)
          </h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {progress.preview.slice(0, 5).map((result, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
              >
                <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center text-sm">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 dark:text-white truncate">
                    {result.name}
                  </p>
                  {result.rating && (
                    <p className="text-xs text-gray-500">⭐ {result.rating}</p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Status Messages */}
      <motion.div
        className="mt-6 text-center text-sm text-gray-500"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        {status === 'scrolling' && '🔄 Finding more businesses...'}
        {status === 'extracting' && '⚡ Extracting business details...'}
        {status === 'completed' && '🎉 All done!'}
        {status === 'failed' && `❌ ${progress.error_message || 'Something went wrong'}`}
      </motion.div>
    </motion.div>
  );
}
