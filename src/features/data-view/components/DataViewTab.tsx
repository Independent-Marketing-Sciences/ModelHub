"use client";

import { useState, useEffect, useMemo } from "react";
import { useDataStore } from "@/lib/store";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Download, ChevronLeft, ChevronRight } from "lucide-react";
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs, { Dayjs } from 'dayjs';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';
import * as XLSX from "xlsx";

dayjs.extend(isSameOrAfter);
dayjs.extend(isSameOrBefore);

const ROWS_PER_PAGE = 50;

export function DataViewTab() {
  const { data, columns, getFilteredData, dateRangeStart, dateRangeEnd, dateColumn } = useDataStore();
  const [variableFilter, setVariableFilter] = useState("");

  // Period 1 (Last period)
  const [period1Start, setPeriod1Start] = useState<Dayjs | null>(null);
  const [period1End, setPeriod1End] = useState<Dayjs | null>(null);

  // Period 2 (Previous period)
  const [period2Start, setPeriod2Start] = useState<Dayjs | null>(null);
  const [period2End, setPeriod2End] = useState<Dayjs | null>(null);

  // Get data filtered by date range from store
  const dateFilteredData = getFilteredData();

  // Detect date column
  const detectedDateColumn = useMemo(() => {
    const dateColumnNames = ['OBS', 'obs', 'Date', 'date'];
    return columns.find(col => dateColumnNames.includes(col)) || '';
  }, [columns]);

  console.log('[DataViewTab] Render state:', {
    totalData: data.length,
    filteredData: dateFilteredData.length,
    dateColumn,
    dateRangeStart,
    dateRangeEnd
  });

  // Calculate summary statistics for numeric columns
  const summaryStats = useMemo(() => {
    if (dateFilteredData.length === 0 || !detectedDateColumn) return {};

    const stats: Record<string, {
      total: number;
      mean: number;
      min: number;
      max: number;
      period1: number;
      period2: number;
      percentChange: number;
    }> = {};

    // Exclude date columns
    const excludedColumns = ['OBS', 'obs', 'Date', 'date'];

    columns.forEach(col => {
      // Skip date columns
      if (excludedColumns.includes(col)) return;

      // Check if column is numeric
      const sampleValue = dateFilteredData[0]?.[col];
      const isNumeric = typeof sampleValue === 'number' || !isNaN(parseFloat(String(sampleValue)));

      if (isNumeric) {
        // Get all values with dates
        const valuesWithDates = dateFilteredData.map(row => ({
          date: dayjs(String(row[detectedDateColumn])),
          value: typeof row[col] === 'number' ? row[col] : parseFloat(String(row[col])) || 0
        }));

        // Calculate totals and basic stats
        const values = valuesWithDates.map(v => v.value);
        const total = values.reduce((sum, val) => sum + val, 0);
        const mean = total / values.length;
        const min = Math.min(...values);
        const max = Math.max(...values);

        // Period 1 values (if dates are set)
        let period1 = 0;
        if (period1Start && period1End) {
          const period1Values = valuesWithDates.filter(v =>
            v.date.isSameOrAfter(period1Start, 'day') && v.date.isSameOrBefore(period1End, 'day')
          );
          period1 = period1Values.reduce((sum, v) => sum + v.value, 0);
        }

        // Period 2 values (if dates are set)
        let period2 = 0;
        if (period2Start && period2End) {
          const period2Values = valuesWithDates.filter(v =>
            v.date.isSameOrAfter(period2Start, 'day') && v.date.isSameOrBefore(period2End, 'day')
          );
          period2 = period2Values.reduce((sum, v) => sum + v.value, 0);
        }

        // Percentage change
        const percentChange = period2 !== 0
          ? ((period1 - period2) / period2) * 100
          : 0;

        stats[col] = {
          total,
          mean,
          min,
          max,
          period1,
          period2,
          percentChange
        };
      }
    });

    return stats;
  }, [dateFilteredData, columns, detectedDateColumn, period1Start, period1End, period2Start, period2End]);


  // Filter stats based on search term
  const filteredStats = useMemo(() => {
    if (!variableFilter) return summaryStats;

    const filtered: typeof summaryStats = {};
    Object.entries(summaryStats).forEach(([key, value]) => {
      if (key.toLowerCase().includes(variableFilter.toLowerCase())) {
        filtered[key] = value;
      }
    });
    return filtered;
  }, [summaryStats, variableFilter]);

  const handleExport = () => {
    if (Object.keys(summaryStats).length === 0) return;

    const period1Label = period1Start && period1End
      ? `Period 1 (${period1Start.format('YYYY-MM-DD')} to ${period1End.format('YYYY-MM-DD')})`
      : 'Period 1';

    const period2Label = period2Start && period2End
      ? `Period 2 (${period2Start.format('YYYY-MM-DD')} to ${period2End.format('YYYY-MM-DD')})`
      : 'Period 2';

    // Convert summary stats to array format for Excel
    const exportData = Object.entries(summaryStats).map(([variable, stats]) => ({
      'Variable': variable,
      'Total': stats.total,
      'Mean': stats.mean,
      'Min': stats.min,
      'Max': stats.max,
      [period1Label]: stats.period1,
      [period2Label]: stats.period2,
      '% Change': stats.percentChange
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Summary Statistics");

    XLSX.writeFile(workbook, `summary_statistics_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  // Check if no data is loaded at all
  if (data.length === 0) {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Data View & Summary</CardTitle>
            <CardDescription>
              View and summarize your dataset with pagination and export capabilities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-muted-foreground">
              <p className="text-lg mb-2">No data loaded</p>
              <p className="text-sm">
                Upload a dataset CSV or Excel file to view and analyze your data
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Check if date filter has filtered out all data
  if (dateFilteredData.length === 0) {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Data View & Summary</CardTitle>
            <CardDescription>
              View and summarize your dataset with pagination and export capabilities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-muted-foreground">
              <p className="text-lg mb-2">No data matches the selected date range</p>
              <p className="text-sm">
                Try adjusting the date range filter to see data
              </p>
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
          <CardTitle>Data View & Summary</CardTitle>
          <CardDescription>
            View and summarize your dataset with pagination and export capabilities
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium">Period Comparison</h3>
                <Button
                  onClick={handleExport}
                  disabled={Object.keys(summaryStats).length === 0}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Export Summary Statistics
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* Period 1 */}
                <div className="space-y-3 p-4 rounded-lg border bg-muted/30">
                  <h4 className="text-sm font-medium">Period 1</h4>
                  <div className="space-y-3">
                    <DatePicker
                      label="Start Date"
                      value={period1Start}
                      onChange={(newValue) => setPeriod1Start(newValue)}
                      slotProps={{
                        textField: {
                          size: 'small',
                          fullWidth: true,
                          sx: {
                            '& .MuiInputBase-root': {
                              color: 'var(--foreground)',
                              backgroundColor: 'var(--background)',
                            },
                            '& .MuiInputLabel-root': {
                              color: 'var(--muted-foreground)',
                            },
                            '& .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'var(--border)',
                            }
                          }
                        }
                      }}
                    />
                    <DatePicker
                      label="End Date"
                      value={period1End}
                      onChange={(newValue) => setPeriod1End(newValue)}
                      minDate={period1Start || undefined}
                      slotProps={{
                        textField: {
                          size: 'small',
                          fullWidth: true,
                          sx: {
                            '& .MuiInputBase-root': {
                              color: 'var(--foreground)',
                              backgroundColor: 'var(--background)',
                            },
                            '& .MuiInputLabel-root': {
                              color: 'var(--muted-foreground)',
                            },
                            '& .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'var(--border)',
                            }
                          }
                        }
                      }}
                    />
                  </div>
                </div>

                {/* Period 2 */}
                <div className="space-y-3 p-4 rounded-lg border bg-muted/30">
                  <h4 className="text-sm font-medium">Period 2</h4>
                  <div className="space-y-3">
                    <DatePicker
                      label="Start Date"
                      value={period2Start}
                      onChange={(newValue) => setPeriod2Start(newValue)}
                      slotProps={{
                        textField: {
                          size: 'small',
                          fullWidth: true,
                          sx: {
                            '& .MuiInputBase-root': {
                              color: 'var(--foreground)',
                              backgroundColor: 'var(--background)',
                            },
                            '& .MuiInputLabel-root': {
                              color: 'var(--muted-foreground)',
                            },
                            '& .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'var(--border)',
                            }
                          }
                        }
                      }}
                    />
                    <DatePicker
                      label="End Date"
                      value={period2End}
                      onChange={(newValue) => setPeriod2End(newValue)}
                      minDate={period2Start || undefined}
                      slotProps={{
                        textField: {
                          size: 'small',
                          fullWidth: true,
                          sx: {
                            '& .MuiInputBase-root': {
                              color: 'var(--foreground)',
                              backgroundColor: 'var(--background)',
                            },
                            '& .MuiInputLabel-root': {
                              color: 'var(--muted-foreground)',
                            },
                            '& .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'var(--border)',
                            }
                          }
                        }
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </LocalizationProvider>

          {/* Dataset Overview */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Rows</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dateFilteredData.length.toLocaleString()}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Columns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{columns.length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Numeric Variables</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Object.keys(summaryStats).length}</div>
              </CardContent>
            </Card>
          </div>

          {/* Summary Statistics Section */}
          {Object.keys(summaryStats).length > 0 && (
            <div>
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium">Variable Summary Statistics</h3>
                  <p className="text-sm text-muted-foreground">
                    Detailed statistics and period comparisons for all numeric variables
                  </p>
                </div>
                <Input
                  placeholder="Filter variables..."
                  value={variableFilter}
                  onChange={(e) => setVariableFilter(e.target.value)}
                  className="max-w-xs"
                />
              </div>
              <div className="rounded-md border overflow-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium border-b whitespace-nowrap">
                        Variable
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Total
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Mean
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Min
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Max
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Period 1
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        Period 2
                      </th>
                      <th className="px-4 py-3 text-right font-medium border-b whitespace-nowrap">
                        % Change
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-background">
                    {Object.entries(filteredStats).map(([col, stats]) => (
                      <tr key={col} className="hover:bg-muted/50">
                        <td className="px-4 py-2 border-b font-medium">
                          {col}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          {stats.total.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          {stats.mean.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          {stats.min.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          {stats.max.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          {stats.period1.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          {stats.period2.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2 border-b text-right font-mono">
                          <span className={`inline-block px-2 py-1 rounded text-xs ${
                            stats.percentChange > 0
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                              : stats.percentChange < 0
                              ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                              : 'bg-muted text-muted-foreground'
                          }`}>
                            {stats.percentChange > 0 ? '+' : ''}{stats.percentChange.toFixed(2)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
