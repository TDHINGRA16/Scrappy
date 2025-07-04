"use client"

import type React from "react"
import type { SearchRequest, SearchJobResponse } from "@/lib/types"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import TextPressure from "@/components/TextPressure"

export default function SearchPage() {
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [limit, setLimit] = useState("10")
  const [source, setSource] = useState("google_maps") // Always use Google Maps
  const [mode, setMode] = useState("scrape_only")
  const [messageType, setMessageType] = useState("email")
  const [prewrittenMessage, setPrewrittenMessage] = useState(
    "Hi {name}, I'd like to connect with you about your business.",
  )
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      const token = localStorage.getItem("token")
      const response = await fetch("/api/search/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query,
          limit: Number.parseInt(limit),
          mode,
          message_type: messageType,
          prewritten_message: prewrittenMessage,
          source, // Include source in the request
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Failed to create search job")
      }

      // Redirect to job status page
      router.push(`/dashboard/jobs/${data.job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create search job")
    } finally {
      setIsLoading(false)
    }
  }
  return (
    <div className="space-y-6 bg-white min-h-screen p-6">
      <div>
        <div style={{ height: '50px', width: '300px', marginBottom: '10px' }}>
          <TextPressure
            text="CREATE SEARCH JOB"
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
        <p className="text-muted-foreground">Set up a new scraping job to find and contact businesses</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>Search Parameters</CardTitle>
            <CardDescription>Define what you want to search for</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="query">Search Query</Label>
              <Input
                id="query"
                placeholder="e.g., restaurants in New York"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="limit">Result Limit</Label>
              <Select value={limit} onValueChange={setLimit}>
                <SelectTrigger>
                  <SelectValue placeholder="Select limit" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5 results</SelectItem>
                  <SelectItem value="10">10 results</SelectItem>
                  <SelectItem value="25">25 results</SelectItem>
                  <SelectItem value="50">50 results</SelectItem>
                  <SelectItem value="100">100 results</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Search Source</Label>
              <RadioGroup value={source} onValueChange={setSource} disabled>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="google_maps" id="google_maps" />
                  <Label htmlFor="google_maps">Google Maps</Label>
                </div>
              </RadioGroup>
              <p className="text-xs text-muted-foreground">
                Scrapes Google Maps using Selenium for local businesses with contact information.
              </p>
            </div>

            <div className="space-y-2">
              <Label>Mode</Label>
              <RadioGroup value={mode} onValueChange={setMode}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="scrape_only" id="scrape_only" />
                  <Label htmlFor="scrape_only">Scrape Only</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="scrape_and_contact" id="scrape_and_contact" />
                  <Label htmlFor="scrape_and_contact">Scrape and Contact</Label>
                </div>
              </RadioGroup>
            </div>

            {mode === "scrape_and_contact" && (
              <>
                <div className="space-y-2">
                  <Label>Contact Method</Label>
                  <RadioGroup value={messageType} onValueChange={setMessageType}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="email" id="email" />
                      <Label htmlFor="email">Email</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="whatsapp" id="whatsapp" />
                      <Label htmlFor="whatsapp">WhatsApp</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="both" id="both" />
                      <Label htmlFor="both">Both</Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="message">Message Template</Label>
                  <Textarea
                    id="message"
                    placeholder="Enter your message template. Use {name} for business name."
                    value={prewrittenMessage}
                    onChange={(e) => setPrewrittenMessage(e.target.value)}
                    rows={4}
                  />
                  <p className="text-xs text-muted-foreground">
                    Use {"{name}"} to insert the business name in your message.
                  </p>
                </div>
              </>
            )}
          </CardContent>
          <CardFooter>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Creating Job..." : "Create Search Job"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
