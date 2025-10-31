"use client";

import { useState, useMemo, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useDataStore } from "@/lib/store";
import { useModellingStore } from "@/lib/store/modelling-store";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import dayjs from "dayjs";

interface ModelDetailsTabProps {
  onModelConfigured: (configured: boolean) => void;
}

export function ModelDetailsTab({ onModelConfigured }: ModelDetailsTabProps) {
  const { data, columns, dateColumn } = useDataStore();
  const { modelConfig, setModelConfig, initializeVariableTransformations } = useModellingStore();

  // Get numeric columns for KPI selection
  const numericColumns = useMemo(() => {
    return columns.filter(col => {
      if (data.length === 0) return false;
      const sampleValue = data[0][col];
      return typeof sampleValue === 'number' || !isNaN(parseFloat(String(sampleValue)));
    });
  }, [columns, data]);

  const [selectedKPI, setSelectedKPI] = useState(modelConfig?.kpi || "");
  const [startDate, setStartDate] = useState(modelConfig?.start_date || "");
  const [endDate, setEndDate] = useState(modelConfig?.end_date || "");
  const [xsWeights, setXsWeights] = useState(modelConfig?.xs_weights || "weights");
  const [logTransBias, setLogTransBias] = useState(modelConfig?.log_trans_bias ? "yes" : "no");
  const [antiLogsAtMidpoints, setAntiLogsAtMidpoints] = useState(modelConfig?.take_anti_logs_at_midpoints ? "yes" : "no");

  // Get available dates from the dataset
  const availableDates = useMemo(() => {
    if (!data.length || !dateColumn) return [];
    const dates = data
      .map((row) => row[dateColumn])
      .filter((date) => date != null && date !== "")
      .map((date) => String(date));
    return Array.from(new Set(dates)).sort();
  }, [data, dateColumn]);

  const handleApply = () => {
    if (!selectedKPI || !startDate || !endDate) {
      alert("Please fill in all required fields");
      return;
    }

    // Save to store
    const config = {
      kpi: selectedKPI,
      start_date: startDate,
      end_date: endDate,
      xs_weights: xsWeights,
      log_trans_bias: logTransBias === "yes",
      take_anti_logs_at_midpoints: antiLogsAtMidpoints === "yes",
    };

    setModelConfig(config);

    // Initialize variable transformations for all numeric columns
    initializeVariableTransformations(numericColumns);

    // Emit model configuration
    onModelConfigured(true);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Model Details</CardTitle>
        <CardDescription>
          Configure your regression model parameters
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* KPI Selection */}
        <div className="space-y-2">
          <Label htmlFor="kpi">Target Variable (KPI) *</Label>
          <SearchableSelect
            value={selectedKPI}
            onValueChange={setSelectedKPI}
            options={numericColumns.map(col => ({ value: col, label: col }))}
            placeholder="Select target variable..."
          />
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start-date">Start Date *</Label>
            <Select value={startDate} onValueChange={setStartDate}>
              <SelectTrigger>
                <SelectValue placeholder="Select start date" />
              </SelectTrigger>
              <SelectContent>
                {availableDates.slice(0, 50).map((date) => (
                  <SelectItem key={date} value={date}>
                    {dayjs(date).format('DD/MM/YYYY')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="end-date">End Date *</Label>
            <Select value={endDate} onValueChange={setEndDate}>
              <SelectTrigger>
                <SelectValue placeholder="Select end date" />
              </SelectTrigger>
              <SelectContent>
                {availableDates.slice(-50).map((date) => (
                  <SelectItem key={date} value={date}>
                    {dayjs(date).format('DD/MM/YYYY')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Cross-Section Weights */}
        <div className="space-y-2">
          <Label htmlFor="xs-weights">Cross-Section Weights</Label>
          <Select value={xsWeights} onValueChange={setXsWeights}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="weights">Weights</SelectItem>
              <SelectItem value="none">None</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Log Transformation Bias */}
        <div className="space-y-2">
          <Label htmlFor="log-trans-bias">Log Transformation Bias</Label>
          <Select value={logTransBias} onValueChange={setLogTransBias}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="yes">Yes</SelectItem>
              <SelectItem value="no">No</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Anti-logs at Midpoints */}
        <div className="space-y-2">
          <Label htmlFor="anti-logs">Take Anti-logs at Midpoints</Label>
          <Select value={antiLogsAtMidpoints} onValueChange={setAntiLogsAtMidpoints}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="yes">Yes</SelectItem>
              <SelectItem value="no">No</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Apply Button */}
        <div className="flex justify-end">
          <Button onClick={handleApply} disabled={!selectedKPI || !startDate || !endDate}>
            Apply Model Configuration
          </Button>
        </div>

        {modelConfig ? (
          <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-md p-3 flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-green-800 dark:text-green-300">
              Model configuration saved! You can now proceed to Variable Details to configure transformations.
            </div>
          </div>
        ) : (
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-blue-800 dark:text-blue-300">
              Configure your model details here before proceeding to variable details and running the regression.
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
