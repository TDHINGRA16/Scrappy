"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Search, Home, ImportIcon as FileImport, LogOut } from "lucide-react"
import { Suspense } from "react"
import TextPressure from "@/components/TextPressure"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }

    // Verify token
    const verifyToken = async () => {
      try {
        const response = await fetch("/api/auth/verify", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (!response.ok) {
          throw new Error("Invalid token")
        }

        setIsLoading(false)
      } catch (err) {
        localStorage.removeItem("token")
        router.push("/login")
      }
    }

    verifyToken()
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem("token")
    router.push("/login")
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p>Loading...</p>
      </div>
    )
  }
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="font-bold">
              <div style={{ height: '40px', width: '120px' }}>
                <TextPressure
                  text="SCRAPPY"
                  flex={true}
                  alpha={false}
                  stroke={false}
                  width={true}
                  weight={true}
                  italic={true}
                  textColor="#000000"
                  minFontSize={18}
                />
              </div>
            </Link>
            <nav className="hidden md:flex gap-6">
              <Link href="/dashboard" className="text-sm font-medium">
                Dashboard
              </Link>
              <Link href="/dashboard/search" className="text-sm font-medium">
                Search
              </Link>
              <Link href="/dashboard/import" className="text-sm font-medium">
                Import
              </Link>
            </nav>
          </div>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </header>
      <div className="container flex-1 py-6">
        <Suspense fallback={<div>Loading...</div>}>
          <div className="flex flex-col md:hidden space-y-2 mb-6">
            <Link href="/dashboard">
              <Button variant="outline" className="w-full justify-start">
                <Home className="mr-2 h-4 w-4" />
                Dashboard
              </Button>
            </Link>
            <Link href="/dashboard/search">
              <Button variant="outline" className="w-full justify-start">
                <Search className="mr-2 h-4 w-4" />
                Search
              </Button>
            </Link>
            <Link href="/dashboard/import">
              <Button variant="outline" className="w-full justify-start">
                <FileImport className="mr-2 h-4 w-4" />
                Import
              </Button>
            </Link>
          </div>
          {children}
        </Suspense>
      </div>
    </div>
  )
}
