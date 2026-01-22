// ========================================
// Skeleton Loading Component
// ========================================

"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
  animate?: boolean;
}

export function Skeleton({
  className,
  variant = "text",
  width,
  height,
  animate = true,
}: SkeletonProps) {
  const variantStyles = {
    text: "rounded",
    circular: "rounded-full",
    rectangular: "rounded-lg",
  };

  return (
    <div
      className={cn(
        "bg-gray-200",
        animate && "animate-pulse",
        variantStyles[variant],
        className
      )}
      style={{
        width: width,
        height: height || (variant === "text" ? "1em" : undefined),
      }}
    />
  );
}

// Table Skeleton
export function TableSkeleton({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div className="w-full overflow-hidden rounded-lg border border-gray-200">
      {/* Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          className="px-4 py-3 border-b border-gray-100 last:border-0"
        >
          <div className="flex gap-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton key={colIndex} className="h-4 flex-1" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// Card Skeleton
export function CardSkeleton() {
  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-200">
      <Skeleton className="h-6 w-3/4 mb-4" />
      <Skeleton className="h-4 w-full mb-2" />
      <Skeleton className="h-4 w-5/6 mb-4" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-20" variant="rectangular" />
        <Skeleton className="h-8 w-20" variant="rectangular" />
      </div>
    </div>
  );
}

// Form Skeleton
export function FormSkeleton({ fields = 3 }: { fields?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i}>
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-10 w-full" variant="rectangular" />
        </div>
      ))}
      <Skeleton className="h-10 w-32 mt-4" variant="rectangular" />
    </div>
  );
}

export default Skeleton;
