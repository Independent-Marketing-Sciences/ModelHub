"use client";

import { useState, useMemo } from "react";
import { useDataStore } from "@/lib/store/index";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { Loader2, TrendingUp, AlertCircle, ArrowUpDown, ArrowUp, ArrowDown, Calendar, X } from "lucide-react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ZAxis } from "recharts";
import { pythonClient, CorrelationResult } from "@/lib/api/python-client";
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs, { Dayjs } from 'dayjs';

type SortOrder = 'desc' | 'asc' | 'abs-desc' | 'abs-asc';

export function CorrelationTab() {
  const { columns, data: allData, dateColumn } = useDataStore();
  const [selectedVariable, setSelectedVariable] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [correlationResults, setCorrelationResults] = useState<CorrelationResult[]>([]);
  const [period1Results, setPeriod1Results] = useState<CorrelationResult[]>([]);
  const [period2Results, setPeriod2Results] = useState<CorrelationResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>('abs-desc');
  const [compareMode, setCompareMode] = useState(false);

  // Period 1 dates
  const [period1Start, setPeriod1Start] = useState<Dayjs | null>(null);
  const [period1End, setPeriod1End] = useState<Dayjs | null>(null);

  // Period 2 dates
  const [period2Start, setPeriod2Start] = useState<Dayjs | null>(null);
  const [period2End, setPeriod2End] = useState<Dayjs | null>(null);

  // Get available dates for date pickers
  const availableDates = useMemo(() => {
    if (!allData.length || !dateColumn) return [];

    const dates = allData
      .map((row) => row[dateColumn])
      .filter((date) => date != null && date !== "")
      .map((date) => String(date));

    return Array.from(new Set(dates)).sort();
  }, [allData, dateColumn]);

  const minDate = availableDates.length > 0 ? dayjs(availableDates[0]) : dayjs('2000-01-01');
  const maxDate = availableDates.length > 0 ? dayjs(availableDates[availableDates.length - 1]) : dayjs();

  // Filter data by date range
  const getDataForPeriod = (start: Dayjs | null, end: Dayjs | null) => {
    if (!start || !end || !dateColumn) return allData;

    const startStr = start.format('YYYY-MM-DD');
    const endStr = end.format('YYYY-MM-DD');

    return allData.filter(row => {
      const dateValue = row[dateColumn];
      if (!dateValue) return true;
      const dateStr = String(dateValue);
      return dateStr >= startStr && dateStr <= endStr;
    });
  };

  // Get current data based on mode
  const data = useMemo(() => {
    return allData;
  }, [allData]);

  // Get numeric columns only, excluding "OBS"
  const numericColumns = columns.filter(col => {
    if (col.toUpperCase() === "OBS") return false;
    if (data.length === 0) return false;
    const sampleValue = data[0][col];
    return typeof sampleValue === 'number' || !isNaN(parseFloat(String(sampleValue)));
  });

  const calculateCorrelations = async (dataToUse: any[]) => {
    if (!selectedVariable) {
      throw new Error("Please select a variable");
    }

    // Check if Python backend is available
    const isBackendAvailable = await pythonClient.isAvailable();
    if (!isBackendAvailable) {
      throw new Error(
        "Python backend is not running. Please start the backend server:\n" +
        "1. Open terminal in backend folder\n" +
        "2. Run: python main.py\n" +
        "The backend should run on http://localhost:8000"
      );
    }

    // Prepare data for all numeric columns
    const variables: Record<string, number[]> = {};
    const processedData: Record<string, number[]> = {};

    // Initialize arrays
    numericColumns.forEach(col => {
      processedData[col] = [];
    });

    // Single pass through data
    dataToUse.forEach(row => {
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

    return result.correlations;
  };

  const handleCalculate = async () => {
    if (!selectedVariable) {
      setError("Please select a variable");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (compareMode) {
        // Compare two periods
        if (!period1Start || !period1End || !period2Start || !period2End) {
          throw new Error("Please select date ranges for both periods");
        }

        const period1Data = getDataForPeriod(period1Start, period1End);
        const period2Data = getDataForPeriod(period2Start, period2End);

        const [p1Results, p2Results] = await Promise.all([
          calculateCorrelations(period1Data),
          calculateCorrelations(period2Data)
        ]);

        setPeriod1Results(p1Results);
        setPeriod2Results(p2Results);
        setCorrelationResults([]);
      } else {
        // Single period analysis
        const results = await calculateCorrelations(data);
        setCorrelationResults(results);
        setPeriod1Results([]);
        setPeriod2Results([]);
      }
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
        return sorted.sort((a, b) => a.correlation - b.correlation);
      case 'desc':
        return sorted.sort((a, b) => b.correlation - a.correlation);
      case 'abs-asc':
        return sorted.sort((a, b) => Math.abs(a.correlation) - Math.abs(b.correlation));
      case 'abs-desc':
      default:
        return sorted.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
    }
  }, [correlationResults, sortOrder]);

  // Comparison results combined
  const comparisonResults = useMemo(() => {
    if (period1Results.length === 0 || period2Results.length === 0) return [];

    const combined = period1Results.map(p1 => {
      const p2 = period2Results.find(r => r.variable === p1.variable);
      return {
        variable: p1.variable,
        period1: p1.correlation,
        period2: p2?.correlation || 0,
        change: p2 ? p2.correlation - p1.correlation : 0,
        p1Strength: p1.strength,
        p2Strength: p2?.strength || 'N/A',
        p1PValue: p1.p_value,
        p2PValue: p2?.p_value || 1
      };
    });

    // Sort by absolute change
    return combined.sort((a, b) => Math.abs(b.change) - Math.abs(a.change));
  }, [period1Results, period2Results]);

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
      return [];
    }

    const mediaResults = correlationResults.filter(result =>
      result.variable.toLowerCase().startsWith('media_') &&
      result.variable.toLowerCase().endsWith('_spd')
    );

    const chartData = mediaResults.map(result => {
      const spendValues = data.map(row => {
        const val = row[result.variable];
        return typeof val === 'number' ? val : parseFloat(String(val)) || 0;
      });
      const avgSpend = spendValues.reduce((a, b) => a + b, 0) / spendValues.length;

      return {
        name: result.variable.replace(/^media_/, '').replace(/_spd$/, ''),
        correlation: result.correlation,
        spend: avgSpend,
        size: avgSpend,
        fullName: result.variable
      };
    });

    return chartData;
  }, [selectedVariable, correlationResults, data]);

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
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

              {/* Comparison Mode Toggle */}
              <div className="flex items-center gap-3 p-4 bg-muted/30 rounded-lg border">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="compareMode"
                      checked={compareMode}
                      onChange={(e) => setCompareMode(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-300"
                    />
                    <label htmlFor="compareMode" className="text-sm font-medium cursor-pointer">
                      Enable Period Comparison
                    </label>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Compare correlations across two different time periods
                  </p>
                </div>
              </div>

              {/* Period Date Selectors */}
              {compareMode && availableDates.length > 0 && (
                <div className="grid md:grid-cols-2 gap-4 p-4 border rounded-lg bg-card">
                  {/* Period 1 */}
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium flex items-center gap-2">
                      <span className="inline-block w-3 h-3 rounded-full bg-blue-500"></span>
                      Period 1
                    </h3>
                    <DatePicker
                      label="Start Date"
                      value={period1Start}
                      onChange={(newValue) => setPeriod1Start(newValue)}
                      minDate={minDate}
                      maxDate={maxDate}
                      format="DD/MM/YYYY"
                      slotProps={{
                        textField: {
                          size: 'small',
                          fullWidth: true,
                          sx: {
                            '& .MuiInputBase-root': { color: '#ffffff', backgroundColor: 'hsl(215, 20%, 20%)' },
                            '& .MuiInputBase-input': { color: '#ffffff !important', WebkitTextFillColor: '#ffffff !important' },
                            '& .MuiInputLabel-root': { color: 'hsl(214, 17%, 62%)' },
                            '& .MuiOutlinedInput-notchedOutline': { borderColor: 'hsl(215, 25%, 35%)' },
                            '& .MuiSvgIcon-root': { color: '#ffffff' }
                          }
                        }
                      }}
                    />
                    <DatePicker
                      label="End Date"
                      value={period1End}
                      onChange={(newValue) => setPeriod1End(newValue)}
                      minDate={period1Start || minDate}
                      maxDate={maxDate}
                      format="DD/MM/YYYY"
                      slotProps={{
                        textField: {
                          size: 'small',
                          fullWidth: true,
                          sx: {
                            '& .MuiInputBase-root': { color: '#ffffff', backgroundColor: 'hsl(215, 20%, 20%)' },
                            '& .MuiInputBase-input': { color: '#ffffff !important', WebkitTextFillColor: '#ffffff !important' },
                            '& .MuiInputLabel-root': { color: 'hsl(214, 17%, 62%)' },
                            '& .MuiOutlinedInput-notchedOutline': { borderColor: 'hsl(215, 25%, 35%)' },
                            '& .MuiSvgIcon-root': { color: '#ffffff' }
                          }
                        }
                      }}
                    />
                  </div>

                  {/* Period 2 */}
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium flex items-center gap-2">
                      <span className="inline-block w-3 h-3 rounded-full bg-purple-500"></span>
                      Period 2
                    </h3>
                    <DatePicker
                      label="Start Date"
                      value={period2Start}
                      onChange={(newValue) => setPeriod2Start(newValue)}
                      minDate={minDate}
                      maxDate={maxDate}
                      format="DD/MM/YYYY"
                      slotProps={{
                        textField: {
                          size: 'small',
                          fullWidth: true,
                          sx: {
                            '& .MuiInputBase-root': { color: '#ffffff', backgroundColor: 'hsl(215, 20%, 20%)' },
                            '& .MuiInputBase-input': { color: '#ffffff !important', WebkitTextFillColor: '#ffffff !important' },
                            '& .MuiInputLabel-root': { color: 'hsl(214, 17%, 62%)' },
                            '& .MuiOutlinedInput-notchedOutline': { borderColor: 'hsl(215, 25%, 35%)' },
                            '& .MuiSvgIcon-root': { color: '#ffffff' }
                          }
                        }
                      }}
                    />
                    <DatePicker
                      label="End Date"
                      value={period2End}
                      onChange={(newValue) => setPeriod2End(newValue)}
                      minDate={period2Start || minDate}
                      maxDate={maxDate}
                      format="DD/MM/YYYY"
                      slotProps={{
                        textField: {
                          size: 'small',
                          fullWidth: true,
                          sx: {
                            '& .MuiInputBase-root': { color: '#ffffff', backgroundColor: 'hsl(215, 20%, 20%)' },
                            '& .MuiInputBase-input': { color: '#ffffff !important', WebkitTextFillColor: '#ffffff !important' },
                            '& .MuiInputLabel-root': { color: 'hsl(214, 17%, 62%)' },
                            '& .MuiOutlinedInput-notchedOutline': { borderColor: 'hsl(215, 25%, 35%)' },
                            '& .MuiSvgIcon-root': { color: '#ffffff' }
                          }
                        }
                      }}
                    />
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
                    compareMode ? "Compare Periods" : "Calculate Correlations"
                  )}
                </Button>
              </div>

              {/* Comparison Results */}
              {compareMode && comparisonResults.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium">
                      Period Comparison: <span className="font-semibold">{selectedVariable}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="flex items-center gap-1">
                        <span className="inline-block w-3 h-3 rounded-full bg-blue-500"></span>
                        {period1Start?.format('DD/MM/YY')} - {period1End?.format('DD/MM/YY')}
                      </span>
                      <span>vs</span>
                      <span className="flex items-center gap-1">
                        <span className="inline-block w-3 h-3 rounded-full bg-purple-500"></span>
                        {period2Start?.format('DD/MM/YY')} - {period2End?.format('DD/MM/YY')}
                      </span>
                    </div>
                  </div>

                  <div className="rounded-md border overflow-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="bg-muted/50">
                          <th className="border-b p-3 text-left text-sm font-medium">Variable</th>
                          <th className="border-b p-3 text-center text-sm font-medium">Period 1</th>
                          <th className="border-b p-3 text-center text-sm font-medium">Period 2</th>
                          <th className="border-b p-3 text-center text-sm font-medium">Change</th>
                          <th className="border-b p-3 text-center text-sm font-medium">Direction</th>
                        </tr>
                      </thead>
                      <tbody className="bg-background">
                        {comparisonResults.map((result) => (
                          <tr key={result.variable} className="hover:bg-muted/50">
                            <td className="border-b p-3 font-medium">{result.variable}</td>
                            <td className="border-b p-3 text-center">
                              <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${getCorrelationColor(result.period1)}`}>
                                {result.period1.toFixed(3)}
                              </span>
                            </td>
                            <td className="border-b p-3 text-center">
                              <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${getCorrelationColor(result.period2)}`}>
                                {result.period2.toFixed(3)}
                              </span>
                            </td>
                            <td className="border-b p-3 text-center">
                              <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${
                                Math.abs(result.change) >= 0.2
                                  ? result.change > 0
                                    ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                                    : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                                  : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-300'
                              }`}>
                                {result.change >= 0 ? '+' : ''}{result.change.toFixed(3)}
                              </span>
                            </td>
                            <td className="border-b p-3 text-center">
                              {Math.abs(result.change) >= 0.2 ? (
                                result.change > 0 ? (
                                  <ArrowUp className="inline h-4 w-4 text-green-600" />
                                ) : (
                                  <ArrowDown className="inline h-4 w-4 text-red-600" />
                                )
                              ) : (
                                <span className="text-muted-foreground text-xs">~</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="text-xs p-4 bg-muted/50 rounded-lg">
                    <div className="font-medium mb-2">Interpretation:</div>
                    <div className="space-y-1 text-muted-foreground">
                      <div><span className="text-green-600 font-semibold">↑ Positive change</span> = Correlation increased in Period 2</div>
                      <div><span className="text-red-600 font-semibold">↓ Negative change</span> = Correlation decreased in Period 2</div>
                      <div><span className="font-semibold">~ Minimal change</span> = Change &lt; 0.2 (not meaningful)</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Single Period Correlation Results */}
              {!compareMode && correlationResults.length > 0 && (
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

              {correlationResults.length === 0 && comparisonResults.length === 0 && !isLoading && (
                <div className="text-center py-12 text-muted-foreground border rounded-lg bg-muted/30">
                  <p className="text-base mb-2">No correlation analysis yet</p>
                  <p className="text-sm">
                    {compareMode
                      ? "Select date ranges for both periods and click Compare"
                      : "Select a variable and click Calculate to see ranked correlations"
                    }
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </LocalizationProvider>
  );
}
