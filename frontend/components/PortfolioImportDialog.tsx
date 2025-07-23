"use client"

import * as React from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button" // Assuming shadcn/ui Button
import { Input } from "@/components/ui/input" // Assuming shadcn/ui Input
import { Label } from "@/components/ui/label" // Assuming shadcn/ui Label
import { Upload } from "lucide-react"

interface PortfolioImportDialogProps {
  isOpen: boolean
  onClose: () => void
  onImport: (method: string, data?: any) => void
}

export default function PortfolioImportDialog({ isOpen, onClose, onImport }: PortfolioImportDialogProps) {
  const [csvFile, setCsvFile] = React.useState<File | null>(null)
  const [isLoading, setIsLoading] = React.useState(false)

  const handleCsvUpload = async () => {
    if (!csvFile) return
    setIsLoading(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500))
    onImport("csv", csvFile.name) // Pass file name for demo
    setIsLoading(false)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Import Your Portfolio</DialogTitle>
          <DialogDescription>Choose a method to import your existing stock portfolio.</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="csv-upload" className="flex items-center gap-2">
              <Upload className="w-4 h-4" /> Upload CSV
            </Label>
            <Input
              id="csv-upload"
              type="file"
              accept=".csv"
              onChange={(e) => setCsvFile(e.target.files ? e.target.files[0] : null)}
            />
            <Button onClick={handleCsvUpload} disabled={!csvFile || isLoading}>
              {isLoading ? "Uploading..." : "Upload CSV"}
            </Button>
            <p className="text-xs text-gray-500 mt-1">
              Download your holdings as a CSV from your brokerage and upload here.
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
