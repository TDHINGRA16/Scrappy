"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Eye, RefreshCw, Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import TextPressure from "@/components/TextPressure"
import JobNotification from "@/components/JobNotification"

interface JobStatus {
  id: string
  status: string
  created_at: string
  updated_at: string
  query: string
  limit: number
  results_count?: number
  error_message?: string
  progress_percentage?: number
  current_step?: string
  estimated_time_remaining?: string
}

interface CompletedJob {
  id: string
  query: string
  status: string
}

export default function JobsPage() {
  const router = useRouter()
  const [jobs, setJobs] = useState<JobStatus[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [isMounted, setIsMounted] = useState(false)
  const [completedJobs, setCompletedJobs] = useState<CompletedJob[]>([])
  const [previousJobStatuses, setPreviousJobStatuses] = useState<Record<string, string>>({})

  useEffect(() => {
    setIsMounted(true)
    fetchJobs()
    
    // Auto-refresh for processing jobs with more frequent updates
    const interval = setInterval(() => {
      const hasProcessingJobs = jobs.some(job => 
        job.status.includes("processing") || 
        job.status.includes("scraping") || 
        job.status === "pending"
      )
      if (hasProcessingJobs) {
        fetchJobs()
      }
    }, 3000) // Refresh every 3 seconds for processing jobs
    
    return () => clearInterval(interval)
  }, [])

  const fetchJobs = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem("token")
      const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '') || ''
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/export/jobs?page=1&size=50`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch jobs")
      }

      const data = await response.json()
      const jobsWithProgress = await Promise.all(
        (data.jobs || []).map(async (job: JobStatus) => {
          // Fetch progress for each job
          try {
            const progressResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/search/${job.id}/progress`, {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            })
            
            if (progressResponse.ok) {
              const progressData = await progressResponse.json()
              return {
                ...job,
                progress_percentage: progressData.progress_percentage,
                current_step: progressData.current_step,
                estimated_time_remaining: progressData.estimated_time_remaining
              }
            }
          } catch (error) {
            console.error(`Failed to fetch progress for job ${job.id}:`, error)
          }
          
          return job
        })
      )
      
      // Check for newly completed jobs
      jobsWithProgress.forEach(job => {
        const previousStatus = previousJobStatuses[job.id]
        if (previousStatus && previousStatus.includes("processing") && job.status === "completed") {
          setCompletedJobs(prev => [...prev, { id: job.id, query: job.query, status: job.status }])
        }
      })
      
      setPreviousJobStatuses(
        jobsWithProgress.reduce((acc, job) => ({ ...acc, [job.id]: job.status }), {})
      )
      
      setJobs(jobsWithProgress)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch jobs")
      setJobs([])
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return "default"
      case "running":
        return "secondary"
      case "failed":
        return "destructive"
      case "pending":
        return "outline"
      default:
        return "outline"
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffInSeconds < 60) {
      return `${diffInSeconds} seconds ago`
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60)
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600)
      return `${hours} hour${hours > 1 ? 's' : ''} ago`
    } else {
      const days = Math.floor(diffInSeconds / 86400)
      return `${days} day${days > 1 ? 's' : ''} ago`
    }
  }

  const dismissNotification = (jobId: string) => {
    setCompletedJobs(prev => prev.filter(job => job.id !== jobId))
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin" />
        <span className="ml-2">Loading jobs...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6 bg-white min-h-screen p-6">
      {/* Job completion notifications */}
      {completedJobs.map(job => (
        <JobNotification
          key={job.id}
          jobId={job.id}
          status={job.status}
          query={job.query}
          onDismiss={() => dismissNotification(job.id)}
        />
      ))}

      <div className="flex justify-between items-center">
        <div style={{ height: '50px', width: '200px' }}>
          {isMounted ? (
            <TextPressure
              text="JOBS"
              flex={true}
              alpha={false}
              stroke={false}
              width={true}
              weight={true}
              italic={true}
              textColor="#000000"
              minFontSize={20}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <h1 className="text-2xl font-bold text-black">JOBS</h1>
            </div>
          )}
        </div>
        <Button variant="outline" size="icon" onClick={fetchJobs}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex justify-between items-center">
        <Button onClick={() => router.push("/dashboard/search")}>
          Create New Job
        </Button>
      </div>

      {(jobs?.length || 0) === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <h3 className="text-lg font-semibold mb-2">No jobs found</h3>
            <p className="text-muted-foreground mb-4">Create your first scraping job to get started</p>
            <Button onClick={() => router.push("/dashboard/search")}>
              Create New Job
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {jobs?.map((job) => (
            <Card key={job.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{job.query}</CardTitle>
                    <CardDescription>
                      Created: {formatDate(job.created_at)}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={getStatusColor(job.status)}>
                      {job.status}
                    </Badge>
                    {job.status.includes("processing") && (
                      <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Progress Bar for Processing Jobs */}
                  {job.status.includes("processing") && job.progress_percentage !== undefined && (
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-sm">
                        <span>{job.current_step || "Processing..."}</span>
                        <span>{job.progress_percentage}%</span>
                      </div>
                      <Progress value={job.progress_percentage} className="h-2" />
                      {job.estimated_time_remaining && (
                        <p className="text-xs text-muted-foreground">
                          ⏱️ {job.estimated_time_remaining}
                        </p>
                      )}
                    </div>
                  )}
                  
                  {/* Real-time status for processing jobs */}
                  {job.status.includes("processing") && (
                    <div className="flex items-center gap-2 text-xs text-blue-600">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>Live updates every 3 seconds</span>
                    </div>
                  )}
                  
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-muted-foreground">
                      <p>Limit: {job.limit} results</p>
                      {job.results_count !== undefined && (
                        <p>Found: {job.results_count} results</p>
                      )}
                      {job.error_message && (
                        <p className="text-red-500">Error: {job.error_message}</p>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/dashboard/jobs/${job.id}`)}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
