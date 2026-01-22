// ========================================
// Signup Form Component - Redesigned with Animations
// ========================================

"use client";

import { useState, FormEvent, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Confetti from "react-confetti";
import { 
  User, 
  Mail, 
  Lock, 
  ArrowRight, 
  AlertCircle, 
  Sparkles,
  CheckCircle2,
  Shield
} from "lucide-react";
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
  helperText?: string;
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
  helperText,
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
      {helperText && !error && (
        <p className="text-sm text-neutral-500">{helperText}</p>
      )}
    </motion.div>
  );
}

// ========================================
// Password Strength Indicator
// ========================================

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: "8+ characters", valid: password.length >= 8 },
    { label: "Lowercase", valid: /[a-z]/.test(password) },
    { label: "Uppercase", valid: /[A-Z]/.test(password) },
    { label: "Number", valid: /[0-9]/.test(password) },
  ];

  const strength = checks.filter(c => c.valid).length;

  return (
    <div className="space-y-2">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((level) => (
          <div
            key={level}
            className={cn(
              "h-1 flex-1 rounded-full transition-colors duration-300",
              strength >= level
                ? strength <= 1 ? "bg-error-500"
                : strength === 2 ? "bg-warning-500"
                : strength === 3 ? "bg-primary-500"
                : "bg-success-500"
                : "bg-neutral-200"
            )}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {checks.map((check) => (
          <span
            key={check.label}
            className={cn(
              "text-xs flex items-center gap-1 transition-colors",
              check.valid ? "text-success-600" : "text-neutral-400"
            )}
          >
            <CheckCircle2 className={cn(
              "w-3 h-3",
              check.valid ? "opacity-100" : "opacity-30"
            )} />
            {check.label}
          </span>
        ))}
      </div>
    </div>
  );
}

// ========================================
// Main Signup Form
// ========================================

export function SignupForm() {
  const router = useRouter();
  const { signUp, isLoading } = useAuth();
  const formRef = useRef<HTMLFormElement>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Get window size for confetti
  useState(() => {
    if (typeof window !== "undefined") {
      setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    }
  });

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name) {
      newErrors.name = "Name is required";
    } else if (formData.name.length < 2) {
      newErrors.name = "Name must be at least 2 characters";
    }

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = "Invalid email format";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!validate()) return;

    const result = await signUp(formData.email, formData.password, formData.name);

    if (result.error) {
      setSubmitError(result.error);
      showToast.error(result.error);
    } else {
      setShowConfetti(true);
      showToast.success("Account created! Welcome to Scrappy! 🎉");
      setTimeout(() => {
        router.push("/dashboard");
      }, 2000);
    }
  };

  return (
    <>
      {/* Confetti Effect */}
      {showConfetti && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={300}
          gravity={0.2}
          colors={["#3b82f6", "#a855f7", "#22c55e", "#eab308", "#ef4444"]}
        />
      )}

      <motion.form
        ref={formRef}
        onSubmit={handleSubmit}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="space-y-5 w-full max-w-md mx-auto"
      >
        {/* Header */}
        <motion.div 
          className="text-center mb-8"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-success-100 text-success-700 text-sm font-medium mb-4">
            <Sparkles className="w-4 h-4" />
            Free to get started
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-neutral-900 to-neutral-600 bg-clip-text text-transparent">
            Create your account
          </h1>
          <p className="text-neutral-600 mt-2">
            Start generating leads in minutes
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
            label="Full Name"
            icon={<User className="w-4 h-4" />}
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={errors.name}
            placeholder="John Doe"
            autoComplete="name"
          />

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
            autoComplete="new-password"
          />

          {formData.password && <PasswordStrength password={formData.password} />}

          <AnimatedInput
            label="Confirm Password"
            icon={<Shield className="w-4 h-4" />}
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            error={errors.confirmPassword}
            placeholder="••••••••"
            autoComplete="new-password"
          />
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            required
            className="w-4 h-4 mt-0.5 text-primary-600 border-neutral-300 rounded focus:ring-primary-500 transition-colors"
          />
          <span className="ml-2 text-sm text-neutral-600">
            I agree to the{" "}
            <Link href="/terms" className="text-primary-600 hover:text-primary-700 font-medium">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/privacy" className="text-primary-600 hover:text-primary-700 font-medium">
              Privacy Policy
            </Link>
          </span>
        </div>

        <AnimatedButton
          type="submit"
          loading={isLoading}
          className="w-full"
          size="lg"
          glow
        >
          Create Account
          <ArrowRight className="w-5 h-5 ml-2" />
        </AnimatedButton>

        <motion.p 
          className="text-center text-neutral-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          Already have an account?{" "}
          <Link
            href="/auth/login"
            className="text-primary-600 hover:text-primary-700 font-semibold transition-colors"
          >
            Sign in
          </Link>
        </motion.p>
      </motion.form>
    </>
  );
}

export default SignupForm;
