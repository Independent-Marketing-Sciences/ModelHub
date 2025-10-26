"use client";

import { useRef } from "react";
import { useDataStore } from "@/lib/store";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { ThemeLogo } from "@/components/ThemeLogo";
import { Upload, FileSpreadsheet, LineChart, TrendingUp } from "lucide-react";
import Papa from "papaparse";
import * as XLSX from "xlsx";

interface LandingPageProps {
  onDataLoaded: () => void;
}

export function LandingPage({ onDataLoaded }: LandingPageProps) {
  const { setData, setColumns, setError, setIsLoading } = useDataStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setError(null);

    const fileExtension = file.name.split('.').pop()?.toLowerCase();

    if (fileExtension === 'csv') {
      Papa.parse(file, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (results) => {
          if (results.data && results.data.length > 0) {
            const columns = Object.keys(results.data[0] as object);
            setColumns(columns);
            setData(results.data as any[]);
            setIsLoading(false);
            onDataLoaded();
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
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: 'array' });
          const firstSheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet);

          if (jsonData && jsonData.length > 0) {
            const columns = Object.keys(jsonData[0] as object);
            setColumns(columns);
            setData(jsonData as any[]);
            setIsLoading(false);
            onDataLoaded();
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

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Theme Toggle in top right */}
      <div className="absolute top-6 right-6">
        <ThemeToggle />
      </div>

      {/* Logo higher up */}
      <div className="pt-8 pb-4 flex justify-center">
        <ThemeLogo width={240} height={96} />
      </div>

      {/* Main content centered below */}
      <div className="flex-1 flex items-center justify-center px-4 -mt-6">
        <div className="mx-auto w-full max-w-[550px]">
          <div className="flex w-full flex-col justify-center space-y-6">
            {/* Header */}
            <div className="flex flex-col space-y-4 text-center">
              <h1 className="text-2xl font-semibold tracking-tight">
                Modelling Mate
              </h1>
              <p className="text-sm text-muted-foreground">
                Media Analytics & Marketing Mix Modeling
              </p>
            </div>

          {/* Main Card */}
          <Card>
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl tracking-tight">
                Get Started
              </CardTitle>
              <CardDescription>
                Upload your dataset to begin analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Upload Section */}
              <div className="grid gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileUpload}
                  className="hidden"
                />

                <div
                  className="group relative grid h-52 w-full cursor-pointer place-items-center rounded-lg border-2 border-dashed border-muted-foreground/25 px-5 py-2.5 text-center transition hover:bg-muted/25"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="flex flex-col items-center justify-center gap-4">
                    <div className="flex h-20 w-20 items-center justify-center rounded-full border bg-background">
                      <FileSpreadsheet className="h-10 w-10 text-muted-foreground" />
                    </div>
                    <div className="space-y-px">
                      <p className="font-medium text-sm">
                        Choose file or drag & drop
                      </p>
                      <p className="text-xs text-muted-foreground">
                        CSV, XLSX, XLS (max. 100MB)
                      </p>
                    </div>
                  </div>
                </div>

                <Button
                  onClick={() => fileInputRef.current?.click()}
                  size="lg"
                  className="w-full"
                >
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Dataset
                </Button>
              </div>

            </CardContent>
          </Card>

          {/* Features */}
          <div className="grid gap-4 pt-2">
            <div className="grid grid-cols-3 gap-2">
              <div className="flex flex-col gap-2 rounded-lg border bg-card p-3 text-card-foreground">
                <LineChart className="h-5 w-5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">
                    Charting
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Interactive visualizations
                  </p>
                </div>
              </div>
              <div className="flex flex-col gap-2 rounded-lg border bg-card p-3 text-card-foreground">
                <TrendingUp className="h-5 w-5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">
                    Correlation
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Relationship analysis
                  </p>
                </div>
              </div>
              <div className="flex flex-col gap-2 rounded-lg border bg-card p-3 text-card-foreground">
                <TrendingUp className="h-5 w-5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">
                    Prophet
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Time-series forecasting
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <p className="px-8 text-center text-sm text-muted-foreground">
            © 2025 Independent Marketing Sciences
          </p>
          </div>
        </div>
      </div>
    </div>
  );
}
