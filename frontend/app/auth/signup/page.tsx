// ========================================
// Signup Page - Redesigned with Modern Styling
// ========================================

import { SignupForm } from "@/components/auth/SignupForm";
import { Header } from "@/components/layout/Header";

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-white to-secondary-50/30 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-0 w-[600px] h-[600px] bg-secondary-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-primary-500/5 rounded-full blur-3xl" />
      </div>

      <Header />
      <main className="relative flex items-center justify-center py-12 px-4">
        <div className="w-full max-w-md">
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-neutral-200/50 p-8 border border-neutral-200/60">
            <SignupForm />
          </div>
        </div>
      </main>
    </div>
  );
}
