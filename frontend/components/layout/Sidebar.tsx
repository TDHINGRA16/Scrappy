// ========================================
// Sidebar Component (Dashboard) - Redesigned with Animations
// ========================================

"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Search, 
  History, 
  FileSpreadsheet, 
  MessageSquare, 
  Settings, 
  ChevronLeft,
  Zap,
  Sparkles
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  name: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

const navItems: NavItem[] = [
  {
    name: "Scraper",
    href: "/dashboard",
    icon: <Search className="w-5 h-5" />,
  },
  {
    name: "History",
    href: "/dashboard/history",
    icon: <History className="w-5 h-5" />,
  },
  {
    name: "Google Sheets",
    href: "/dashboard/sheets",
    icon: <FileSpreadsheet className="w-5 h-5" />,
  },
  {
    name: "Outreach",
    href: "/dashboard/outreach",
    icon: <MessageSquare className="w-5 h-5" />,
    badge: "New",
  },
  {
    name: "Settings",
    href: "/dashboard/settings",
    icon: <Settings className="w-5 h-5" />,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "fixed left-0 top-16 h-[calc(100vh-4rem)] bg-white/80 backdrop-blur-xl border-r border-neutral-200/50",
        "transition-all duration-300 ease-in-out z-30",
        isCollapsed ? "w-[72px]" : "w-64"
      )}
    >
      <div className="flex flex-col h-full">
        {/* Toggle Button */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-6 w-6 h-6 bg-white border border-neutral-200 rounded-full flex items-center justify-center shadow-md hover:shadow-lg transition-all z-10"
        >
          <ChevronLeft 
            className={cn(
              "w-4 h-4 text-neutral-600 transition-transform duration-300",
              isCollapsed && "rotate-180"
            )}
          />
        </motion.button>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-6 space-y-1.5">
          {navItems.map((item, index) => {
            const isActive = pathname === item.href;
            return (
              <motion.div
                key={item.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Link
                  href={item.href}
                  className={cn(
                    "group relative flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200",
                    isActive
                      ? "bg-gradient-to-r from-primary-500/10 to-secondary-500/10 text-primary-700"
                      : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900"
                  )}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute left-0 w-1 h-6 bg-gradient-to-b from-primary-500 to-secondary-500 rounded-full"
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  )}
                  
                  <span className={cn(
                    "transition-colors duration-200",
                    isActive ? "text-primary-600" : "text-neutral-400 group-hover:text-neutral-600"
                  )}>
                    {item.icon}
                  </span>
                  
                  <AnimatePresence>
                    {!isCollapsed && (
                      <motion.div
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: "auto" }}
                        exit={{ opacity: 0, width: 0 }}
                        className="flex items-center gap-2 overflow-hidden"
                      >
                        <span className="font-medium whitespace-nowrap">{item.name}</span>
                        {item.badge && (
                          <span className="px-1.5 py-0.5 text-[10px] font-bold bg-gradient-to-r from-secondary-500 to-primary-500 text-white rounded-full">
                            {item.badge}
                          </span>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  {/* Tooltip for collapsed state */}
                  {isCollapsed && (
                    <div className="absolute left-full ml-2 px-2 py-1 bg-neutral-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                      {item.name}
                    </div>
                  )}
                </Link>
              </motion.div>
            );
          })}
        </nav>

        {/* Footer */}
        <AnimatePresence>
          {!isCollapsed && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="p-4 border-t border-neutral-200/50"
            >
              <div className="bg-gradient-to-br from-primary-500/10 to-secondary-500/10 rounded-xl p-4 relative overflow-hidden">
                {/* Background decoration */}
                <div className="absolute top-0 right-0 w-16 h-16 bg-primary-500/10 rounded-full blur-xl" />
                
                <div className="relative flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4 text-primary-600" />
                  <span className="text-sm font-bold bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
                    Scrappy v2.0
                  </span>
                </div>
                <p className="relative text-xs text-neutral-600 flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  Pro Lead Generation
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.aside>
  );
}

export default Sidebar;
