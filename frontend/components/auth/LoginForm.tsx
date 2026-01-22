// ========================================
// Login Form Component - Redesigned with Animations
// ========================================

"use client";

import { useState, FormEvent, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, Lock, ArrowRight, AlertCircle, Sparkles } from "lucide-react";
import { AnimatedButton } from "@/components/ui/animated-button";
import { useAuth } from "@/hooks/useAuth";
import { showToast } from "@/lib/toast";
import { isValidEmail, cn } from "@/lib/utils";

// ========================================
// Animated Input Component
// ========================================

interface AnimatedInputProps {
  label: string;
  icon: React.ReactNode;
  type?: string;
  placeholder: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  autoComplete?: string;
}

function AnimatedInput({
  label,
  icon,
  type = "text",
  placeholder,
  value,
  onChange,
  error,
  autoComplete,
}: AnimatedInputProps) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-1.5"
    >
      <label className="block text-sm font-medium text-neutral-700">
        {label}
      </label>
      <div className="relative">
        <div className={cn(
          "absolute left-3 top-1/2 -translate-y-1/2 transition-colors duration-200",
          isFocused ? "text-primary-500" : "text-neutral-400"
        )}>
          {icon}
        </div>
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          autoComplete={autoComplete}
          className={cn(
            "w-full pl-10 pr-4 py-3 rounded-xl border-2 transition-all duration-200",
            "text-neutral-900 placeholder:text-neutral-400",
            "focus:outline-none focus:ring-0",
            isFocused
              ? "border-primary-500 bg-primary-50/30 shadow-sm shadow-primary-500/10"
              : "border-neutral-200 bg-white hover:border-neutral-300",
            error && "border-error-500 bg-error-50/30"
          )}
        />
      </div>
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-error-600 flex items-center gap-1"
        >
          <AlertCircle className="w-3.5 h-3.5" />
          {error}
        </motion.p>
      )}
    </motion.div>
  );
}

// ========================================
// Main Login Form
// ========================================

export function LoginForm() {
  const router = useRouter();
  const { signIn, isLoading } = useAuth();
  const formRef = useRef<HTMLFormElement>(null);

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = "Invalid email format";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!validate()) return;

    const result = await signIn(formData.email, formData.password);

    if (result.error) {
      setSubmitError(result.error);
      showToast.error(result.error);
    } else {
      showToast.success("Welcome back! 👋");
      router.push("/dashboard");
    }
  };

  return (
    <motion.form
      ref={formRef}
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6 w-full max-w-md mx-auto"
    >
      {/* Header */}
      <motion.div 
        className="text-center mb-8"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-100 text-primary-700 text-sm font-medium mb-4">
          <Sparkles className="w-4 h-4" />
          Welcome back
        </div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-neutral-900 to-neutral-600 bg-clip-text text-transparent">
          Sign in to Scrappy
        </h1>
        <p className="text-neutral-600 mt-2">
          Continue your lead generation journey
        </p>
      </motion.div>

      {/* Error Alert */}
      <AnimatePresence>
        {submitError && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-error-50 border border-error-200 text-error-700 px-4 py-3 rounded-xl flex items-center gap-3"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{submitError}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="space-y-4">
        <AnimatedInput
          label="Email"
          icon={<Mail className="w-4 h-4" />}
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          error={errors.email}
          placeholder="you@example.com"
          autoComplete="email"
        />

        <AnimatedInput
          label="Password"
          icon={<Lock className="w-4 h-4" />}
          type="password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          error={errors.password}
          placeholder="••••••••"
          autoComplete="current-password"
        />
      </div>

      <div className="flex items-center justify-between">
        <label className="flex items-center cursor-pointer group">
          <input
            type="checkbox"
            className="w-4 h-4 text-primary-600 border-neutral-300 rounded focus:ring-primary-500 transition-colors"
          />
          <span className="ml-2 text-sm text-neutral-600 group-hover:text-neutral-900 transition-colors">
            Remember me
          </span>
        </label>
        <Link
          href="/auth/forgot-password"
          className="text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
        >
          Forgot password?
        </Link>
      </div>

      <AnimatedButton
        type="submit"
        loading={isLoading}
        className="w-full"
        size="lg"
        glow
      >
        Sign In
        <ArrowRight className="w-5 h-5 ml-2" />
      </AnimatedButton>

      <motion.p 
        className="text-center text-neutral-600"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        Don&apos;t have an account?{" "}
        <Link
          href="/auth/signup"
          className="text-primary-600 hover:text-primary-700 font-semibold transition-colors"
        >
          Sign up for free
        </Link>
      </motion.p>
    </motion.form>
  );
}

export default LoginForm;
