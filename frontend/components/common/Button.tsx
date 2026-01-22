// ========================================
// Button Component - Updated Styling
// ========================================

"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";
import type { ButtonProps } from "@/types";

const buttonVariants = {
  primary:
    "bg-gradient-to-r from-primary-600 to-primary-700 text-white hover:from-primary-700 hover:to-primary-800 focus:ring-primary-500 shadow-md hover:shadow-lg",
  secondary:
    "bg-gradient-to-r from-neutral-600 to-neutral-700 text-white hover:from-neutral-700 hover:to-neutral-800 focus:ring-neutral-500 shadow-md hover:shadow-lg",
  outline:
    "border-2 border-primary-600 text-primary-600 hover:bg-primary-50 focus:ring-primary-500",
  ghost:
    "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 focus:ring-neutral-500",
  danger:
    "bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 focus:ring-red-500 shadow-md hover:shadow-lg",
};

const buttonSizes = {
  sm: "px-3.5 py-1.5 text-sm",
  md: "px-5 py-2.5 text-base",
  lg: "px-7 py-3.5 text-lg",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled = false,
      className,
      onClick,
      type = "button",
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || isLoading}
        onClick={onClick}
        className={cn(
          "inline-flex items-center justify-center font-medium rounded-lg",
          "transition-all duration-200 ease-in-out",
          "focus:outline-none focus:ring-2 focus:ring-offset-2",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          buttonVariants[variant],
          buttonSizes[size],
          className
        )}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
