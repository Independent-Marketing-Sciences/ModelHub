"use client";

import { useEffect, useState, useCallback } from "react";
import { useDataStore } from "@/lib/store";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import Papa from "papaparse";

export function NamingConventionTab() {
  const { namingConvention, setNamingConvention, isLoading, setIsLoading } = useDataStore();
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredData, setFilteredData] = useState(namingConvention);

  const loadNamingConvention = useCallback(async () => {
    setIsLoading(true);
    try {
      // In production, this would load from the actual Excel file
      // For now, we'll use a placeholder
      const placeholderData = [
        {
          Category: "Brand",
          Subcategory: "Display",
          Channel: "Google Display",
          Campaign: "Brand Awareness",
          Description: "General brand awareness campaign",
        },
        {
          Category: "Performance",
          Subcategory: "Search",
          Channel: "Google Search",
          Campaign: "Conversion Campaign",
          Description: "High-intent keyword targeting",
        },
      ];
      setNamingConvention(placeholderData);
    } catch (error) {
      console.error("Error loading naming convention:", error);
    } finally {
      setIsLoading(false);
    }
  }, [setIsLoading, setNamingConvention]);

  useEffect(() => {
    // Load naming convention data
    if (namingConvention.length === 0) {
      loadNamingConvention();
    }
  }, [namingConvention.length, loadNamingConvention]);

  useEffect(() => {
    // Filter data based on search term
    if (searchTerm) {
      const filtered = namingConvention.filter((row) =>
        Object.values(row).some((value) =>
          String(value).toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
      setFilteredData(filtered);
    } else {
      setFilteredData(namingConvention);
    }
  }, [searchTerm, namingConvention]);

  const columns = filteredData.length > 0 ? Object.keys(filteredData[0]) : [];

  return (
    <Card className="border-2">
      <CardHeader className="bg-gradient-to-r from-slate-50 to-purple-50">
        <CardTitle className="text-xl">Naming Convention Reference</CardTitle>
        <CardDescription>
          Search and filter the project naming convention lookup table
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="space-y-4">
          <Input
            placeholder="Search naming convention..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />

          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading naming convention...
            </div>
          ) : filteredData.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No data available. Please upload a naming convention file.
            </div>
          ) : (
            <div className="rounded-md border overflow-auto max-h-[600px]">
              <table className="w-full text-sm">
                <thead className="bg-muted sticky top-0">
                  <tr>
                    {columns.map((col) => (
                      <th
                        key={col}
                        className="px-4 py-3 text-left font-medium border-b"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((row, idx) => (
                    <tr key={idx} className="hover:bg-muted/50">
                      {columns.map((col) => (
                        <td key={col} className="px-4 py-2 border-b">
                          {String(row[col] || "")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="text-sm text-muted-foreground">
            Showing {filteredData.length} of {namingConvention.length} rows
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
