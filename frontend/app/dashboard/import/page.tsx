"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import TextPressure from "@/components/TextPressure"

export default function ImportPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [sheetId, setSheetId] = useState("")
  const [sheetRange, setSheetRange] = useState("A:Z")
  const [messageTemplate, setMessageTemplate] = useState("Hi {name}, I'd like to connect with you about your business.")
  const [contactMethod, setContactMethod] = useState("email")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleCsvUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError("Please select a CSV file")
      return
    }

    setIsLoading(true)
    setError("")

    try {
      const token = localStorage.getItem("token")
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch("/api/import/csv", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Failed to import CSV")
      }

      // Redirect to job status page
      router.push(`/dashboard/jobs/${data.job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to import CSV")
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleSheetsImport = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      const token = localStorage.getItem("token")
      const response = await fetch("/api/import/google-sheets", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          sheet_id: sheetId,
          range: sheetRange,
          message_template: messageTemplate,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Failed to import from Google Sheets")
      }

      // Redirect to job status page
      router.push(`/dashboard/jobs/${data.job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to import from Google Sheets")
    } finally {
      setIsLoading(false)
    }
  }
  return (
    <div className="space-y-6 bg-white min-h-screen p-6">
      <div>
        <div style={{ height: '50px', width: '250px', marginBottom: '10px' }}>
          <TextPressure
            text="IMPORT DATA"
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
        <p className="text-muted-foreground">Import contacts from CSV or Google Sheets</p>
      </div>

      <Tabs defaultValue="csv">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="csv">CSV Upload</TabsTrigger>
          <TabsTrigger value="sheets">Google Sheets</TabsTrigger>
        </TabsList>

        <TabsContent value="csv">
          <Card>
            <form onSubmit={handleCsvUpload}>
              <CardHeader>
                <CardTitle>CSV Import</CardTitle>
                <CardDescription>Upload a CSV file with contact information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="csv-file">CSV File</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="csv-file"
                      type="file"
                      accept=".csv"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      required
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">CSV should have columns for name, email, and phone.</p>
                </div>

                <div className="space-y-2">
                  <Label>Contact Method</Label>
                  <RadioGroup value={contactMethod} onValueChange={setContactMethod}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="email" id="csv-email" />
                      <Label htmlFor="csv-email">Email</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="whatsapp" id="csv-whatsapp" />
                      <Label htmlFor="csv-whatsapp">WhatsApp</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="both" id="csv-both" />
                      <Label htmlFor="csv-both">Both</Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="csv-message">Message Template</Label>
                  <Textarea
                    id="csv-message"
                    placeholder="Enter your message template. Use {name} for business name."
                    value={messageTemplate}
                    onChange={(e) => setMessageTemplate(e.target.value)}
                    rows={4}
                  />
                  <p className="text-xs text-muted-foreground">
                    Use {"{name}"} to insert the business name in your message.
                  </p>
                </div>
              </CardContent>
              <CardFooter>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? "Importing..." : "Import CSV"}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </TabsContent>

        <TabsContent value="sheets">
          <Card>
            <form onSubmit={handleGoogleSheetsImport}>
              <CardHeader>
                <CardTitle>Google Sheets Import</CardTitle>
                <CardDescription>Import data from a Google Sheets document</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="sheet-id">Google Sheet ID</Label>
                  <Input
                    id="sheet-id"
                    placeholder="e.g., 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                    value={sheetId}
                    onChange={(e) => setSheetId(e.target.value)}
                    required
                  />
                  <p className="text-xs text-muted-foreground">The ID is in the URL of your Google Sheet.</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sheet-range">Sheet Range</Label>
                  <Input
                    id="sheet-range"
                    placeholder="e.g., A:Z or Sheet1!A2:E"
                    value={sheetRange}
                    onChange={(e) => setSheetRange(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label>Contact Method</Label>
                  <RadioGroup value={contactMethod} onValueChange={setContactMethod}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="email" id="sheets-email" />
                      <Label htmlFor="sheets-email">Email</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="whatsapp" id="sheets-whatsapp" />
                      <Label htmlFor="sheets-whatsapp">WhatsApp</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="both" id="sheets-both" />
                      <Label htmlFor="sheets-both">Both</Label>
                    </div>
                  </RadioGroup>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sheets-message">Message Template</Label>
                  <Textarea
                    id="sheets-message"
                    placeholder="Enter your message template. Use {name} for business name."
                    value={messageTemplate}
                    onChange={(e) => setMessageTemplate(e.target.value)}
                    rows={4}
                  />
                  <p className="text-xs text-muted-foreground">
                    Use {"{name}"} to insert the business name in your message.
                  </p>
                </div>
              </CardContent>
              <CardFooter>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? "Importing..." : "Import from Google Sheets"}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
