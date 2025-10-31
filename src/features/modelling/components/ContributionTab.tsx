"use client";

import { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useModellingStore } from "@/lib/store/modelling-store";
import { formatCoefficient, formatPValue, getSignificanceStars } from "@/lib/api/modelling-client";
import { AlertCircle } from "lucide-react";

export function ContributionTab() {
  const { regressionResults } = useModellingStore();

  // Calculate summary statistics for each variable
  const contributionSummary = useMemo(() => {
    if (!regressionResults) return [];

    const { coefficients, p_values, t_stats, variable_contributions } = regressionResults;

    return Object.keys(coefficients)
      .filter((varName) => varName !== "const")
      .map((varName) => {
        const contributions = variable_contributions[varName] || [];
        const totalContribution = contributions.reduce((sum, val) => sum + val, 0);
        const avgContribution = totalContribution / contributions.length;

        return {
          variable: varName,
          coefficient: coefficients[varName],
          pValue: p_values[varName],
          tStat: t_stats[varName],
          totalContribution,
          avgContribution,
          significance: getSignificanceStars(p_values[varName]),
        };
      })
      .sort((a, b) => Math.abs(b.totalContribution) - Math.abs(a.totalContribution));
  }, [regressionResults]);

  if (!regressionResults) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Contribution Analysis</CardTitle>
          <CardDescription>Variable contributions to the target KPI</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
              Please run the regression first to see contribution analysis.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { coefficients } = regressionResults;
  const interceptValue = coefficients.const || 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Contribution Analysis</CardTitle>
        <CardDescription>
          Variable coefficients and contributions to the target KPI
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Intercept */}
        <div className="border rounded-md p-4 bg-muted/30">
          <div className="flex justify-between items-center">
            <span className="font-medium">Intercept (Constant)</span>
            <span className="text-lg font-mono">{formatCoefficient(interceptValue)}</span>
          </div>
        </div>

        {/* Contribution Table */}
        <div className="rounded-md border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Variable</th>
                <th className="px-4 py-3 text-right font-medium">Coefficient</th>
                <th className="px-4 py-3 text-right font-medium">t-Statistic</th>
                <th className="px-4 py-3 text-right font-medium">p-value</th>
                <th className="px-4 py-3 text-right font-medium">Total Contribution</th>
                <th className="px-4 py-3 text-right font-medium">Avg Contribution</th>
                <th className="px-4 py-3 text-center font-medium">Sig.</th>
              </tr>
            </thead>
            <tbody>
              {contributionSummary.map((row, idx) => (
                <tr
                  key={row.variable}
                  className={`border-t hover:bg-muted/50 ${
                    row.pValue < 0.05 ? "bg-green-50/30 dark:bg-green-950/10" : ""
                  }`}
                >
                  <td className="px-4 py-3 font-medium">{row.variable}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatCoefficient(row.coefficient)}</td>
                  <td className="px-4 py-3 text-right font-mono">{row.tStat.toFixed(3)}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatPValue(row.pValue)}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatCoefficient(row.totalContribution)}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatCoefficient(row.avgContribution)}</td>
                  <td className="px-4 py-3 text-center font-bold text-amber-600">{row.significance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div className="text-xs text-muted-foreground space-y-1">
          <p>*** p {"<"} 0.001, ** p {"<"} 0.01, * p {"<"} 0.05</p>
          <p>Total Contribution = Sum of (coefficient × variable value) across all observations</p>
          <p>Variables highlighted in green are statistically significant (p {"<"} 0.05)</p>
        </div>
      </CardContent>
    </Card>
  );
}
