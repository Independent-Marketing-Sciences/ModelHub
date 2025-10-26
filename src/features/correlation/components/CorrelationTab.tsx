"use client";

import { useState, useMemo } from "react";
import { useDataStore } from "@/lib/store/index";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { Loader2, TrendingUp, AlertCircle, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ZAxis } from "recharts";
import { pythonClient, CorrelationResult } from "@/lib/api/python-client";

type SortOrder = 'desc' | 'asc' | 'abs-desc' | 'abs-asc';

export function CorrelationTab() {
  const { columns, getFilteredData } = useDataStore();
  const [selectedVariable, setSelectedVariable] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [correlationResults, setCorrelationResults] = useState<CorrelationResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>('abs-desc');

  // Get data filtered by date range from store
  const data = getFilteredData();

  // Get numeric columns only, excluding "OBS"
  const numericColumns = columns.filter(col => {
    if (col.toUpperCase() === "OBS") return false;
    if (data.length === 0) return false;
    const sampleValue = data[0][col];
    return typeof sampleValue === 'number' || !isNaN(parseFloat(String(sampleValue)));
  });

  const handleCalculate = async () => {
    if (!selectedVariable) {
      setError("Please select a variable");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Check if Python backend is available
      const isBackendAvailable = await pythonClient.isAvailable();
      if (!isBackendAvailable) {
        throw new Error(
          "Python backend is not running. Please start the backend server:\n" +
          "1. Open terminal in python-backend folder\n" +
          "2. Run: python main.py\n" +
          "The backend should run on http://localhost:8000"
        );
      }

      // Prepare data for all numeric columns
      const variables: Record<string, number[]> = {};

      // Process all data in a single pass for better performance
      const processedData: Record<string, number[]> = {};

      // Initialize arrays
      numericColumns.forEach(col => {
        processedData[col] = [];
      });

      // Single pass through data
      data.forEach(row => {
        numericColumns.forEach(col => {
          const val = row[col];
          const numVal = typeof val === 'number' ? val : parseFloat(String(val));
          if (!isNaN(numVal)) {
            processedData[col].push(numVal);
          }
        });
      });

      // Add to variables object
      Object.keys(processedData).forEach(col => {
        if (processedData[col].length > 0) {
          variables[col] = processedData[col];
        }
      });

      // Call Python backend to get ranked correlations
      const result = await pythonClient.correlationRanked({
        target_variable: selectedVariable,
        variables
      });

      setCorrelationResults(result.correlations);
    } catch (err) {
      console.error("Correlation error:", err);
      setError(err instanceof Error ? err.message : "Failed to calculate correlations");
    } finally {
      setIsLoading(false);
    }
  };

  const getCorrelationColor = (value: number) => {
    const abs = Math.abs(value);
    if (abs >= 0.7) return value > 0 ? "bg-green-600 dark:bg-green-700 text-white" : "bg-red-600 dark:bg-red-700 text-white";
    if (abs >= 0.4) return value > 0 ? "bg-green-400 dark:bg-green-600 text-white" : "bg-red-400 dark:bg-red-600 text-white";
    if (abs >= 0.2) return value > 0 ? "bg-green-200 dark:bg-green-900/50 text-green-900 dark:text-green-300" : "bg-red-200 dark:bg-red-900/50 text-red-900 dark:text-red-300";
    return "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-300";
  };

  // Sort correlation results based on sort order
  const sortedCorrelationResults = useMemo(() => {
    if (correlationResults.length === 0) return [];

    const sorted = [...correlationResults];

    switch (sortOrder) {
      case 'asc':
        // Sort by correlation ascending (most negative to most positive)
        return sorted.sort((a, b) => a.correlation - b.correlation);
      case 'desc':
        // Sort by correlation descending (most positive to most negative)
        return sorted.sort((a, b) => b.correlation - a.correlation);
      case 'abs-asc':
        // Sort by absolute value ascending (weakest to strongest)
        return sorted.sort((a, b) => Math.abs(a.correlation) - Math.abs(b.correlation));
      case 'abs-desc':
      default:
        // Sort by absolute value descending (strongest to weakest) - default
        return sorted.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
    }
  }, [correlationResults, sortOrder]);

  const cycleSortOrder = () => {
    const orders: SortOrder[] = ['abs-desc', 'abs-asc', 'desc', 'asc'];
    const currentIndex = orders.indexOf(sortOrder);
    const nextIndex = (currentIndex + 1) % orders.length;
    setSortOrder(orders[nextIndex]);
  };

  const getSortLabel = () => {
    switch (sortOrder) {
      case 'abs-desc': return 'Absolute (Strongest First)';
      case 'abs-asc': return 'Absolute (Weakest First)';
      case 'desc': return 'Value (High to Low)';
      case 'asc': return 'Value (Low to High)';
    }
  };

  // Prepare bubble chart data for media variables
  const bubbleChartData = useMemo(() => {
    if (!selectedVariable || correlationResults.length === 0) {
      console.log('[CorrelationTab] No bubble chart data: selectedVariable=', selectedVariable, 'correlationResults.length=', correlationResults.length);
      return [];
    }

    // Filter for media spend variables
    const mediaResults = correlationResults.filter(result =>
      result.variable.toLowerCase().startsWith('media_') &&
      result.variable.toLowerCase().endsWith('_spd')
    );

    console.log('[CorrelationTab] Found media variables:', mediaResults.length, mediaResults.map(r => r.variable));

    // Get the spend values for each media variable
    const chartData = mediaResults.map(result => {
      // Calculate average spend for bubble size
      const spendValues = data.map(row => {
        const val = row[result.variable];
        return typeof val === 'number' ? val : parseFloat(String(val)) || 0;
      });
      const avgSpend = spendValues.reduce((a, b) => a + b, 0) / spendValues.length;

      return {
        name: result.variable.replace(/^media_/, '').replace(/_spd$/, ''),
        correlation: result.correlation,
        spend: avgSpend,
        size: avgSpend, // bubble size
        fullName: result.variable
      };
    });

    console.log('[CorrelationTab] Bubble chart data:', chartData);
    return chartData;
  }, [selectedVariable, correlationResults, data]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Correlation Analysis</CardTitle>
          <CardDescription>
            Analyze correlations between variables with ranked results (OBS excluded)
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-6">
            {data.length === 0 && (
              <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5" />
                <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
                  No data loaded. Please upload a dataset first.
                </div>
              </div>
            )}

            {/* Variable Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Select Target Variable
              </label>
              <SearchableSelect
                value={selectedVariable}
                onValueChange={setSelectedVariable}
                options={numericColumns.map(col => ({ value: col, label: col }))}
                placeholder="Choose a variable..."
              />
              {selectedVariable && (
                <p className="text-xs text-muted-foreground mt-2">
                  Will show correlations between <strong>{selectedVariable}</strong> and all other numeric variables
                </p>
              )}
            </div>

            {error && (
              <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-md p-3 text-sm text-red-800 dark:text-red-300 whitespace-pre-line">
                {error}
              </div>
            )}

            {/* Calculate Button */}
            <div className="flex justify-center">
              <Button
                onClick={handleCalculate}
                disabled={isLoading || !selectedVariable || data.length === 0}
                size="lg"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Calculating...
                  </>
                ) : (
                  "Calculate Correlations"
                )}
              </Button>
            </div>

            {/* Correlation Results */}
            {correlationResults.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">
                    Correlations with <span className="font-semibold">{selectedVariable}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={cycleSortOrder}
                    className="flex items-center gap-2"
                  >
                    <ArrowUpDown className="h-4 w-4" />
                    Sort: {getSortLabel()}
                  </Button>
                </div>

                <div className="rounded-md border overflow-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-muted/50">
                        <th className="border-b p-3 text-left text-sm font-medium">Rank</th>
                        <th className="border-b p-3 text-left text-sm font-medium">Variable</th>
                        <th className="border-b p-3 text-center text-sm font-medium">Correlation</th>
                        <th className="border-b p-3 text-center text-sm font-medium">Strength</th>
                        <th className="border-b p-3 text-center text-sm font-medium">p-value</th>
                        <th className="border-b p-3 text-center text-sm font-medium">Significance</th>
                      </tr>
                    </thead>
                    <tbody className="bg-background">
                      {sortedCorrelationResults.map((result, idx) => (
                        <tr key={result.variable} className="hover:bg-muted/50">
                          <td className="border-b p-3 text-center font-semibold text-muted-foreground">
                            {idx + 1}
                          </td>
                          <td className="border-b p-3 font-medium">
                            {result.variable}
                          </td>
                          <td className="border-b p-3 text-center">
                            <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${getCorrelationColor(result.correlation)}`}>
                              {result.correlation.toFixed(3)}
                            </span>
                          </td>
                          <td className="border-b p-3 text-center text-sm">
                            {result.strength}
                            <span className="text-muted-foreground ml-1">
                              ({result.correlation > 0 ? '+' : '-'})
                            </span>
                          </td>
                          <td className="border-b p-3 text-center text-sm font-mono">
                            {result.p_value.toFixed(4)}
                          </td>
                          <td className="border-b p-3 text-center">
                            {result.p_value < 0.001 ? (
                              <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded font-semibold">
                                ***
                              </span>
                            ) : result.p_value < 0.01 ? (
                              <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded font-semibold">
                                **
                              </span>
                            ) : result.p_value < 0.05 ? (
                              <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded font-semibold">
                                *
                              </span>
                            ) : (
                              <span className="text-xs px-2 py-1 bg-muted text-muted-foreground rounded">
                                n.s.
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Legend */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs p-4 bg-muted/50 rounded-lg">
                  <div>
                    <div className="font-medium mb-2">Correlation Strength:</div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-green-600"></div>
                        <span>Strong Positive (≥0.7)</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-green-400"></div>
                        <span>Moderate Positive (0.4-0.7)</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-green-200 border"></div>
                        <span>Weak Positive (0.2-0.4)</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-red-200 border"></div>
                        <span>Weak Negative (-0.2 to -0.4)</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-red-400"></div>
                        <span>Moderate Negative (-0.4 to -0.7)</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-red-600"></div>
                        <span>Strong Negative (≤-0.7)</span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <div className="font-medium mb-2">Statistical Significance:</div>
                    <div className="space-y-1">
                      <div><span className="font-semibold">***</span> = p &lt; 0.001 (Highly significant)</div>
                      <div><span className="font-semibold">**</span> = p &lt; 0.01 (Very significant)</div>
                      <div><span className="font-semibold">*</span> = p &lt; 0.05 (Significant)</div>
                      <div><span className="font-semibold">n.s.</span> = p ≥ 0.05 (Not significant)</div>
                    </div>
                  </div>
                </div>

                {/* Media Spend Bubble Chart */}
                {bubbleChartData.length > 0 && (
                  <div className="border rounded-lg p-6 bg-card mt-6">
                    <div className="mb-4">
                      <h3 className="text-sm font-medium">Media Spend vs Correlation</h3>
                      <p className="text-sm text-muted-foreground">
                        Bubble size represents average spend amount
                      </p>
                    </div>
                    <div className="h-[400px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                          <XAxis
                            type="number"
                            dataKey="correlation"
                            name="Correlation"
                            label={{ value: 'Correlation with KPI', position: 'insideBottom', offset: -10, fill: 'currentColor' }}
                            domain={[-1, 1]}
                            tick={{ fill: 'currentColor' }}
                            className="text-gray-700 dark:text-gray-300"
                          />
                          <YAxis
                            type="number"
                            dataKey="spend"
                            name="Avg Spend"
                            label={{ value: 'Average Spend', angle: -90, position: 'insideLeft', fill: 'currentColor' }}
                            tick={{ fill: 'currentColor' }}
                            className="text-gray-700 dark:text-gray-300"
                          />
                          <ZAxis type="number" dataKey="size" range={[100, 1000]} />
                          <Tooltip
                            cursor={{ strokeDasharray: '3 3' }}
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const data = payload[0].payload;
                                return (
                                  <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded shadow-sm">
                                    <p className="font-semibold text-gray-900 dark:text-white">{data.fullName}</p>
                                    <p className="text-sm text-gray-700 dark:text-gray-300">Correlation: {data.correlation.toFixed(3)}</p>
                                    <p className="text-sm text-gray-700 dark:text-gray-300">Avg Spend: {data.spend.toFixed(2)}</p>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Legend wrapperStyle={{ color: 'inherit' }} className="text-gray-700 dark:text-gray-300" />
                          <Scatter
                            name="Media Variables"
                            data={bubbleChartData}
                            fill="#3b82f6"
                            fillOpacity={0.6}
                          />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            )}

            {correlationResults.length === 0 && !isLoading && (
              <div className="text-center py-12 text-muted-foreground border rounded-lg bg-muted/30">
                <p className="text-base mb-2">No correlation analysis yet</p>
                <p className="text-sm">
                  Select a variable and click Calculate to see ranked correlations
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
