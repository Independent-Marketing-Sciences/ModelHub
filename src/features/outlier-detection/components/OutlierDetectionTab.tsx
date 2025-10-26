"use client";

import { useMemo, useState } from "react";
import { useDataStore } from "@/lib/store";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Download } from "lucide-react";
import * as XLSX from "xlsx";

interface OutlierInfo {
  variable: string;
  date: string;
  value: number;
  mean: number;
  stdDev: number;
  zScore: number;
  deviations: number;
}

export function OutlierDetectionTab() {
  const { getFilteredData, columns, dateColumn } = useDataStore();
  const [variableFilter, setVariableFilter] = useState("");
  const [deviationThreshold, setDeviationThreshold] = useState(3);

  const dateFilteredData = getFilteredData();

  // Detect date column
  const detectedDateColumn = useMemo(() => {
    const dateColumnNames = ['OBS', 'obs', 'Date', 'date'];
    return columns.find(col => dateColumnNames.includes(col)) || dateColumn || '';
  }, [columns, dateColumn]);

  // Calculate outliers for all numeric variables
  const outlierAnalysis = useMemo(() => {
    if (dateFilteredData.length === 0 || !detectedDateColumn) return [];

    const excludedColumns = ['OBS', 'obs', 'Date', 'date'];
    const allOutliers: OutlierInfo[] = [];

    columns.forEach(col => {
      if (excludedColumns.includes(col)) return;

      const sampleValue = dateFilteredData[0]?.[col];
      const isNumeric = typeof sampleValue === 'number' || !isNaN(parseFloat(String(sampleValue)));

      if (isNumeric) {
        const values = dateFilteredData.map(row => {
          const val = row[col];
          return typeof val === 'number' ? val : parseFloat(String(val)) || 0;
        });

        // Calculate mean and standard deviation
        const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
        const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
        const stdDev = Math.sqrt(variance);

        // Find outliers
        dateFilteredData.forEach((row, idx) => {
          const value = values[idx];
          const zScore = stdDev !== 0 ? (value - mean) / stdDev : 0;
          const deviations = Math.abs(zScore);

          if (deviations >= deviationThreshold) {
            allOutliers.push({
              variable: col,
              date: String(row[detectedDateColumn] || ''),
              value,
              mean,
              stdDev,
              zScore,
              deviations
            });
          }
        });
      }
    });

    // Sort by deviation magnitude (highest first)
    return allOutliers.sort((a, b) => b.deviations - a.deviations);
  }, [dateFilteredData, columns, detectedDateColumn, deviationThreshold]);

  // Filter outliers by variable name
  const filteredOutliers = useMemo(() => {
    if (!variableFilter) return outlierAnalysis;
    return outlierAnalysis.filter(outlier =>
      outlier.variable.toLowerCase().includes(variableFilter.toLowerCase())
    );
  }, [outlierAnalysis, variableFilter]);

  // Summary statistics
  const summary = useMemo(() => {
    const variableOutlierCounts: Record<string, number> = {};
    outlierAnalysis.forEach(outlier => {
      variableOutlierCounts[outlier.variable] = (variableOutlierCounts[outlier.variable] || 0) + 1;
    });

    const topVariables = Object.entries(variableOutlierCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    return {
      totalOutliers: outlierAnalysis.length,
      affectedVariables: Object.keys(variableOutlierCounts).length,
      topVariables
    };
  }, [outlierAnalysis]);

  const handleExport = () => {
    if (filteredOutliers.length === 0) return;

    const exportData = filteredOutliers.map(outlier => ({
      'Variable': outlier.variable,
      'Date': outlier.date,
      'Value': outlier.value,
      'Mean': outlier.mean,
      'Std Dev': outlier.stdDev,
      'Z-Score': outlier.zScore,
      'Deviations': outlier.deviations
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Outliers");

    XLSX.writeFile(workbook, `outliers_${deviationThreshold}sd_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  if (dateFilteredData.length === 0) {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Outlier Detection</CardTitle>
            <CardDescription>
              Identify data points that deviate significantly from the mean
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-muted-foreground">
              <p className="text-lg mb-2">No data loaded</p>
              <p className="text-sm">Upload a dataset to detect outliers</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Outlier Detection</CardTitle>
          <CardDescription>
            Identify data points beyond {deviationThreshold} standard deviations from the mean
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {/* Controls */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Deviation Threshold</label>
                <Input
                  type="number"
                  min="1"
                  max="5"
                  step="0.5"
                  value={deviationThreshold}
                  onChange={(e) => setDeviationThreshold(Math.max(1, Math.min(5, parseFloat(e.target.value) || 3)))}
                  className="w-32"
                />
              </div>
              <div className="text-xs text-muted-foreground mt-6">
                Detecting values beyond ±{deviationThreshold} standard deviations
              </div>
            </div>
            <Button
              onClick={handleExport}
              disabled={filteredOutliers.length === 0}
            >
              <Download className="mr-2 h-4 w-4" />
              Export Outliers
            </Button>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Outliers</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.totalOutliers.toLocaleString()}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Affected Variables</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.affectedVariables}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Detection Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {((summary.totalOutliers / dateFilteredData.length) * 100).toFixed(2)}%
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Top Variables with Outliers */}
          {summary.topVariables.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium mb-3">Top Variables with Most Outliers</h3>
              <div className="grid grid-cols-5 gap-2">
                {summary.topVariables.map(([variable, count]) => (
                  <Card key={variable} className="p-3">
                    <div className="text-xs text-muted-foreground truncate" title={variable}>{variable}</div>
                    <div className="text-lg font-bold">{count}</div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Outliers Table */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium">Detected Outliers</h3>
                <p className="text-sm text-muted-foreground">
                  All data points exceeding the deviation threshold
                </p>
              </div>
              <Input
                placeholder="Filter by variable..."
                value={variableFilter}
                onChange={(e) => setVariableFilter(e.target.value)}
                className="max-w-xs"
              />
            </div>

            {filteredOutliers.length > 0 ? (
              <div className="rounded-md border overflow-auto max-h-[600px]">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium border-b whitespace-nowrap">
                        Variable
                      </th>
                      <th className="px-4 py-3 text-left font-medium border-b whitespace-nowrap">
                        Date
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Value
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Mean
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Std Dev
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Z-Score
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Deviations
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-background">
                    {filteredOutliers.map((outlier, idx) => (
                      <tr key={idx} className="hover:bg-muted/50">
                        <td className="px-4 py-2 border-b font-medium">
                          {outlier.variable}
                        </td>
                        <td className="px-4 py-2 border-b">
                          {outlier.date}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          {outlier.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          {outlier.mean.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          {outlier.stdDev.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          <span className={`inline-block px-2 py-1 rounded text-xs ${
                            outlier.zScore > 0
                              ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                              : 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300'
                          }`}>
                            {outlier.zScore > 0 ? '+' : ''}{outlier.zScore.toFixed(2)}
                          </span>
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          <span className="inline-block px-2 py-1 rounded text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300">
                            {outlier.deviations.toFixed(2)}σ
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground border rounded-md">
                <p className="text-lg mb-2">No outliers detected</p>
                <p className="text-sm">
                  {variableFilter
                    ? `No outliers found for variables matching "${variableFilter}"`
                    : `Try adjusting the deviation threshold to detect outliers`}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
