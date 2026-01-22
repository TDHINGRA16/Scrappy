// ========================================
// Animated Card Component
// ========================================

"use client";

import { forwardRef } from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

export interface AnimatedCardProps extends HTMLMotionProps<"div"> {
  hover?: boolean;
  delay?: number;
  variant?: "default" | "bordered" | "elevated" | "glass";
  padding?: "none" | "sm" | "md" | "lg";
}

const cardVariants = {
  default: "bg-white border border-neutral-200",
  bordered: "bg-white border-2 border-neutral-300",
  elevated: "bg-white shadow-lg border border-neutral-100",
  glass: "bg-white/70 backdrop-blur-lg border border-white/20",
};

const paddingVariants = {
  none: "",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

export const AnimatedCard = forwardRef<HTMLDivElement, AnimatedCardProps>(
  (
    {
      children,
      className,
      hover = true,
      delay = 0,
      variant = "default",
      padding = "md",
      ...props
    },
    ref
  ) => {
    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
          duration: 0.5,
          delay,
          ease: [0.25, 0.1, 0.25, 1],
        }}
        whileHover={
          hover
            ? {
                y: -4,
                boxShadow: "0 20px 40px rgba(0,0,0,0.1)",
                transition: { duration: 0.2 },
              }
            : undefined
        }
        className={cn(
          "rounded-xl transition-all duration-200",
          cardVariants[variant],
          paddingVariants[padding],
          hover && "cursor-pointer",
          className
        )}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

AnimatedCard.displayName = "AnimatedCard";

export default AnimatedCard;
