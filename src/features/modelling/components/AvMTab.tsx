"use client";

import { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useModellingStore } from "@/lib/store/modelling-store";
import { AlertCircle } from "lucide-react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from "recharts";

export function AvMTab() {
  const { regressionResults, modelConfig } = useModellingStore();

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!regressionResults) return [];

    const { transformed_data, fitted_values, residuals } = regressionResults;

    console.log('[AvMTab] Regression Results:', regressionResults);
    console.log('[AvMTab] Transformed Data Keys:', Object.keys(transformed_data));
    console.log('[AvMTab] Fitted Values Length:', fitted_values?.length);
    console.log('[AvMTab] Residuals Length:', residuals?.length);
    console.log('[AvMTab] Model Config:', modelConfig);

    // Get observation column (obs, OBS, date, Date)
    const obsCol = ['obs', 'OBS', 'date', 'Date'].find(col => col in transformed_data);
    const observations = obsCol ? transformed_data[obsCol] : Array.from({ length: fitted_values.length }, (_, i) => i + 1);

    console.log('[AvMTab] Observation Column:', obsCol);
    console.log('[AvMTab] Observations Sample:', observations.slice(0, 5));

    // Get actual KPI values
    const kpi = modelConfig?.kpi || '';
    const actualValues = transformed_data[kpi] || [];

    console.log('[AvMTab] KPI:', kpi);
    console.log('[AvMTab] Actual Values Length:', actualValues.length);
    console.log('[AvMTab] Actual Values Sample:', actualValues.slice(0, 5));

    const data = observations.map((obs, idx) => ({
      obs: String(obs),
      actual: actualValues[idx] || 0,
      fitted: fitted_values[idx] || 0,
      residual: residuals[idx] || 0,
    }));

    console.log('[AvMTab] Chart Data Sample:', data.slice(0, 5));

    return data;
  }, [regressionResults, modelConfig]);

  if (!regressionResults) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Actual vs Model</CardTitle>
          <CardDescription>Compare actual values with model predictions and residuals</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
              Please run the regression first to see the Actual vs Model chart.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Actual vs Model (AvM)</CardTitle>
        <CardDescription>
          Comparison of actual {modelConfig?.kpi} values vs model predictions with residuals
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="border rounded-md p-3 bg-muted/30">
            <div className="text-muted-foreground mb-1">Observations</div>
            <div className="text-2xl font-semibold">{chartData.length}</div>
          </div>
          <div className="border rounded-md p-3 bg-muted/30">
            <div className="text-muted-foreground mb-1">Mean Residual</div>
            <div className="text-2xl font-semibold">
              {(chartData.reduce((sum, d) => sum + d.residual, 0) / chartData.length).toFixed(4)}
            </div>
          </div>
          <div className="border rounded-md p-3 bg-muted/30">
            <div className="text-muted-foreground mb-1">R²</div>
            <div className="text-2xl font-semibold">{regressionResults.r_squared.toFixed(4)}</div>
          </div>
        </div>

        {/* Chart */}
        <div className="w-full h-[500px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="obs"
                angle={-45}
                textAnchor="end"
                height={80}
                className="text-xs"
                label={{ value: 'Observation', position: 'insideBottom', offset: -10 }}
              />
              <YAxis
                className="text-xs"
                label={{ value: 'Value', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px'
                }}
                formatter={(value: number) => value.toFixed(4)}
              />
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="line"
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
                name="Actual"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="fitted"
                stroke="hsl(var(--chart-2))"
                strokeWidth={2}
                name="Model Fitted"
                dot={false}
              />
              <Bar
                dataKey="residual"
                fill="hsl(var(--chart-3))"
                opacity={0.5}
                name="Residuals"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="text-xs text-muted-foreground">
          <p>The chart shows actual values (blue line), model fitted values (orange line), and residuals (semi-transparent bars).</p>
          <p>Residuals = Actual - Fitted. Smaller residuals indicate better model fit.</p>
        </div>
      </CardContent>
    </Card>
  );
}
