// ========================================
// Input Component - Updated Styling
// ========================================

"use client";

import { forwardRef, InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import type { InputProps } from "@/types";

type CombinedInputProps = InputProps & InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, CombinedInputProps>(
  ({ label, error, helperText, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-neutral-700 mb-1.5"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            "w-full px-4 py-2.5 border rounded-xl",
            "bg-white/50 backdrop-blur-sm",
            "transition-all duration-200",
            "focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500",
            "placeholder:text-neutral-400",
            error
              ? "border-red-400 focus:ring-red-500/20 focus:border-red-500"
              : "border-neutral-200 hover:border-neutral-300",
            "disabled:bg-neutral-50 disabled:cursor-not-allowed disabled:opacity-60",
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1.5 text-sm text-red-600 flex items-center gap-1">
            <span className="inline-block w-1 h-1 bg-red-500 rounded-full"></span>
            {error}
          </p>
        )}
        {helperText && !error && (
          <p className="mt-1.5 text-sm text-neutral-500">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;
