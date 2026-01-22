// ========================================
// Header Component - Redesigned with Animations
// ========================================

"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Search, 
  Menu, 
  X, 
  LogOut, 
  User,
  Zap,
  LayoutDashboard,
  History,
  Settings
} from "lucide-react";
import { AnimatedButton } from "@/components/ui/animated-button";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

export function Header() {
  const router = useRouter();
  const { user, isAuthenticated, signOut, isLoading } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleSignOut = async () => {
    await signOut();
    router.push("/");
  };

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="sticky top-0 z-40 w-full bg-white/80 backdrop-blur-lg border-b border-neutral-200/50"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <motion.div 
              whileHover={{ scale: 1.05, rotate: 5 }}
              whileTap={{ scale: 0.95 }}
              className="w-9 h-9 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/25"
            >
              <Zap className="w-5 h-5 text-white" />
            </motion.div>
            <span className="text-xl font-bold bg-gradient-to-r from-neutral-900 to-neutral-600 bg-clip-text text-transparent group-hover:from-primary-600 group-hover:to-secondary-600 transition-all duration-300">
              Scrappy
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {isAuthenticated ? (
              <>
                <NavLink href="/dashboard" icon={<LayoutDashboard className="w-4 h-4" />}>
                  Dashboard
                </NavLink>
                <NavLink href="/dashboard/history" icon={<History className="w-4 h-4" />}>
                  History
                </NavLink>
                <NavLink href="/dashboard/settings" icon={<Settings className="w-4 h-4" />}>
                  Settings
                </NavLink>
              </>
            ) : (
              <>
                <NavLink href="/features">Features</NavLink>
                <NavLink href="/pricing">Pricing</NavLink>
              </>
            )}
          </nav>

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-neutral-100 rounded-full">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
                    <User className="w-3.5 h-3.5 text-white" />
                  </div>
                  <span className="text-sm font-medium text-neutral-700">
                    {user?.name || user?.email?.split("@")[0]}
                  </span>
                </div>
                <AnimatedButton
                  variant="ghost"
                  size="sm"
                  onClick={handleSignOut}
                  loading={isLoading}
                  leftIcon={<LogOut className="w-4 h-4" />}
                >
                  Sign Out
                </AnimatedButton>
              </div>
            ) : (
              <>
                <Link href="/auth/login">
                  <AnimatedButton variant="ghost" size="sm">
                    Sign In
                  </AnimatedButton>
                </Link>
                <Link href="/auth/signup">
                  <AnimatedButton size="sm" glow>
                    Get Started
                  </AnimatedButton>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="md:hidden p-2 text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 rounded-lg transition-colors"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </motion.button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden border-t border-neutral-200 bg-white overflow-hidden"
          >
            <div className="px-4 py-4 space-y-2">
              {isAuthenticated ? (
                <>
                  <MobileNavLink href="/dashboard" icon={<LayoutDashboard className="w-5 h-5" />}>
                    Dashboard
                  </MobileNavLink>
                  <MobileNavLink href="/dashboard/history" icon={<History className="w-5 h-5" />}>
                    History
                  </MobileNavLink>
                  <MobileNavLink href="/dashboard/settings" icon={<Settings className="w-5 h-5" />}>
                    Settings
                  </MobileNavLink>
                  <div className="pt-2">
                    <AnimatedButton
                      variant="outline"
                      className="w-full"
                      onClick={handleSignOut}
                      leftIcon={<LogOut className="w-4 h-4" />}
                    >
                      Sign Out
                    </AnimatedButton>
                  </div>
                </>
              ) : (
                <>
                  <MobileNavLink href="/features">Features</MobileNavLink>
                  <MobileNavLink href="/pricing">Pricing</MobileNavLink>
                  <div className="pt-2 space-y-2">
                    <Link href="/auth/login" className="block">
                      <AnimatedButton variant="outline" className="w-full">
                        Sign In
                      </AnimatedButton>
                    </Link>
                    <Link href="/auth/signup" className="block">
                      <AnimatedButton className="w-full">
                        Get Started
                      </AnimatedButton>
                    </Link>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}

// Navigation Link Component
interface NavLinkProps {
  href: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
}

function NavLink({ href, children, icon }: NavLinkProps) {
  return (
    <Link
      href={href}
      className="flex items-center gap-2 px-4 py-2 text-neutral-600 hover:text-neutral-900 font-medium rounded-lg hover:bg-neutral-100 transition-all duration-200"
    >
      {icon}
      {children}
    </Link>
  );
}

// Mobile Navigation Link Component
function MobileNavLink({ href, children, icon }: NavLinkProps) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-3 py-2.5 text-neutral-700 hover:text-neutral-900 font-medium rounded-xl hover:bg-neutral-100 transition-colors"
    >
      {icon && <span className="text-neutral-400">{icon}</span>}
      {children}
    </Link>
  );
}

export default Header;
