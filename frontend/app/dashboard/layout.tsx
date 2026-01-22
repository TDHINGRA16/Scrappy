// ========================================
// Dashboard Layout - Redesigned with Modern Styling
// ========================================

import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-white to-neutral-100/50">
      <Header />
      <Sidebar />
      <main className="pl-64 pt-16 min-h-screen">
        <div className="p-8 max-w-[1600px]">{children}</div>
      </main>
    </div>
  );
}
