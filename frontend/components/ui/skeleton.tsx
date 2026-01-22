// ========================================
// Enhanced Skeleton Loading Components
// ========================================

"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular" | "rounded";
  animate?: boolean;
}

export function Skeleton({ 
  className, 
  variant = "rectangular",
  animate = true 
}: SkeletonProps) {
  return (
    <div
      className={cn(
        "bg-neutral-200",
        animate && "skeleton-shimmer",
        variant === "text" && "h-4 rounded",
        variant === "circular" && "rounded-full",
        variant === "rectangular" && "rounded-lg",
        variant === "rounded" && "rounded-xl",
        className
      )}
    />
  );
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          className={cn(
            "h-4",
            i === lines - 1 ? "w-2/3" : "w-full"
          )}
        />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="p-6 bg-white rounded-xl border border-neutral-200 space-y-4">
      <div className="flex items-start justify-between">
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
      <div className="flex gap-3 pt-2">
        <Skeleton className="h-10 w-24 rounded-lg" />
        <Skeleton className="h-10 w-24 rounded-lg" />
      </div>
    </div>
  );
}

export function SkeletonTable({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden">
      {/* Header */}
      <div className="bg-neutral-50 border-b border-neutral-200 p-4">
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton
              key={i}
              className="h-4 flex-1"
            />
          ))}
        </div>
      </div>
      {/* Rows */}
      <div className="divide-y divide-neutral-200">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="p-4 flex gap-4">
            {Array.from({ length: columns }).map((_, j) => (
              <Skeleton
                key={j}
                className="h-4 flex-1"
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function SkeletonAvatar({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: "w-8 h-8",
    md: "w-10 h-10",
    lg: "w-12 h-12",
  };

  return (
    <Skeleton
      variant="circular"
      className={sizeClasses[size]}
    />
  );
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="p-6 bg-white rounded-xl border border-neutral-200"
        >
          <div className="flex items-start justify-between">
            <div className="space-y-2 flex-1">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-20" />
            </div>
            <Skeleton className="h-12 w-12 rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SkeletonDashboard() {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Stats row */}
      <SkeletonStats />
      
      {/* Two column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
      
      {/* Table */}
      <SkeletonTable rows={5} columns={5} />
    </div>
  );
}

export default Skeleton;
