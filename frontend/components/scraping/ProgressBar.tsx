// ========================================
// Progress Bar Component - Redesigned with Animations
// ========================================

"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as Progress from "@radix-ui/react-progress";
import { 
  Loader2, 
  Download, 
  CheckCircle2, 
  XCircle, 
  Sparkles,
  Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ScrapeProgress } from "@/types";

interface ProgressBarProps {
  progress: ScrapeProgress;
  className?: string;
}

export function ProgressBar({ progress, className }: ProgressBarProps) {
  const percentage =
    progress.targetCount > 0
      ? Math.round((progress.currentCount / progress.targetCount) * 100)
      : 0;

  const statusConfig = {
    idle: {
      color: "bg-neutral-300",
      gradient: "from-neutral-300 to-neutral-400",
      icon: null,
      text: "text-neutral-600",
    },
    scrolling: {
      color: "bg-primary-500",
      gradient: "from-primary-400 via-primary-500 to-primary-600",
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
      text: "text-primary-600",
    },
    extracting: {
      color: "bg-warning-500",
      gradient: "from-warning-400 via-warning-500 to-warning-600",
      icon: <Download className="w-4 h-4 animate-bounce" />,
      text: "text-warning-600",
    },
    processing: {
      color: "bg-secondary-500",
      gradient: "from-secondary-400 via-secondary-500 to-secondary-600",
      icon: <Sparkles className="w-4 h-4 animate-pulse" />,
      text: "text-secondary-600",
    },
    complete: {
      color: "bg-success-500",
      gradient: "from-success-400 via-success-500 to-success-600",
      icon: <CheckCircle2 className="w-4 h-4" />,
      text: "text-success-600",
    },
    error: {
      color: "bg-error-500",
      gradient: "from-error-400 via-error-500 to-error-600",
      icon: <XCircle className="w-4 h-4" />,
      text: "text-error-600",
    },
  };

  const config = statusConfig[progress.status];

  if (progress.status === "idle") {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={cn("w-full", className)}
    >
      {/* Status header */}
      <div className="flex items-center justify-between mb-3">
        <motion.div 
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-2"
        >
          <div className={cn(
            "p-1.5 rounded-lg",
            progress.status === "complete" ? "bg-success-100" :
            progress.status === "error" ? "bg-error-100" :
            "bg-primary-100"
          )}>
            <span className={config.text}>
              {config.icon}
            </span>
          </div>
          <span className="text-sm font-medium text-neutral-700">
            {progress.message}
          </span>
        </motion.div>
        <motion.div
          key={progress.currentCount}
          initial={{ scale: 1.2, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="flex items-center gap-1"
        >
          <Zap className="w-4 h-4 text-primary-500" />
          <span className="text-sm font-bold text-neutral-900">
            {progress.currentCount}
          </span>
          <span className="text-sm text-neutral-500">
            / {progress.targetCount}
          </span>
        </motion.div>
      </div>

      {/* Progress bar using Radix UI */}
      <Progress.Root
        className="relative h-3 w-full overflow-hidden rounded-full bg-neutral-200"
        value={percentage}
      >
        <Progress.Indicator
          className={cn(
            "h-full rounded-full transition-transform duration-500 ease-out relative overflow-hidden bg-gradient-to-r",
            config.gradient
          )}
          style={{ transform: `translateX(-${100 - percentage}%)` }}
        >
          {/* Animated shimmer effect */}
          <motion.div
            animate={{ x: ["0%", "200%"] }}
            transition={{ 
              duration: 1.5, 
              repeat: Infinity, 
              ease: "linear" 
            }}
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -skew-x-12"
          />
        </Progress.Indicator>
      </Progress.Root>

      {/* Bottom info */}
      <div className="flex items-center justify-between mt-2">
        <div className="flex items-center gap-2">
          {/* Status dots */}
          <div className="flex gap-1">
            {["scrolling", "extracting", "processing", "complete"].map((step, index) => {
              const stepIndex = ["scrolling", "extracting", "processing", "complete"].indexOf(progress.status);
              const isActive = index <= stepIndex;
              const isCurrent = progress.status === step;
              
              return (
                <motion.div
                  key={step}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className={cn(
                    "w-2 h-2 rounded-full transition-colors duration-300",
                    isActive 
                      ? isCurrent 
                        ? statusConfig[step as keyof typeof statusConfig].color 
                        : "bg-success-400"
                      : "bg-neutral-300"
                  )}
                />
              );
            })}
          </div>
        </div>
        <motion.span 
          key={percentage}
          initial={{ scale: 1.1 }}
          animate={{ scale: 1 }}
          className={cn(
            "text-xs font-bold",
            percentage === 100 ? "text-success-600" : "text-neutral-600"
          )}
        >
          {percentage}%
        </motion.span>
      </div>
    </motion.div>
  );
}

export default ProgressBar;
