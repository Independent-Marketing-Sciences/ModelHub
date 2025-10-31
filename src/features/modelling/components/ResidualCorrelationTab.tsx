"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useModellingStore } from "@/lib/store/modelling-store";
import { AlertCircle } from "lucide-react";
import { Input } from "@/components/ui/input";

// Helper function to calculate correlation between two arrays
function calculateCorrelation(x: number[], y: number[]): number {
  const n = Math.min(x.length, y.length);
  if (n === 0) return 0;

  // Calculate means
  const meanX = x.slice(0, n).reduce((sum, val) => sum + val, 0) / n;
  const meanY = y.slice(0, n).reduce((sum, val) => sum + val, 0) / n;

  // Calculate correlation coefficient
  let numerator = 0;
  let sumXSquared = 0;
  let sumYSquared = 0;

  for (let i = 0; i < n; i++) {
    const dx = x[i] - meanX;
    const dy = y[i] - meanY;
    numerator += dx * dy;
    sumXSquared += dx * dx;
    sumYSquared += dy * dy;
  }

  const denominator = Math.sqrt(sumXSquared * sumYSquared);
  return denominator === 0 ? 0 : numerator / denominator;
}

// Helper to get cell background color based on correlation
function getCorrelationColor(correlation: number): string {
  const absCorr = Math.abs(correlation);
  if (absCorr > 0.7) return correlation > 0 ? "bg-green-100 dark:bg-green-950" : "bg-red-100 dark:bg-red-950";
  if (absCorr > 0.5) return correlation > 0 ? "bg-green-50 dark:bg-green-900/30" : "bg-red-50 dark:bg-red-900/30";
  if (absCorr > 0.3) return correlation > 0 ? "bg-green-50/50 dark:bg-green-900/20" : "bg-red-50/50 dark:bg-red-900/20";
  return "";
}

export function ResidualCorrelationTab() {
  const { regressionResults } = useModellingStore();
  const [searchTerm, setSearchTerm] = useState("");

  // Calculate correlations between residuals and all variables
  const correlations = useMemo(() => {
    if (!regressionResults) return [];

    const { residuals, transformed_data } = regressionResults;

    const results: Array<{ variable: string; correlation: number }> = [];

    // Calculate correlation for each variable in transformed data
    Object.keys(transformed_data).forEach(varName => {
      // Skip observation columns
      if (['obs', 'OBS', 'date', 'Date'].includes(varName)) return;

      const varData = transformed_data[varName];
      if (!Array.isArray(varData)) return;

      // Filter out non-numeric values
      const numericData = varData.filter(v => typeof v === 'number') as number[];
      if (numericData.length === 0) return;

      const correlation = calculateCorrelation(residuals, numericData);
      results.push({ variable: varName, correlation });
    });

    // Sort by absolute correlation (descending)
    return results.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
  }, [regressionResults]);

  // Filter correlations based on search term
  const filteredCorrelations = useMemo(() => {
    if (!searchTerm) return correlations;
    const lowerSearch = searchTerm.toLowerCase();
    return correlations.filter(c => c.variable.toLowerCase().includes(lowerSearch));
  }, [correlations, searchTerm]);

  if (!regressionResults) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Residual Correlation</CardTitle>
          <CardDescription>Analyze correlations between residuals and variables</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
              Please run the regression first to see residual correlations.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Residual Correlation</CardTitle>
        <CardDescription>
          Correlation between model residuals and transformed variables (ideally should be close to 0)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="border rounded-md p-3 bg-muted/30">
            <div className="text-muted-foreground mb-1">Total Variables</div>
            <div className="text-2xl font-semibold">{correlations.length}</div>
          </div>
          <div className="border rounded-md p-3 bg-muted/30">
            <div className="text-muted-foreground mb-1">Max |Correlation|</div>
            <div className="text-2xl font-semibold">
              {correlations.length > 0 ? Math.abs(correlations[0].correlation).toFixed(4) : 'N/A'}
            </div>
          </div>
          <div className="border rounded-md p-3 bg-muted/30">
            <div className="text-muted-foreground mb-1">Mean |Correlation|</div>
            <div className="text-2xl font-semibold">
              {correlations.length > 0
                ? (correlations.reduce((sum, c) => sum + Math.abs(c.correlation), 0) / correlations.length).toFixed(4)
                : 'N/A'}
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div>
          <Input
            type="text"
            placeholder="Search variables..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>

        {/* Correlation Table */}
        <div className="border rounded-md overflow-hidden">
          <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Variable</th>
                  <th className="px-4 py-3 text-right font-medium">Correlation</th>
                  <th className="px-4 py-3 text-right font-medium">|Correlation|</th>
                  <th className="px-4 py-3 text-center font-medium">Strength</th>
                </tr>
              </thead>
              <tbody>
                {filteredCorrelations.map((item) => {
                  const absCorr = Math.abs(item.correlation);
                  let strength = 'Weak';
                  if (absCorr > 0.7) strength = 'Strong';
                  else if (absCorr > 0.5) strength = 'Moderate';
                  else if (absCorr > 0.3) strength = 'Mild';

                  return (
                    <tr
                      key={item.variable}
                      className={`border-t hover:bg-muted/50 ${getCorrelationColor(item.correlation)}`}
                    >
                      <td className="px-4 py-3 font-medium">{item.variable}</td>
                      <td className="px-4 py-3 text-right font-mono">
                        {item.correlation >= 0 ? '+' : ''}{item.correlation.toFixed(4)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono">{absCorr.toFixed(4)}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`text-xs px-2 py-1 rounded ${
                          absCorr > 0.5 ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200' :
                          absCorr > 0.3 ? 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200' :
                          'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                        }`}>
                          {strength}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="text-xs text-muted-foreground space-y-1">
          <p><strong>Interpretation:</strong> High correlations (|r| &gt; 0.5) suggest the residuals contain patterns related to that variable, indicating potential model misspecification.</p>
          <p><strong>Ideal:</strong> All correlations should be close to 0, meaning residuals are random and uncorrelated with predictors.</p>
          <p><strong>Color coding:</strong> Green = positive correlation, Red = negative correlation. Intensity indicates strength.</p>
        </div>
      </CardContent>
    </Card>
  );
}
