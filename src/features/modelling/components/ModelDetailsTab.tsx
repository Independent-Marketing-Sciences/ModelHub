"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDataStore } from "@/lib/store";
import { useModellingStore } from "@/lib/store/modelling-store";
import { CheckCircle2, Upload } from "lucide-react";

interface ModelDetailsTabProps {
  onModelConfigured: (configured: boolean) => void;
}

interface ModelDetail {
  parameter: string;
  value: string;
  editable: boolean;
}

export function ModelDetailsTab({ onModelConfigured }: ModelDetailsTabProps) {
  const { columns, data, dateColumn } = useDataStore();
  const { modelConfig, setModelConfig } = useModellingStore();

  // Get date range from dataset
  const dateRange = useMemo(() => {
    if (!data.length || !dateColumn) return { min: "", max: "" };

    const dates = data
      .map(row => row[dateColumn])
      .filter(date => date != null && date !== "")
      .map(date => String(date));

    if (dates.length === 0) return { min: "", max: "" };

    const sortedDates = dates.sort();
    return {
      min: sortedDates[0],
      max: sortedDates[sortedDates.length - 1]
    };
  }, [data, dateColumn]);

  // Initialize model details as table rows with dataset date range
  const [modelDetails, setModelDetails] = useState<ModelDetail[]>([
    { parameter: "Regression Approach", value: "OLS", editable: true },
    { parameter: "KPI", value: "", editable: true },
    { parameter: "Start Date", value: dateRange.min, editable: true },
    { parameter: "End Date", value: dateRange.max, editable: true },
    { parameter: "XS Weights", value: "weights", editable: true },
    { parameter: "Log Trans Bias", value: "no", editable: true },
    { parameter: "Take Anti-logs at Midpoints", value: "yes", editable: true },
  ]);

  // Update dates when dataset changes
  useEffect(() => {
    if (dateRange.min && dateRange.max && !modelConfig) {
      setModelDetails(prev => prev.map(row => {
        if (row.parameter === "Start Date") return { ...row, value: dateRange.min };
        if (row.parameter === "End Date") return { ...row, value: dateRange.max };
        return row;
      }));
    }
  }, [dateRange.min, dateRange.max, modelConfig]);

  // Load existing config if available
  useEffect(() => {
    if (modelConfig) {
      setModelDetails([
        { parameter: "Regression Approach", value: "OLS", editable: true },
        { parameter: "KPI", value: modelConfig.kpi, editable: true },
        { parameter: "Start Date", value: modelConfig.start_date, editable: true },
        { parameter: "End Date", value: modelConfig.end_date, editable: true },
        { parameter: "XS Weights", value: modelConfig.xs_weights, editable: true },
        { parameter: "Log Trans Bias", value: modelConfig.log_trans_bias ? "yes" : "no", editable: true },
        { parameter: "Take Anti-logs at Midpoints", value: modelConfig.take_anti_logs_at_midpoints ? "yes" : "no", editable: true },
      ]);
    }
  }, [modelConfig]);

  const updateValue = (parameter: string, newValue: string) => {
    setModelDetails((prev) =>
      prev.map((row) =>
        row.parameter === parameter ? { ...row, value: newValue } : row
      )
    );
  };

  const handleApply = () => {
    const detailsMap = Object.fromEntries(
      modelDetails.map((d) => [d.parameter, d.value])
    );

    if (!detailsMap["KPI"] || !detailsMap["Start Date"] || !detailsMap["End Date"]) {
      alert("Please fill in KPI, Start Date, and End Date");
      return;
    }

    const config = {
      kpi: detailsMap["KPI"],
      start_date: detailsMap["Start Date"],
      end_date: detailsMap["End Date"],
      xs_weights: detailsMap["XS Weights"] || "weights",
      log_trans_bias: detailsMap["Log Trans Bias"]?.toLowerCase() === "yes",
      take_anti_logs_at_midpoints: detailsMap["Take Anti-logs at Midpoints"]?.toLowerCase() === "yes",
    };

    setModelConfig(config);
    onModelConfigured(true);
  };

  const handleImportExcel = async () => {
    // TODO: Implement Excel import
    alert("Excel import coming soon!");
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Model Details</CardTitle>
            <CardDescription>
              Configure your regression model parameters (editable table format)
            </CardDescription>
          </div>
          <Button variant="outline" onClick={handleImportExcel}>
            <Upload className="mr-2 h-4 w-4" />
            Import from Excel
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Editable Table */}
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left font-medium w-1/3">Parameter</th>
                <th className="px-4 py-3 text-left font-medium">Value</th>
              </tr>
            </thead>
            <tbody>
              {modelDetails.map((row) => (
                <tr key={row.parameter} className="border-t hover:bg-muted/50">
                  <td className="px-4 py-3 font-medium">{row.parameter}</td>
                  <td className="px-4 py-2">
                    <Input
                      value={row.value}
                      onChange={(e) => updateValue(row.parameter, e.target.value)}
                      disabled={!row.editable}
                      className="h-8"
                      placeholder={`Enter ${row.parameter.toLowerCase()}...`}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Available columns hint */}
        <div className="text-xs text-muted-foreground p-3 bg-muted/30 rounded-md">
          <p className="font-medium mb-1">Available columns in dataset:</p>
          <p className="font-mono">{columns.join(", ")}</p>
        </div>

        {/* Apply Button */}
        <div className="flex justify-end gap-2">
          <Button onClick={handleApply}>
            Apply Configuration
          </Button>
        </div>

        {/* Success Message */}
        {modelConfig && (
          <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-md p-3 flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-green-800 dark:text-green-300">
              Model configuration saved! Proceed to Variable Details.
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="text-xs text-muted-foreground space-y-1">
          <p><strong>Regression Approach:</strong> OLS, Ridge, Lasso</p>
          <p><strong>Date format:</strong> YYYY-MM-DD (e.g., 2021-01-01)</p>
          <p><strong>XS Weights:</strong> "weights" or column name</p>
          <p><strong>Boolean values:</strong> "yes" or "no"</p>
        </div>
      </CardContent>
    </Card>
  );
}
