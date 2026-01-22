// ========================================
// Animated Button Component
// ========================================

"use client";

import { forwardRef } from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface AnimatedButtonProps
  extends Omit<HTMLMotionProps<"button">, "children"> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg" | "xl";
  loading?: boolean;
  icon?: React.ReactNode;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  iconPosition?: "left" | "right";
  children: React.ReactNode;
  fullWidth?: boolean;
  glow?: boolean;
}

const variants = {
  primary:
    "bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30",
  secondary:
    "bg-secondary-600 text-white hover:bg-secondary-700 shadow-lg shadow-secondary-500/25 hover:shadow-xl hover:shadow-secondary-500/30",
  outline:
    "border-2 border-primary-600 text-primary-600 hover:bg-primary-50 bg-transparent",
  ghost:
    "text-neutral-700 hover:bg-neutral-100 bg-transparent",
  danger:
    "bg-error-500 text-white hover:bg-error-600 shadow-lg shadow-error-500/25",
};

const sizes = {
  sm: "px-3 py-1.5 text-sm gap-1.5",
  md: "px-5 py-2.5 text-base gap-2",
  lg: "px-6 py-3 text-lg gap-2.5",
  xl: "px-8 py-4 text-xl gap-3",
};

const iconSizes = {
  sm: "w-4 h-4",
  md: "w-4 h-4",
  lg: "w-5 h-5",
  xl: "w-6 h-6",
};

export const AnimatedButton = forwardRef<HTMLButtonElement, AnimatedButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      icon,
      leftIcon,
      rightIcon,
      iconPosition = "left",
      children,
      className,
      disabled,
      fullWidth = false,
      glow = false,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;
    // Determine which icons to render without forwarding non-standard props
    const renderLeftIcon = leftIcon ?? (icon && iconPosition === "left" ? icon : null);
    const renderRightIcon = rightIcon ?? (icon && iconPosition === "right" ? icon : null);

    return (
      <motion.button
        ref={ref}
        whileHover={isDisabled ? undefined : { scale: 1.02 }}
        whileTap={isDisabled ? undefined : { scale: 0.98 }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
        className={cn(
          // Base styles
          "relative inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2",
          // Variant styles
          variants[variant],
          // Size styles
          sizes[size],
          // Full width
          fullWidth && "w-full",
          // Glow effect
          glow && variant === "primary" && "shadow-glow hover:shadow-glow-lg",
          glow && variant === "secondary" && "shadow-glow-secondary",
          className
        )}
        disabled={isDisabled}
        {...props}
      >
        {/* Loading spinner */}
        {loading && (
          <Loader2 className={cn("animate-spin", iconSizes[size])} />
        )}
        
        {/* Left icon */}
        {!loading && renderLeftIcon && (
          <span className={iconSizes[size]}>{renderLeftIcon}</span>
        )}
        
        {/* Button text */}
        <span>{children}</span>
        
        {/* Right icon */}
        {!loading && renderRightIcon && (
          <span className={iconSizes[size]}>{renderRightIcon}</span>
        )}

        {/* Shimmer overlay effect */}
        <motion.div
          className="absolute inset-0 rounded-xl overflow-hidden pointer-events-none"
          initial={false}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full"
            whileHover={{ x: "200%" }}
            transition={{ duration: 0.6, ease: "easeInOut" }}
          />
        </motion.div>
      </motion.button>
    );
  }
);

AnimatedButton.displayName = "AnimatedButton";

export default AnimatedButton;
