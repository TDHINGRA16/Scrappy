"use client"

import { use, useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AlertCircle, Download, RefreshCw, Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { formatDistanceToNow } from "date-fns"
import TextPressure from "@/components/TextPressure"
import JobNotification from "@/components/JobNotification"

interface JobStatus {
  job_id: number
  query: string
  source: string  // Add source field
  mode: string
  status: string
  created_at: string
  results_count: number
  messages_count: number
  message_stats: {
    sent: number
    failed: number
    pending: number
  }
  has_results: boolean
  can_export: boolean
}

interface JobProgress {
  job_id: number
  status: string
  progress_percentage: number
  current_step: string
  results_count: number
  target_results: number
  query: string
  created_at: string
  estimated_time_remaining: string
}

interface Result {
  id: number
  name: string
  website?: string | null
  email?: string | null
  phone?: string | null
  address?: string | null
  source: string
  // Enhanced fields from the new scraper
  reviews_count?: number | null
  reviews_average?: number | null
  store_shopping?: string | null
  in_store_pickup?: string | null
  store_delivery?: string | null
  place_type?: string | null
  opening_hours?: string | null
  introduction?: string | null
}

interface Message {
  id: number
  contact_method: string
  recipient: string
  message: string
  status: string
  sent_at: string
}

export default function JobPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [jobProgress, setJobProgress] = useState<JobProgress | null>(null)
  const [results, setResults] = useState<Result[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [exportFormat, setExportFormat] = useState("csv")
  const [isMounted, setIsMounted] = useState(false)
  const [showCompletionNotification, setShowCompletionNotification] = useState(false)

  const fetchJobProgress = async () => {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/search/${resolvedParams.id}/progress`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch job progress")
      }

      const data = await response.json()
      setJobProgress(data)
    } catch (err) {
      console.error("Failed to fetch job progress:", err)
    }
  }

  const fetchJobStatus = async () => {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/export/jobs/${resolvedParams.id}/status`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch job status")
      }

      const data = await response.json()
      
      // Check if job just completed
      if (jobStatus && jobStatus.status.includes("processing") && data.status === "completed") {
        setShowCompletionNotification(true)
      }
      
      setJobStatus(data)

      // If job is completed, fetch results
      if (data.has_results) {
        fetchJobResults()
      }
      
      // Always fetch progress
      fetchJobProgress()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch job status")
    } finally {
      setIsLoading(false)
    }
  }

  const fetchJobResults = async () => {
    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/export/json/${resolvedParams.id}?include_messages=true`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch job results")
      }

      const data = await response.json()
      setResults(data.results || [])
      setMessages(data.messages || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch job results")
    }
  }

  useEffect(() => {
    fetchJobStatus()

    // Poll for updates if job is still processing with more frequent updates
    const interval = setInterval(() => {
      if (
        jobStatus &&
        (jobStatus.status === "pending" ||
          jobStatus.status.includes("processing") ||
          jobStatus.status.includes("scraping"))
      ) {
        fetchJobStatus()
        fetchJobProgress() // Also fetch progress updates
      } else if (jobStatus && jobStatus.status === "completed" && jobStatus.has_results) {
        // If job is completed and has results, fetch them once
        fetchJobResults()
      }
    }, 2000) // Poll every 2 seconds for more frequent updates

    return () => clearInterval(interval)
  }, [resolvedParams.id, jobStatus?.status]) // Include jobStatus?.status in dependencies

  // Additional effect to fetch results when job completes
  useEffect(() => {
    if (jobStatus && jobStatus.status === "completed" && jobStatus.has_results && results.length === 0) {
      fetchJobResults()
    }
  }, [jobStatus?.status, jobStatus?.has_results])

  useEffect(() => {
    setIsMounted(true)
  }, [])

  const handleExport = () => {
    const token = localStorage.getItem("token")
    const url = `/api/export/${exportFormat}/${resolvedParams.id}?include_messages=true`

    // Create a hidden form to submit as POST
    const form = document.createElement("form")
    form.method = "POST"
    form.action = url

    // Add authorization header via meta tag (this is a workaround)
    const meta = document.createElement("meta")
    meta.name = "authorization"
    meta.content = `Bearer ${token}`
    document.head.appendChild(meta)

    document.body.appendChild(form)
    form.submit()

    // Clean up
    setTimeout(() => {
      document.head.removeChild(meta)
      document.body.removeChild(form)
    }, 100)
  }

  const getStatusColor = (status: string) => {
    if (status === "completed" || status === "sent") return "success"
    if (status === "failed" || status.includes("failed")) return "destructive"
    if (status.includes("processing") || status.includes("scraping") || status === "pending") return "warning"
    return "secondary"
  }

  const getProgressValue = () => {
    if (jobProgress) {
      return jobProgress.progress_percentage
    }
    if (!jobStatus) return 0
    if (jobStatus.status === "completed") return 100
    if (jobStatus.status === "pending") return 5
    if (jobStatus.status.includes("processing")) return 30
    if (jobStatus.status.includes("scraping_completed")) return 70
    return 50
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p>Loading job details...</p>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!jobStatus) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Job not found</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6 bg-white min-h-screen p-6">
      {/* Job completion notification */}
      {showCompletionNotification && jobStatus && (
        <JobNotification
          jobId={resolvedParams.id}
          status={jobStatus.status}
          query={jobStatus.query}
          onDismiss={() => setShowCompletionNotification(false)}
        />
      )}

      <div className="flex justify-between items-center">
        <div>
          <div style={{ height: '50px', width: '300px', marginBottom: '10px' }}>
            {isMounted ? (
              <TextPressure
                text={`JOB #${jobStatus.job_id}`}
                flex={true}
                alpha={false}
                stroke={false}
                width={true}
                weight={true}
                italic={true}
                textColor="#000000"
                minFontSize={18}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <h1 className="text-xl font-bold text-black">{`JOB #${jobStatus.job_id}`}</h1>
              </div>
            )}
          </div>
          {jobStatus.query && (
            <h2 className="text-lg font-semibold mb-2">{jobStatus.query}</h2>
          )}
          <p className="text-muted-foreground">
            Google Maps
            {" • "}
            {jobStatus.mode === "scrape_only" ? "Scrape Only" : "Scrape & Contact"}
            {" • "}
            {formatDistanceToNow(new Date(jobStatus.created_at), { addSuffix: true })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={getStatusColor(jobStatus.status) as any}>{jobStatus.status}</Badge>
          {jobStatus.status.includes("processing") && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Processing...</span>
            </div>
          )}
          <Button variant="outline" size="icon" onClick={fetchJobStatus}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job Progress</CardTitle>
          <CardDescription>
            {jobProgress ? jobProgress.current_step : "Loading progress..."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={getProgressValue()} className="h-3" />
          
          {jobProgress && (
            <div className="flex justify-between items-center text-sm text-muted-foreground">
              <span>{jobProgress.results_count} / {jobProgress.target_results} results</span>
              <span>{jobProgress.estimated_time_remaining}</span>
            </div>
          )}

          {/* Real-time status indicator */}
          {jobStatus && (jobStatus.status.includes("processing") || jobStatus.status.includes("scraping")) && (
            <div className="flex items-center gap-2 text-sm text-blue-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>{jobProgress?.current_step || "Processing..."}</span>
            </div>
          )}

          {/* Completion notification */}
          {jobStatus && jobStatus.status === "completed" && (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <span>✅ Scraping completed successfully!</span>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
            <div>
              <p className="text-sm text-muted-foreground">Results</p>
              <p className="text-2xl font-bold">{jobStatus.results_count}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Messages</p>
              <p className="text-2xl font-bold">{jobStatus.messages_count}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Sent</p>
              <p className="text-2xl font-bold">{jobStatus.message_stats?.sent || 0}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Failed</p>
              <p className="text-2xl font-bold">{jobStatus.message_stats?.failed || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {jobStatus.has_results && (
        <>
          <Tabs defaultValue="results">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="results">Results ({results.length})</TabsTrigger>
              <TabsTrigger value="messages">Messages ({messages.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="results">
              <Card>
                <CardHeader>
                  <CardTitle>Scraped Results</CardTitle>
                  <CardDescription>Businesses found during scraping</CardDescription>
                </CardHeader>
                <CardContent>
                  {results.length === 0 ? (
                    <p>No results found yet.</p>
                  ) : (
                    <div className="space-y-4">
                      {results.map((result) => (
                        <div key={result.id} className="border-b pb-4">
                          <p className="font-medium">{result.name}</p>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-2">
                            <p className="text-sm">
                              <span className="text-muted-foreground">Website:</span>{" "}
                              {result.website ? (
                                <a
                                  href={result.website.startsWith('http://') || result.website.startsWith('https://') ? result.website : `https://${result.website}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary hover:underline"
                                >
                                  {result.website}
                                </a>
                              ) : (
                                "N/A"
                              )}
                            </p>
                            <p className="text-sm">
                              <span className="text-muted-foreground">Email:</span> {result.email || "N/A"}
                            </p>
                            <p className="text-sm">
                              <span className="text-muted-foreground">Phone:</span> {result.phone || "N/A"}
                            </p>
                            <p className="text-sm">
                              <span className="text-muted-foreground">Place Type:</span> {result.place_type || "N/A"}
                            </p>
                            <p className="text-sm">
                              <span className="text-muted-foreground">Reviews:</span> {result.reviews_count ? `${result.reviews_count} (${result.reviews_average}★)` : "N/A"}
                            </p>
                            <p className="text-sm">
                              <span className="text-muted-foreground">Opening Hours:</span> {result.opening_hours || "N/A"}
                            </p>
                            <p className="text-sm">
                              <span className="text-muted-foreground">Store Shopping:</span> {result.store_shopping || "N/A"}
                            </p>
                            <p className="text-sm">
                              <span className="text-muted-foreground">In-Store Pickup:</span> {result.in_store_pickup || "N/A"}
                            </p>
                            <p className="text-sm">
                              <span className="text-muted-foreground">Delivery:</span> {result.store_delivery || "N/A"}
                            </p>
                            <p className="text-sm">
                              <span className="text-muted-foreground">Source:</span> {result.source || "N/A"}
                            </p>
                          </div>
                          {result.address && (
                            <p className="text-sm mt-2">
                              <span className="text-muted-foreground">Address:</span> {result.address}
                            </p>
                          )}
                          {result.introduction && (
                            <p className="text-sm mt-2">
                              <span className="text-muted-foreground">About:</span> {result.introduction}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="messages">
              <Card>
                <CardHeader>
                  <CardTitle>Outreach Messages</CardTitle>
                  <CardDescription>Messages sent to contacts</CardDescription>
                </CardHeader>
                <CardContent>
                  {messages.length === 0 ? (
                    <p>No messages found for this job.</p>
                  ) : (
                    <div className="space-y-4">
                      {messages.map((message) => (
                        <div key={message.id} className="border-b pb-4">
                          <div className="flex justify-between items-center">
                            <p className="font-medium">{message.recipient}</p>
                            <Badge variant={getStatusColor(message.status) as any}>{message.status}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {message.contact_method === "email" ? "Email" : "WhatsApp"}
                            {message.sent_at && (
                              <>
                                {" • "}
                                {formatDistanceToNow(new Date(message.sent_at), { addSuffix: true })}
                              </>
                            )}
                          </p>
                          <p className="text-sm mt-2 border-l-2 border-muted pl-2 italic">{message.message}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {jobStatus.can_export && (
            <Card>
              <CardHeader>
                <CardTitle>Export Data</CardTitle>
                <CardDescription>Download your results in different formats</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <Button
                    variant={exportFormat === "csv" ? "default" : "outline"}
                    onClick={() => setExportFormat("csv")}
                  >
                    CSV
                  </Button>
                  <Button
                    variant={exportFormat === "excel" ? "default" : "outline"}
                    onClick={() => setExportFormat("excel")}
                  >
                    Excel
                  </Button>
                  <Button
                    variant={exportFormat === "json" ? "default" : "outline"}
                    onClick={() => setExportFormat("json")}
                  >
                    JSON
                  </Button>
                </div>
              </CardContent>
              <CardFooter>
                <Button onClick={handleExport}>
                  <Download className="mr-2 h-4 w-4" />
                  Export as {exportFormat.toUpperCase()}
                </Button>
              </CardFooter>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
