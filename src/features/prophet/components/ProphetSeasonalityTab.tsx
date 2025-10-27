"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { Button } from "@/components/ui/button";
import { TrendingUp, AlertCircle, Loader2, CheckCircle, Info, Download } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, ComposedChart } from "recharts";
import { pythonClient, ProphetForecastResponse } from "@/lib/api/python-client";
import { useDataStore } from "@/lib/store/index";

export function ProphetSeasonalityTab() {
  const [selectedKPI, setSelectedKPI] = useState("");
  const [selectedDateCol, setSelectedDateCol] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [technicalError, setTechnicalError] = useState<string | null>(null);
  const [backendAvailable, setBackendAvailable] = useState(false);
  const [forecastData, setForecastData] = useState<ProphetForecastResponse | null>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  const { columns, getFilteredData } = useDataStore();

  // Get data filtered by date range from store
  const data = getFilteredData();

  // Auto-detect date column - always use OBS, obs, Date, or date
  useEffect(() => {
    if (columns.length > 0) {
      const dateColumnNames = ['OBS', 'obs', 'Date', 'date'];
      const foundDateCol = columns.find(col => dateColumnNames.includes(col));
      if (foundDateCol) {
        setSelectedDateCol(foundDateCol);
      } else {
        // Fallback: Try case-insensitive match
        const caseInsensitiveMatch = columns.find(col =>
          dateColumnNames.some(name => col.toLowerCase() === name.toLowerCase())
        );
        setSelectedDateCol(caseInsensitiveMatch || '');
      }
    }
  }, [columns]);

  // Check if Python backend is available
  useEffect(() => {
    checkBackend();
  }, []);

  const handleExportSeasonality = () => {
    if (!seasonalityChartData || seasonalityChartData.length === 0) {
      setError("No yearly seasonality data to export. Please run a forecast first.");
      return;
    }

    // Create CSV content
    const headers = ['Date', 'Yearly Seasonality'];
    const rows = seasonalityChartData.map(item => [item.date, item.yearly]);
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `yearly_seasonality_${selectedKPI}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const checkBackend = async () => {
    try {
      const result = await pythonClient.checkAvailability();
      setBackendAvailable(result.available);

      if (!result.available) {
        setError(
          "Prophet forecasting is not available.\n\n" +
          "To enable this feature:\n" +
          "1. Make sure Python is installed on your system\n" +
          "2. Run 'Install-Dependencies.bat' as Administrator (found in the Modelling Mate installation folder)\n" +
          "3. Wait for installation to complete (5-10 minutes)\n" +
          "4. Restart Modelling Mate\n\n" +
          "Note: Prophet requires Microsoft C++ Build Tools on Windows.\n" +
          "See the troubleshooting guide if installation fails."
        );

        // Store technical error details
        if (result.error) {
          setTechnicalError(`Technical details: ${result.error}`);
        } else {
          setTechnicalError("Technical details: Unable to connect to Python backend at http://localhost:8000");
        }
      } else {
        // Backend is available, check if Prophet is actually installed
        if (result.details?.dependencies?.prophet === false) {
          setError(
            "Prophet library is not installed in the Python backend.\n\n" +
            "To fix this:\n" +
            "1. Run 'Install-Dependencies.bat' as Administrator\n" +
            "2. Wait for installation to complete\n" +
            "3. Restart Modelling Mate\n\n" +
            "If installation fails, you may need Microsoft C++ Build Tools."
          );
          setTechnicalError("Technical details: Python backend is running but Prophet library is not installed");
          setBackendAvailable(false);
        }
      }
    } catch (err) {
      setBackendAvailable(false);
      setError(
        "Failed to check Python backend status.\n\n" +
        "Please ensure:\n" +
        "1. Python is installed\n" +
        "2. Dependencies are installed (run Install-Dependencies.bat)\n" +
        "3. The app has been restarted"
      );
      setTechnicalError(`Technical details: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleRunForecast = async () => {
    if (!selectedKPI) {
      setError("Please select a KPI");
      return;
    }

    if (!data || data.length === 0) {
      setError("No data available. Please load a dataset first.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setTechnicalError(null);

    if (!selectedDateCol) {
      setError("Please select a date column");
      setIsLoading(false);
      return;
    }

    try {
      // Extract dates and values, filter out undefined/null
      const dates = data
        .map(row => row[selectedDateCol])
        .filter(d => d !== undefined && d !== null)
        .map(d => String(d));

      const values = data
        .map(row => row[selectedKPI])
        .filter(v => v !== undefined && v !== null)
        .map(v => typeof v === 'number' ? v : parseFloat(String(v)) || 0);

      if (dates.length === 0 || values.length === 0) {
        setError("No valid data found in selected columns");
        setIsLoading(false);
        return;
      }

      // Validate minimum data points for Prophet
      const MIN_DATA_POINTS = 10;
      if (dates.length < MIN_DATA_POINTS) {
        setError(
          `Insufficient data for Prophet forecasting.\n\n` +
          `Found: ${dates.length} data points\n` +
          `Required: At least ${MIN_DATA_POINTS} data points\n\n` +
          `Prophet requires a reasonable amount of historical data to identify patterns and trends. ` +
          `Please load a dataset with more observations.`
        );
        setIsLoading(false);
        return;
      }

      // Check if backend is still available before making the request
      const backendCheck = await pythonClient.checkAvailability();
      if (!backendCheck.available) {
        setError(
          "Python backend is not available.\n\n" +
          "The backend may have stopped or crashed. Please:\n" +
          "1. Restart Modelling Mate\n" +
          "2. Check that Python dependencies are installed\n" +
          "3. Click 'Retry' to check connection again"
        );
        setTechnicalError(backendCheck.error || "Cannot connect to backend");
        setBackendAvailable(false);
        setIsLoading(false);
        return;
      }

      // Call Python backend
      const result = await pythonClient.prophetForecast({
        dates,
        values,
        periods: 52 * 7, // Forecast 52 weeks (as daily data)
        yearly_seasonality: true,
        weekly_seasonality: true,
      });

      setForecastData(result);
      setTechnicalError(null); // Clear any previous errors
      setError(null); // Clear any previous errors
    } catch (err) {
      console.error("Prophet forecast error:", err);

      // Determine the specific error type
      let userMessage = "Failed to generate forecast.";
      let technicalMessage = err instanceof Error ? err.message : String(err);

      // Check for specific error types
      if (technicalMessage.includes("Failed to fetch") || technicalMessage.includes("fetch")) {
        userMessage =
          "Cannot connect to Python backend.\n\n" +
          "The backend server is not responding. This usually means:\n" +
          "1. The Python backend failed to start when the app launched\n" +
          "2. Prophet or other dependencies are not installed\n" +
          "3. The backend crashed during operation\n\n" +
          "To fix this:\n" +
          "1. Restart Modelling Mate\n" +
          "2. Run 'Install-Dependencies.bat' as Administrator\n" +
          "3. Check the installation folder for error logs";
        technicalMessage = "Network error: " + technicalMessage;
        setBackendAvailable(false);
      } else if (technicalMessage.includes("stan_backend")) {
        userMessage =
          "Prophet version compatibility issue detected.\n\n" +
          "Your Prophet installation may be outdated or incompatible.\n\n" +
          "To fix this:\n" +
          "1. Open Command Prompt as Administrator\n" +
          "2. Run: pip install --upgrade prophet\n" +
          "3. Restart Modelling Mate";
      } else if (technicalMessage.includes("date") || technicalMessage.includes("datetime")) {
        userMessage =
          "Invalid date format in your data.\n\n" +
          `Prophet could not parse the dates in column '${selectedDateCol}'.\n\n` +
          "Supported date formats:\n" +
          "- YYYY-MM-DD (2024-01-15)\n" +
          "- DD/MM/YYYY (15/01/2024)\n" +
          "- MM/DD/YYYY (01/15/2024)\n\n" +
          "Please check your date column format.";
      } else if (technicalMessage.includes("insufficient") || technicalMessage.includes("not enough")) {
        userMessage =
          "Insufficient data for forecasting.\n\n" +
          "Prophet requires enough historical data points to detect patterns.\n" +
          "Please ensure you have at least 10 observations with valid dates and values.";
      }

      setError(userMessage);
      setTechnicalError(`Error: ${technicalMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Prepare chart data - aggregate daily to weekly
  const forecastChartData = forecastData?.forecast ? (() => {
    const dailyData = forecastData.forecast.dates.map((date, idx) => ({
      date: new Date(date),
      forecast: forecastData.forecast.yhat[idx],
      lower: forecastData.forecast.yhat_lower[idx],
      upper: forecastData.forecast.yhat_upper[idx],
    }));

    // Group by week
    const weeklyData: Record<string, { forecast: number[], lower: number[], upper: number[], count: number }> = {};

    dailyData.forEach(item => {
      // Get the Monday of the week (ISO week)
      const dayOfWeek = item.date.getDay();
      const mondayDate = new Date(item.date);
      mondayDate.setDate(item.date.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
      const weekKey = mondayDate.toISOString().split('T')[0];

      if (!weeklyData[weekKey]) {
        weeklyData[weekKey] = { forecast: [], lower: [], upper: [], count: 0 };
      }

      weeklyData[weekKey].forecast.push(item.forecast);
      weeklyData[weekKey].lower.push(item.lower);
      weeklyData[weekKey].upper.push(item.upper);
      weeklyData[weekKey].count++;
    });

    // Calculate weekly averages
    return Object.keys(weeklyData).sort().map(weekKey => ({
      date: weekKey,
      forecast: weeklyData[weekKey].forecast.reduce((a, b) => a + b, 0) / weeklyData[weekKey].count,
      lower: weeklyData[weekKey].lower.reduce((a, b) => a + b, 0) / weeklyData[weekKey].count,
      upper: weeklyData[weekKey].upper.reduce((a, b) => a + b, 0) / weeklyData[weekKey].count,
    }));
  })() : [];

  const trendChartData = forecastData?.components ? forecastData.components.dates.map((date, idx) => ({
    date,
    trend: forecastData.components.trend[idx],
  })) : [];

  const seasonalityChartData = forecastData?.components?.yearly ? forecastData.components.dates.map((date, idx) => ({
    date,
    yearly: forecastData.components.yearly![idx],
  })) : [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Prophet Seasonality Analysis</CardTitle>
          <CardDescription>
            Time-series forecasting and seasonality decomposition using Facebook Prophet
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Error message */}
            {error && (
              <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-md p-4">
                <div className="flex items-start gap-3 mb-3">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm text-red-800 dark:text-red-300 font-medium mb-2">
                      {!backendAvailable ? "Prophet Forecasting Not Available" : "Error"}
                    </div>
                    <div className="text-sm text-red-700 dark:text-red-400 whitespace-pre-line">{error}</div>
                    {!backendAvailable && (
                      <div className="mt-3 text-xs text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 rounded px-2 py-1">
                        <Info className="h-3 w-3 inline mr-1" />
                        Installation folder: C:\Users\[YourUsername]\AppData\Local\Programs\modelling-mate\
                      </div>
                    )}
                  </div>
                  {!backendAvailable && (
                    <Button variant="outline" size="sm" onClick={checkBackend} className="flex-shrink-0">
                      Retry
                    </Button>
                  )}
                </div>

                {/* Technical error details - collapsible */}
                {technicalError && (
                  <div className="border-t border-red-200 dark:border-red-800 pt-3 mt-3">
                    <button
                      onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                      className="flex items-center gap-2 text-xs text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 font-medium"
                    >
                      <Info className="h-3 w-3" />
                      {showTechnicalDetails ? "Hide" : "Show"} Technical Details
                    </button>
                    {showTechnicalDetails && (
                      <div className="mt-2 bg-red-100 dark:bg-red-900/30 rounded p-2 text-xs font-mono text-red-900 dark:text-red-300 overflow-x-auto">
                        {technicalError}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="mb-4">
              <label className="text-sm font-medium mb-2 block">KPI to Forecast</label>
              <SearchableSelect
                value={selectedKPI}
                onValueChange={setSelectedKPI}
                options={columns
                  .filter(col => col !== selectedDateCol)
                  .map(col => ({ value: col, label: col }))}
                placeholder="Choose a KPI..."
                disabled={isLoading}
              />
              {selectedDateCol && (
                <p className="text-xs text-muted-foreground mt-2">
                  Using date column: <span className="font-medium">{selectedDateCol}</span>
                </p>
              )}
            </div>

            <div className="flex justify-center">
              <Button onClick={handleRunForecast} disabled={isLoading || !backendAvailable} size="lg">
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Forecasting...
                  </>
                ) : (
                  <>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Run Forecast
                  </>
                )}
              </Button>
            </div>

            <div className="space-y-4">
              <div className="border rounded-lg p-6 bg-card">
                <h3 className="text-sm font-medium mb-4">Forecast Plot</h3>
                <div>
                  {forecastChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <ComposedChart data={forecastChartData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 12, fill: 'currentColor' }}
                          tickFormatter={(date) => new Date(date).toLocaleDateString()}
                          className="text-gray-700 dark:text-gray-300"
                        />
                        <YAxis tick={{ fontSize: 12, fill: 'currentColor' }} className="text-gray-700 dark:text-gray-300" />
                        <Tooltip
                          labelFormatter={(date) => new Date(date).toLocaleDateString()}
                          formatter={(value: number) => value.toFixed(2)}
                          contentStyle={{
                            backgroundColor: 'rgba(255, 255, 255, 0.95)',
                            border: '1px solid #e5e7eb',
                            borderRadius: '6px'
                          }}
                          wrapperClassName="dark:[&_.recharts-tooltip-wrapper]:!bg-gray-800 dark:[&_.recharts-default-tooltip]:!bg-gray-800 dark:[&_.recharts-default-tooltip]:!border-gray-700 dark:[&_.recharts-tooltip-label]:!text-white dark:[&_.recharts-tooltip-item]:!text-gray-300"
                        />
                        <Legend wrapperStyle={{ color: 'inherit' }} className="text-gray-700 dark:text-gray-300" />
                        {/* Upper confidence interval line */}
                        <Line
                          type="monotone"
                          dataKey="upper"
                          stroke="#93c5fd"
                          strokeWidth={2}
                          strokeDasharray="5 5"
                          dot={false}
                          name="Upper CI"
                        />
                        {/* Lower confidence interval line */}
                        <Line
                          type="monotone"
                          dataKey="lower"
                          stroke="#93c5fd"
                          strokeWidth={2}
                          strokeDasharray="5 5"
                          dot={false}
                          name="Lower CI"
                        />
                        {/* Main forecast line */}
                        <Line
                          type="monotone"
                          dataKey="forecast"
                          stroke="#2563eb"
                          strokeWidth={2.5}
                          dot={false}
                          name="Weekly Forecast"
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                      <p>Forecast visualization will appear here</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="border rounded-lg p-6 bg-card">
                <h3 className="text-sm font-medium mb-4">Trend Decomposition</h3>
                <div>
                  {trendChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={trendChartData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 12, fill: 'currentColor' }}
                          tickFormatter={(date) => new Date(date).toLocaleDateString()}
                          className="text-gray-700 dark:text-gray-300"
                        />
                        <YAxis tick={{ fontSize: 12, fill: 'currentColor' }} className="text-gray-700 dark:text-gray-300" />
                        <Tooltip
                          labelFormatter={(date) => new Date(date).toLocaleDateString()}
                          contentStyle={{
                            backgroundColor: 'rgba(255, 255, 255, 0.95)',
                            border: '1px solid #e5e7eb',
                            borderRadius: '6px'
                          }}
                          wrapperClassName="dark:[&_.recharts-tooltip-wrapper]:!bg-gray-800 dark:[&_.recharts-default-tooltip]:!bg-gray-800 dark:[&_.recharts-default-tooltip]:!border-gray-700 dark:[&_.recharts-tooltip-label]:!text-white dark:[&_.recharts-tooltip-item]:!text-gray-300"
                        />
                        <Legend wrapperStyle={{ color: 'inherit' }} className="text-gray-700 dark:text-gray-300" />
                        <Line type="monotone" dataKey="trend" stroke="#10b981" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                      <p>Trend visualization will appear here</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="border rounded-lg p-6 bg-card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium">Yearly Seasonality</h3>
                  {seasonalityChartData.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleExportSeasonality}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Export CSV
                    </Button>
                  )}
                </div>
                <div>
                  {seasonalityChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={seasonalityChartData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 12, fill: 'currentColor' }}
                          tickFormatter={(date) => new Date(date).toLocaleDateString()}
                          className="text-gray-700 dark:text-gray-300"
                        />
                        <YAxis tick={{ fontSize: 12, fill: 'currentColor' }} className="text-gray-700 dark:text-gray-300" />
                        <Tooltip
                          labelFormatter={(date) => new Date(date).toLocaleDateString()}
                          contentStyle={{
                            backgroundColor: 'rgba(255, 255, 255, 0.95)',
                            border: '1px solid #e5e7eb',
                            borderRadius: '6px'
                          }}
                          wrapperClassName="dark:[&_.recharts-tooltip-wrapper]:!bg-gray-800 dark:[&_.recharts-default-tooltip]:!bg-gray-800 dark:[&_.recharts-default-tooltip]:!border-gray-700 dark:[&_.recharts-tooltip-label]:!text-white dark:[&_.recharts-tooltip-item]:!text-gray-300"
                        />
                        <Legend wrapperStyle={{ color: 'inherit' }} className="text-gray-700 dark:text-gray-300" />
                        <Line type="monotone" dataKey="yearly" stroke="#f59e0b" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                      <p>Seasonality pattern will appear here</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
