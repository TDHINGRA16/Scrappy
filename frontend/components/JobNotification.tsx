"use client"

import { useEffect, useState } from "react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { CheckCircle, X } from "lucide-react"
import { Button } from "@/components/ui/button"

interface JobNotificationProps {
  jobId: string
  status: string
  query: string
  onDismiss: () => void
}

export default function JobNotification({ jobId, status, query, onDismiss }: JobNotificationProps) {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    // Auto-dismiss after 10 seconds
    const timer = setTimeout(() => {
      setIsVisible(false)
      onDismiss()
    }, 10000)

    return () => clearTimeout(timer)
  }, [onDismiss])

  if (!isVisible) return null

  return (
    <Alert className="fixed top-4 right-4 w-96 z-50 shadow-lg border-green-200 bg-green-50">
      <CheckCircle className="h-4 w-4 text-green-600" />
      <AlertDescription className="text-green-800">
        <div className="flex justify-between items-start">
          <div>
            <p className="font-medium">Job Completed! 🎉</p>
            <p className="text-sm mt-1">
              "{query}" has finished scraping
            </p>
            <p className="text-xs mt-1 text-green-600">
              Click to view results
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setIsVisible(false)
              onDismiss()
            }}
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  )
} 