// ========================================
// Empty State Component
// ========================================

"use client";

import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { AnimatedButton } from "./animated-button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeVariants = {
  sm: {
    container: "py-12 px-4",
    iconWrapper: "w-14 h-14 mb-4",
    icon: "w-7 h-7",
    title: "text-lg",
    description: "text-sm max-w-sm",
  },
  md: {
    container: "py-20 px-4",
    iconWrapper: "w-20 h-20 mb-6",
    icon: "w-10 h-10",
    title: "text-2xl",
    description: "text-base max-w-md",
  },
  lg: {
    container: "py-28 px-4",
    iconWrapper: "w-24 h-24 mb-8",
    icon: "w-12 h-12",
    title: "text-3xl",
    description: "text-lg max-w-lg",
  },
};

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  secondaryAction,
  size = "md",
  className,
}: EmptyStateProps) {
  const styles = sizeVariants[size];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={cn(
        "flex flex-col items-center justify-center text-center",
        styles.container,
        className
      )}
    >
      {/* Animated Icon */}
      <motion.div
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{
          delay: 0.2,
          type: "spring",
          stiffness: 200,
          damping: 15,
        }}
        className={cn(
          "rounded-full bg-gradient-to-br from-primary-100 to-secondary-100",
          "flex items-center justify-center",
          styles.iconWrapper
        )}
      >
        <Icon className={cn("text-primary-600", styles.icon)} />
      </motion.div>

      {/* Title */}
      <motion.h3
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className={cn(
          "font-semibold text-neutral-900 mb-2",
          styles.title
        )}
      >
        {title}
      </motion.h3>

      {/* Description */}
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className={cn(
          "text-neutral-600 mb-6",
          styles.description
        )}
      >
        {description}
      </motion.p>

      {/* Actions */}
      {(action || secondaryAction) && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex flex-col sm:flex-row gap-3"
        >
          {action && (
            <AnimatedButton
              onClick={action.onClick}
              icon={action.icon}
              size={size === "lg" ? "lg" : "md"}
            >
              {action.label}
            </AnimatedButton>
          )}
          {secondaryAction && (
            <AnimatedButton
              variant="outline"
              onClick={secondaryAction.onClick}
              size={size === "lg" ? "lg" : "md"}
            >
              {secondaryAction.label}
            </AnimatedButton>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}

export default EmptyState;
