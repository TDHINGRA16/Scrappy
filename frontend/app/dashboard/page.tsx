"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Search, ImportIcon as FileImport } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import TextPressure from "@/components/TextPressure"

interface Job {
  id: number
  query: string
  mode: string
  status: string
  created_at: string
}

interface JobsResponse {
  jobs: Job[]
  pagination: {
    page: number
    size: number
    total: number
    pages: number
  }
}

export default function DashboardPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const token = localStorage.getItem("token")
        const response = await fetch("/api/export/jobs?page=1&size=5", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (!response.ok) {
          throw new Error("Failed to fetch jobs")
        }

        const data: JobsResponse = await response.json()
        setJobs(data.jobs)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch jobs")
      } finally {
        setIsLoading(false)
      }
    }

    fetchJobs()
  }, [])

  const getStatusColor = (status: string) => {
    if (status === "completed") return "success"
    if (status === "failed") return "destructive"
    if (status.includes("processing") || status.includes("scraping")) return "warning"
    return "secondary"
  }
  return (
    <div className="space-y-6 bg-white min-h-screen p-6">
      <div className="flex justify-between items-center">
        <div style={{ height: '50px', width: '200px' }}>
          <TextPressure
            text="DASHBOARD"
            flex={true}
            alpha={false}
            stroke={false}
            width={true}
            weight={true}
            italic={true}
            textColor="#000000"
            minFontSize={20}
          />
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/search">
            <Button>
              <Search className="mr-2 h-4 w-4" />
              New Search
            </Button>
          </Link>
          <Link href="/dashboard/import">
            <Button variant="outline">
              <FileImport className="mr-2 h-4 w-4" />
              Import Data
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Recent Jobs</CardTitle>
            <CardDescription>Your latest scraping jobs</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{jobs.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Completed</CardTitle>
            <CardDescription>Successfully finished jobs</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{jobs.filter((job) => job.status === "completed").length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>In Progress</CardTitle>
            <CardDescription>Currently running jobs</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {
                jobs.filter(
                  (job) =>
                    job.status.includes("processing") || job.status.includes("scraping") || job.status === "pending",
                ).length
              }
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Jobs</CardTitle>
          <CardDescription>Your most recent scraping and import jobs</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p>Loading jobs...</p>
          ) : error ? (
            <p className="text-red-500">{error}</p>
          ) : jobs.length === 0 ? (
            <p>No jobs found. Start by creating a new search job.</p>
          ) : (
            <div className="space-y-4">
              {jobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between border-b pb-4">
                  <div>
                    <p className="font-medium">{job.query || `Job #${job.id}`}</p>
                    <p className="text-sm text-muted-foreground">
                      {job.mode === "scrape_only" ? "Scrape Only" : "Scrape & Contact"}
                      {" • "}
                      {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={getStatusColor(job.status) as any}>{job.status}</Badge>
                    <Link href={`/dashboard/jobs/${job.id}`}>
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
        <CardFooter>
          <Link href="/dashboard/jobs">
            <Button variant="outline">View All Jobs</Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}
