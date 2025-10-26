"use client";

import { useState, useMemo, useCallback } from "react";
import { useDataStore } from "@/lib/store/index";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { BarChart3, AlertCircle, Plus, Trash2, Loader2 } from "lucide-react";
import { pythonClient } from "@/lib/api/python-client";

interface TransformationStep {
  type: string;
  amount: number;
}

interface VariableConfig {
  variable: string;
  transformations: TransformationStep[];
}

const TRANSFORMATION_OPTIONS = [
  { label: 'Log', value: 'log' },
  { label: 'Lag & Lead', value: 'lag & lead' },
  { label: 'Adstock', value: 'adstock' },
  { label: 'Diminishing Returns Absolute', value: 'diminishing_returns_absolute' },
  { label: 'Diminishing Returns Exponential', value: 'diminishing_returns_exponential' },
  { label: 'Simple Moving Average', value: 'sma' },
];

export function ChartingToolTab() {
  const { columns, dateColumn, getFilteredData } = useDataStore();
  const [variable1Config, setVariable1Config] = useState<VariableConfig>({
    variable: "",
    transformations: []
  });
  const [variable2Config, setVariable2Config] = useState<VariableConfig>({
    variable: "",
    transformations: []
  });
  const [chartData, setChartData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get data filtered by date range from store
  const data = getFilteredData();

  // Detect date column
  const detectedDateColumn = useMemo(() => {
    const dateColumnNames = ['OBS', 'obs', 'Date', 'date'];
    return columns.find(col => dateColumnNames.includes(col)) || dateColumn || '';
  }, [columns, dateColumn]);

  // Filter out date columns from variable selection
  const availableColumns = useMemo(() => {
    const dateColumnNames = ['OBS', 'obs', 'Date', 'date'];
    return columns.filter(col => !dateColumnNames.includes(col) && col !== dateColumn);
  }, [columns, dateColumn]);

  // Add transformation row
  const addTransformation = (variableNum: 1 | 2) => {
    if (variableNum === 1) {
      setVariable1Config({
        ...variable1Config,
        transformations: [...variable1Config.transformations, { type: 'log', amount: 0 }]
      });
    } else {
      setVariable2Config({
        ...variable2Config,
        transformations: [...variable2Config.transformations, { type: 'log', amount: 0 }]
      });
    }
  };

  // Remove transformation row
  const removeTransformation = (variableNum: 1 | 2, index: number) => {
    if (variableNum === 1) {
      setVariable1Config({
        ...variable1Config,
        transformations: variable1Config.transformations.filter((_, i) => i !== index)
      });
    } else {
      setVariable2Config({
        ...variable2Config,
        transformations: variable2Config.transformations.filter((_, i) => i !== index)
      });
    }
  };

  // Update transformation
  const updateTransformation = (variableNum: 1 | 2, index: number, field: 'type' | 'amount', value: any) => {
    const config = variableNum === 1 ? variable1Config : variable2Config;
    const newTransformations = [...config.transformations];
    newTransformations[index] = {
      ...newTransformations[index],
      [field]: field === 'amount' ? parseFloat(value) || 0 : value
    };

    if (variableNum === 1) {
      setVariable1Config({ ...variable1Config, transformations: newTransformations });
    } else {
      setVariable2Config({ ...variable2Config, transformations: newTransformations });
    }
  };

  const handleGenerateChart = useCallback(async () => {
    if (!variable1Config.variable) {
      setError("Please select at least Variable 1");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Get raw data for variable 1
      const var1Data = data.map(row => {
        const val = row[variable1Config.variable];
        return typeof val === 'number' ? val : parseFloat(String(val)) || 0;
      });

      // Transform variable 1 using backend
      const var1Result = await pythonClient.transformVariable({
        variable_name: variable1Config.variable,
        data: var1Data,
        transformations: variable1Config.transformations
      });

      let var2Result = null;
      if (variable2Config.variable && variable2Config.variable !== "__none__") {
        // Get raw data for variable 2
        const var2Data = data.map(row => {
          const val = row[variable2Config.variable];
          return typeof val === 'number' ? val : parseFloat(String(val)) || 0;
        });

        // Transform variable 2 using backend
        var2Result = await pythonClient.transformVariable({
          variable_name: variable2Config.variable,
          data: var2Data,
          transformations: variable2Config.transformations
        });
      }

      // Create unique keys for chart data (handles same variable with different transformations)
      const var1Key = variable1Config.transformations.length > 0
        ? `${variable1Config.variable} (transformed)`
        : variable1Config.variable;

      const var2Key = var2Result
        ? (variable2Config.transformations.length > 0
            ? `${variable2Config.variable} (transformed)`
            : variable2Config.variable)
        : null;

      // Prepare chart data with detected date column as X-axis
      const chartPoints = data.map((row, idx) => ({
        date: row[detectedDateColumn] || `Row ${idx + 1}`,
        [var1Key]: var1Result.transformed_data[idx],
        ...(var2Result && var2Key && { [var2Key]: var2Result.transformed_data[idx] })
      }));

      setChartData(chartPoints);
    } catch (err) {
      console.error("Chart generation error:", err);
      setError(err instanceof Error ? err.message : "Failed to generate chart");
    } finally {
      setIsLoading(false);
    }
  }, [data, detectedDateColumn, variable1Config, variable2Config]);

  // Handle Enter key press
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading && variable1Config.variable && data.length > 0) {
      handleGenerateChart();
    }
  }, [handleGenerateChart, isLoading, variable1Config.variable, data.length]);

  // Compute chart keys for display (must match keys used in handleGenerateChart)
  const chartKeys = useMemo(() => {
    const var1Key = variable1Config.transformations.length > 0
      ? `${variable1Config.variable} (transformed)`
      : variable1Config.variable;

    const var2Key = variable2Config.variable && variable2Config.variable !== "__none__"
      ? (variable2Config.transformations.length > 0
          ? `${variable2Config.variable} (transformed)`
          : variable2Config.variable)
      : null;

    return { var1Key, var2Key };
  }, [variable1Config, variable2Config]);

  const renderTransformationTable = (variableNum: 1 | 2) => {
    const config = variableNum === 1 ? variable1Config : variable2Config;
    const varLabel = variableNum === 1 ? "Variable 1" : "Variable 2";

    return (
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-2 block">{varLabel}</label>
          <SearchableSelect
            value={config.variable}
            onValueChange={(val) => {
              if (variableNum === 1) {
                setVariable1Config({ ...variable1Config, variable: val });
              } else {
                setVariable2Config({ ...variable2Config, variable: val });
              }
            }}
            options={[
              { value: "__none__", label: "None" },
              ...availableColumns.map(col => ({ value: col, label: col }))
            ]}
            placeholder={`Select ${varLabel.toLowerCase()}...`}
          />
        </div>

        {config.variable && config.variable !== "__none__" && (
          <Card className="bg-muted/50">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Transformations</CardTitle>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => addTransformation(variableNum)}
                  className="h-7"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {config.transformations.length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-4">
                  No transformations. Click &quot;Add&quot; to add one.
                </p>
              ) : (
                <div className="space-y-2">
                  {/* Table Header */}
                  <div className="grid grid-cols-[1fr,100px,40px] gap-2 pb-1 border-b text-xs font-medium text-muted-foreground">
                    <div>Type</div>
                    <div>Amount</div>
                    <div></div>
                  </div>

                  {/* Table Rows */}
                  {config.transformations.map((transform, idx) => (
                    <div key={idx} className="grid grid-cols-[1fr,100px,40px] gap-2 items-center">
                      <Select
                        value={transform.type}
                        onValueChange={(val) => updateTransformation(variableNum, idx, 'type', val)}
                      >
                        <SelectTrigger className="h-8 text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TRANSFORMATION_OPTIONS.map(opt => (
                            <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>

                      <Input
                        type="number"
                        step="0.1"
                        value={transform.amount}
                        onChange={(e) => updateTransformation(variableNum, idx, 'amount', e.target.value)}
                        className="h-8 text-xs"
                      />

                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => removeTransformation(variableNum, idx)}
                        className="h-8 w-8 p-0"
                      >
                        <Trash2 className="h-3 w-3 text-red-500" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4" onKeyDown={handleKeyPress}>
      <Card>
        <CardHeader>
          <CardTitle>Charting</CardTitle>
          <CardDescription>
            Apply multiple transformations in sequence and compare variables
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {data.length === 0 && (
            <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2 mb-6">
              <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5" />
              <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
                No data loaded. Please upload a dataset first.
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-md p-3 flex items-start gap-2 mb-6">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
              <div className="flex-1 text-sm text-red-800 dark:text-red-300">{error}</div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-6 mb-6">
            {renderTransformationTable(1)}
            {renderTransformationTable(2)}
          </div>

          <div className="flex items-center justify-center mb-6">
            <Button
              onClick={handleGenerateChart}
              disabled={!variable1Config.variable || data.length === 0 || isLoading}
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Generate Chart
                </>
              )}
            </Button>
          </div>

          {/* Chart */}
          <div className="border rounded-lg p-6 bg-card">
            {chartData.length > 0 ? (
              <div className="h-[450px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chartData}
                    margin={{ top: 5, right: 30, left: 20, bottom: 70 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                    <XAxis
                      dataKey="date"
                      angle={-45}
                      textAnchor="end"
                      height={100}
                      tick={{ fontSize: 11, fill: 'currentColor' }}
                      interval="preserveStartEnd"
                      className="text-gray-700 dark:text-gray-300"
                    />
                    <YAxis
                      yAxisId="left"
                      tick={{ fontSize: 11, fill: 'currentColor' }}
                      width={60}
                      className="text-gray-700 dark:text-gray-300"
                    />
                    {variable2Config.variable && variable2Config.variable !== "__none__" && (
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        tick={{ fontSize: 11, fill: 'currentColor' }}
                        width={60}
                        className="text-gray-700 dark:text-gray-300"
                      />
                    )}
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #e5e7eb',
                        borderRadius: '6px',
                        fontSize: '12px'
                      }}
                      wrapperClassName="dark:[&_.recharts-tooltip-wrapper]:!bg-gray-800 dark:[&_.recharts-default-tooltip]:!bg-gray-800 dark:[&_.recharts-default-tooltip]:!border-gray-700 dark:[&_.recharts-tooltip-label]:!text-white dark:[&_.recharts-tooltip-item]:!text-gray-300"
                    />
                    <Legend wrapperStyle={{ color: 'inherit' }} className="text-gray-700 dark:text-gray-300" />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey={chartKeys.var1Key}
                      stroke="#3b82f6"
                      strokeWidth={2}
                      name={chartKeys.var1Key}
                      dot={false}
                    />
                    {chartKeys.var2Key && (
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey={chartKeys.var2Key}
                        stroke="#f59e0b"
                        strokeWidth={2}
                        name={chartKeys.var2Key}
                        dot={false}
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Select variables and click Generate Chart to visualize</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
