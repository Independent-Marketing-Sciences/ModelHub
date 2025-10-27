"use client";

import { useState } from "react";
import { useDataStore } from "@/lib/store/index";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DataViewTab } from "@/features/data-view/components/DataViewTab";
import { ChartingToolTab } from "@/features/transformations/components/ChartingToolTab";
import { CorrelationTab } from "@/features/correlation/components/CorrelationTab";
import { ProphetSeasonalityTab } from "@/features/prophet/components/ProphetSeasonalityTab";
import { FeatureExtractionTab } from "@/features/feature-extraction/components/FeatureExtractionTab";
import { OutlierDetectionTab } from "@/features/outlier-detection/components/OutlierDetectionTab";
import { DateRangeSelector } from "@/components/data/DateRangeSelector";
import { ThemeToggle } from "@/components/theme-toggle";
import { ThemeLogo } from "@/components/ThemeLogo";
import { ArrowLeft, Database, ChevronLeft, ChevronRight, Settings } from "lucide-react";
import { useTheme } from "next-themes";

interface MainDashboardProps {
  onBackToHome: () => void;
}

export function MainDashboard({ onBackToHome }: MainDashboardProps) {
  const { data, setData, setColumns, setError, setIsLoading } = useDataStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedSidebarTab, setSelectedSidebarTab] = useState("modelling-mate");
  const { resolvedTheme } = useTheme();

  const handleNewDataset = async () => {
    // Check if running in Electron
    if (typeof window !== 'undefined' && window.electron) {
      try {
        const filePath = await window.electron.openFile();

        if (filePath) {
          // Import libraries dynamically
          const Papa = (await import('papaparse')).default;
          const XLSX = await import('xlsx');

          setIsLoading(true);
          setError(null);

          // Read file using Electron IPC (not direct fs access)
          const base64Data = await window.electron.readFile(filePath);
          const buffer = Buffer.from(base64Data, 'base64');
          const fileExtension = filePath.split('.').pop()?.toLowerCase();

          if (fileExtension === 'csv') {
            const text = buffer.toString('utf-8');
            Papa.parse(text, {
              header: true,
              dynamicTyping: true,
              skipEmptyLines: true,
              complete: (results: any) => {
                if (results.data && results.data.length > 0) {
                  const columns = Object.keys(results.data[0] as object);
                  setColumns(columns);
                  setData(results.data as any[]);
                  setIsLoading(false);
                } else {
                  setError("No data found in CSV file");
                  setIsLoading(false);
                }
              },
              error: (error: any) => {
                setError(`Error parsing CSV: ${error.message}`);
                setIsLoading(false);
              },
            });
          } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
            try {
              const workbook = XLSX.read(buffer, { type: 'buffer' });
              const firstSheetName = workbook.SheetNames[0];
              const worksheet = workbook.Sheets[firstSheetName];
              const jsonData = XLSX.utils.sheet_to_json(worksheet);

              if (jsonData && jsonData.length > 0) {
                const columns = Object.keys(jsonData[0] as object);
                setColumns(columns);
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
          }
        }
      } catch (error) {
        console.error('Error opening file:', error);
        setError('Failed to open file');
        setIsLoading(false);
      }
    } else {
      // Fallback: go back to home page for browser upload
      setData([]);
      setColumns([]);
      onBackToHome();
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Collapsible Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-40 h-screen border-r bg-background transition-all duration-150 ease-in-out ${
          sidebarOpen ? "w-80" : "w-16"
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Header - Logo */}
          {sidebarOpen ? (
            <div className="border-b bg-muted/30">
              <div className="py-6 px-4 flex justify-center">
                <ThemeLogo
                  width={resolvedTheme === 'dark' ? 120 : 160}
                  height={resolvedTheme === 'dark' ? 48 : 64}
                  className="flex-shrink-0"
                />
              </div>
              <div className="px-4 pb-3 flex justify-end">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setSidebarOpen(false)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex h-14 items-center justify-center border-b bg-muted/30">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setSidebarOpen(true)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Sidebar Content */}
          <div className="flex-1 overflow-y-auto">
            {sidebarOpen && (
              <div className="flex flex-col h-full">
                {/* Top Section - Date Filter */}
                <div className="p-4 border-b">
                  <h3 className="text-xs font-semibold mb-3 text-muted-foreground uppercase tracking-wider">
                    Date Filter
                  </h3>
                  <DateRangeSelector />
                </div>

                {/* Navigation Tabs */}
                <div className="p-4 border-b">
                  <h3 className="text-xs font-semibold mb-3 text-muted-foreground uppercase tracking-wider">
                    Navigation
                  </h3>
                  <Button
                    variant={selectedSidebarTab === "modelling-mate" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedSidebarTab("modelling-mate")}
                    className="w-full justify-start"
                  >
                    <Database className="mr-2 h-4 w-4" />
                    Modelling Mate
                  </Button>
                </div>

                {/* Spacer to push bottom content down */}
                <div className="flex-1"></div>

                {/* Bottom Section - Actions & Theme */}
                <div className="border-t">
                  {/* Actions */}
                  <div className="p-4 border-b">
                    <h3 className="text-xs font-semibold mb-3 text-muted-foreground uppercase tracking-wider">
                      Actions
                    </h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleNewDataset}
                      className="w-full justify-start"
                    >
                      <ArrowLeft className="mr-2 h-4 w-4" />
                      New Dataset
                    </Button>
                  </div>

                  {/* Theme */}
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Theme
                      </span>
                      <ThemeToggle />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className={`flex-1 transition-all duration-150 ease-in-out ${sidebarOpen ? "ml-80" : "ml-16"}`}>
        <div className="w-full px-8 py-6">
          {selectedSidebarTab === "modelling-mate" && (
            <Tabs defaultValue="data" className="space-y-6">
              <TabsList>
                <TabsTrigger value="data">
                  Data View
                </TabsTrigger>
                <TabsTrigger value="charting">
                  Charting
                </TabsTrigger>
                <TabsTrigger value="correlation">
                  Correlation
                </TabsTrigger>
                <TabsTrigger value="outliers">
                  Outliers
                </TabsTrigger>
                <TabsTrigger value="feature-extraction">
                  Feature Extraction
                </TabsTrigger>
                <TabsTrigger value="prophet">
                  Prophet
                </TabsTrigger>
              </TabsList>

              <TabsContent value="data" className="space-y-4 mt-0">
                <DataViewTab />
              </TabsContent>

              <TabsContent value="charting" className="space-y-4 mt-0">
                <ChartingToolTab />
              </TabsContent>

              <TabsContent value="correlation" className="space-y-4 mt-0">
                <CorrelationTab />
              </TabsContent>

              <TabsContent value="outliers" className="space-y-4 mt-0">
                <OutlierDetectionTab />
              </TabsContent>

              <TabsContent value="feature-extraction" className="space-y-4 mt-0">
                <FeatureExtractionTab />
              </TabsContent>

              <TabsContent value="prophet" className="space-y-4 mt-0">
                <ProphetSeasonalityTab />
              </TabsContent>
            </Tabs>
          )}
        </div>
      </div>
    </div>
  );
}
