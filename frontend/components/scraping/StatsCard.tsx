// ========================================
// Stats Card Component - Redesigned with Animations
// ========================================

"use client";

import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown } from "lucide-react";
import { useCounterAnimation, useCardHover } from "@/hooks/useAnimation";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  change?: {
    value: number;
    type: "increase" | "decrease";
  };
  className?: string;
  accentColor?: "primary" | "secondary" | "success" | "warning" | "error";
}

const accentStyles = {
  primary: "from-primary-500 to-primary-600",
  secondary: "from-secondary-500 to-secondary-600",
  success: "from-green-500 to-emerald-600",
  warning: "from-amber-500 to-orange-600",
  error: "from-red-500 to-rose-600",
};

const iconBgStyles = {
  primary: "from-primary-500/10 to-primary-600/10",
  secondary: "from-secondary-500/10 to-secondary-600/10",
  success: "from-green-500/10 to-emerald-600/10",
  warning: "from-amber-500/10 to-orange-600/10",
  error: "from-red-500/10 to-rose-600/10",
};

const iconTextStyles = {
  primary: "text-primary-600",
  secondary: "text-secondary-600",
  success: "text-green-600",
  warning: "text-amber-600",
  error: "text-red-600",
};

export function StatsCard({ 
  title, 
  value, 
  icon, 
  change, 
  className,
  accentColor = "primary"
}: StatsCardProps) {
  const { ref, onMouseEnter, onMouseLeave } = useCardHover();
  const counterRef = useCounterAnimation(value);

  return (
    <motion.div
      ref={ref}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      className={cn(
        "relative bg-white/80 backdrop-blur-sm rounded-2xl border border-neutral-200/50 p-6 transition-all duration-300 overflow-hidden group",
        "hover:shadow-lg hover:shadow-neutral-200/50 hover:border-neutral-300/50",
        className
      )}
    >
      {/* Gradient accent bar */}
      <div className={cn(
        "absolute top-0 left-0 right-0 h-1 bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity",
        accentStyles[accentColor]
      )} />
      
      {/* Background decoration */}
      <div className="absolute -top-12 -right-12 w-24 h-24 bg-gradient-to-br from-neutral-100/50 to-transparent rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="relative flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-neutral-500">{title}</p>
          <p className="text-3xl font-bold text-neutral-900 mt-2">
            <span ref={counterRef}>0</span>
          </p>
          {change && (
            <div className="flex items-center gap-1.5 mt-2">
              <span
                className={cn(
                  "flex items-center gap-0.5 text-sm font-semibold",
                  change.type === "increase" ? "text-green-600" : "text-red-500"
                )}
              >
                {change.type === "increase" ? (
                  <TrendingUp className="w-3.5 h-3.5" />
                ) : (
                  <TrendingDown className="w-3.5 h-3.5" />
                )}
                {Math.abs(change.value)}%
              </span>
              <span className="text-xs text-neutral-400">vs last week</span>
            </div>
          )}
        </div>
        <div className={cn(
          "p-3.5 bg-gradient-to-br rounded-xl transition-transform group-hover:scale-110",
          iconBgStyles[accentColor],
          iconTextStyles[accentColor]
        )}>
          {icon}
        </div>
      </div>
    </motion.div>
  );
}

export default StatsCard;
