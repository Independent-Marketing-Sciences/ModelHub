"use client";

import { useRef } from "react";
import { useDataStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, FileSpreadsheet, CheckCircle2 } from "lucide-react";
import Papa from "papaparse";
import * as XLSX from "xlsx";

export function DatasetLoader() {
  const { data, setData, setColumns, setDateColumn, setError, setIsLoading } = useDataStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Helper function to detect the date column
  const detectDateColumn = (columns: string[]): string => {
    // Check for common date column names (case-insensitive) - OBS is priority
    const dateColumnNames = ['OBS', 'obs', 'Observation', 'observation', 'Date', 'DATE', 'date'];
    for (const name of dateColumnNames) {
      const found = columns.find(col => col.toLowerCase() === name.toLowerCase());
      if (found) {
        console.log('[DatasetLoader] Matched date column:', found);
        return found;
      }
    }
    // If no match, check if any column contains 'date' or 'obs'
    const containsDate = columns.find(col =>
      col.toLowerCase().includes('date') || col.toLowerCase().includes('obs')
    );
    if (containsDate) {
      console.log('[DatasetLoader] Found column containing date/obs:', containsDate);
      return containsDate;
    }

    console.warn('[DatasetLoader] No date column found, defaulting to first column:', columns[0]);
    // Default to first column if no date column found
    return columns[0] || "Date";
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setError(null);

    const fileExtension = file.name.split('.').pop()?.toLowerCase();

    if (fileExtension === 'csv') {
      // Parse CSV file
      Papa.parse(file, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (results) => {
          if (results.data && results.data.length > 0) {
            const columns = Object.keys(results.data[0] as object);
            const dateCol = detectDateColumn(columns);
            console.log('[DatasetLoader] Detected date column:', dateCol);
            setColumns(columns);
            setDateColumn(dateCol);
            setData(results.data as any[]);
            setIsLoading(false);
          } else {
            setError("No data found in CSV file");
            setIsLoading(false);
          }
        },
        error: (error) => {
          setError(`Error parsing CSV: ${error.message}`);
          setIsLoading(false);
        },
      });
    } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
      // Parse Excel file
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: 'array' });

          // Get first sheet
          const firstSheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheetName];

          // Convert to JSON
          const jsonData = XLSX.utils.sheet_to_json(worksheet);

          if (jsonData && jsonData.length > 0) {
            const columns = Object.keys(jsonData[0] as object);
            const dateCol = detectDateColumn(columns);
            console.log('[DatasetLoader] Detected date column:', dateCol);
            setColumns(columns);
            setDateColumn(dateCol);
            setData(jsonData as any[]);
            setIsLoading(false);
          } else {
            setError("No data found in Excel file");
            setIsLoading(false);
          }
        } catch (error) {
          setError(`Error parsing Excel: ${error}`);
          setIsLoading(false);
        }
      };
      reader.readAsArrayBuffer(file);
    } else {
      setError("Unsupported file format. Please upload CSV or Excel files.");
      setIsLoading(false);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const dataLoaded = data.length > 0;

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSpreadsheet className="h-5 w-5" />
          Dataset Loader
        </CardTitle>
        <CardDescription>
          Upload your dataset (CSV or Excel) to begin analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileUpload}
            className="hidden"
          />

          {dataLoaded ? (
            <div className="flex items-center gap-3 text-green-600">
              <CheckCircle2 className="h-5 w-5" />
              <div>
                <p className="font-medium">Dataset loaded successfully</p>
                <p className="text-sm text-muted-foreground">
                  {data.length.toLocaleString()} rows loaded
                </p>
              </div>
              <Button
                onClick={handleUploadClick}
                variant="outline"
                size="sm"
                className="ml-auto"
              >
                <Upload className="mr-2 h-4 w-4" />
                Upload New Dataset
              </Button>
            </div>
          ) : (
            <Button onClick={handleUploadClick} size="lg">
              <Upload className="mr-2 h-4 w-4" />
              Upload Dataset
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
