"use client";

import { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useModellingStore } from "@/lib/store/modelling-store";
import { AlertCircle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

// Color palette for variables
const COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
  "#8b5cf6", // purple
  "#ec4899", // pink
  "#f59e0b", // amber
  "#10b981", // emerald
  "#06b6d4", // cyan
  "#6366f1", // indigo
  "#f97316", // orange
];

export function DecompTab() {
  const { regressionResults, modelConfig } = useModellingStore();

  // Prepare decomposition chart data
  const { chartData, variables } = useMemo(() => {
    if (!regressionResults) return { chartData: [], variables: [] };

    const { transformed_data, variable_contributions, coefficients } = regressionResults;

    // Get observation column
    const obsCol = ['obs', 'OBS', 'date', 'Date'].find(col => col in transformed_data);
    const observations = obsCol ? transformed_data[obsCol] : [];

    // Get all variables (excluding const)
    const vars = Object.keys(variable_contributions).filter(v => v !== 'const');

    // Build chart data
    const data = observations.map((obs, idx) => {
      const row: Record<string, any> = { obs: String(obs) };

      // Add intercept first
      if (coefficients.const !== undefined) {
        row['Intercept'] = coefficients.const;
      }

      // Add each variable's contribution
      vars.forEach(varName => {
        const contributions = variable_contributions[varName];
        if (contributions && contributions[idx] !== undefined) {
          row[varName] = contributions[idx];
        }
      });

      return row;
    });

    // Prepend 'Intercept' to variables list if it exists
    const allVars = coefficients.const !== undefined ? ['Intercept', ...vars] : vars;

    return { chartData: data, variables: allVars };
  }, [regressionResults]);

  if (!regressionResults) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Decomposition</CardTitle>
          <CardDescription>Variable contribution breakdown over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
              Please run the regression first to see the decomposition chart.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Decomposition</CardTitle>
        <CardDescription>
          Variable contributions to {modelConfig?.kpi} broken down by observation
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
            <div className="text-muted-foreground mb-1">Variables</div>
            <div className="text-2xl font-semibold">{variables.length}</div>
          </div>
          <div className="border rounded-md p-3 bg-muted/30">
            <div className="text-muted-foreground mb-1">Model R²</div>
            <div className="text-2xl font-semibold">{regressionResults.r_squared.toFixed(4)}</div>
          </div>
        </div>

        {/* Chart */}
        <div className="w-full h-[600px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 120, left: 20, bottom: 60 }}>
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
                label={{ value: 'Contribution', angle: -90, position: 'insideLeft' }}
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
                layout="vertical"
                align="right"
                verticalAlign="top"
                iconType="square"
              />
              {variables.map((varName, idx) => (
                <Bar
                  key={varName}
                  dataKey={varName}
                  stackId="stack"
                  fill={COLORS[idx % COLORS.length]}
                  name={varName.length > 20 ? varName.substring(0, 17) + '...' : varName}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="text-xs text-muted-foreground space-y-1">
          <p>This stacked bar chart shows how each variable contributes to the predicted {modelConfig?.kpi} value at each observation.</p>
          <p>Contribution = Coefficient × Transformed Variable Value</p>
          <p>The sum of all contributions equals the fitted value for that observation.</p>
        </div>
      </CardContent>
    </Card>
  );
}
