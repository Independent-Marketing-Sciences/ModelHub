"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useModellingStore } from "@/lib/store/modelling-store";
import { formatCoefficient, formatPValue } from "@/lib/api/modelling-client";
import { AlertCircle, CheckCircle, XCircle } from "lucide-react";

export function ModelStatsTab() {
  const { regressionResults } = useModellingStore();

  if (!regressionResults) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Model Statistics</CardTitle>
          <CardDescription>Regression diagnostics and model fit statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
              Please run the regression first to see model statistics.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const {
    coefficients,
    p_values,
    t_stats,
    r_squared,
    adjusted_r_squared,
    f_statistic,
    f_pvalue,
    aic,
    bic,
    durbin_watson,
    diagnostics,
    n_observations,
    degrees_of_freedom,
  } = regressionResults;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Model Statistics</CardTitle>
        <CardDescription>Regression coefficients, fit statistics, and diagnostic tests</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Model Fit Statistics */}
        <div>
          <h3 className="text-sm font-semibold mb-3">Model Fit</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="text-xs text-muted-foreground mb-1">R²</div>
              <div className="text-xl font-semibold">{r_squared.toFixed(4)}</div>
            </div>
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="text-xs text-muted-foreground mb-1">Adjusted R²</div>
              <div className="text-xl font-semibold">{adjusted_r_squared.toFixed(4)}</div>
            </div>
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="text-xs text-muted-foreground mb-1">AIC / BIC</div>
              <div className="text-lg font-semibold">{aic.toFixed(1)} / {bic.toFixed(1)}</div>
            </div>
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="text-xs text-muted-foreground mb-1">Durbin-Watson</div>
              <div className="text-xl font-semibold">{durbin_watson.toFixed(3)}</div>
            </div>
          </div>
        </div>

        {/* Coefficients Table */}
        <div>
          <h3 className="text-sm font-semibold mb-3">Coefficients</h3>
          <div className="rounded-md border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Variable</th>
                  <th className="px-4 py-3 text-right font-medium">Coefficient</th>
                  <th className="px-4 py-3 text-right font-medium">t-Statistic</th>
                  <th className="px-4 py-3 text-right font-medium">p-value</th>
                  <th className="px-4 py-3 text-center font-medium">Sig.</th>
                </tr>
              </thead>
              <tbody>
                {Object.keys(coefficients).map((varName) => {
                  const pValue = p_values[varName];
                  const isSignificant = pValue < 0.05;
                  return (
                    <tr key={varName} className={`border-t hover:bg-muted/50 ${isSignificant ? "bg-green-50/30 dark:bg-green-950/10" : ""}`}>
                      <td className="px-4 py-3 font-medium">{varName}</td>
                      <td className="px-4 py-3 text-right font-mono">{formatCoefficient(coefficients[varName])}</td>
                      <td className="px-4 py-3 text-right font-mono">{t_stats[varName].toFixed(3)}</td>
                      <td className="px-4 py-3 text-right font-mono">{formatPValue(pValue)}</td>
                      <td className="px-4 py-3 text-center">
                        {isSignificant ? <CheckCircle className="h-4 w-4 inline text-green-600" /> : <XCircle className="h-4 w-4 inline text-gray-400" />}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Diagnostic Tests - Simplified */}
        {diagnostics && (
          <div>
            <h3 className="text-sm font-semibold mb-3">Diagnostic Tests</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="border rounded-md p-3 bg-muted/30">
                <div className="font-medium mb-1">Jarque-Bera</div>
                <div className="font-mono">{diagnostics.jarque_bera_stat.toFixed(2)} (p={diagnostics.jarque_bera_pvalue.toFixed(3)})</div>
              </div>
              <div className="border rounded-md p-3 bg-muted/30">
                <div className="font-medium mb-1">Breusch-Pagan</div>
                <div className="font-mono">{diagnostics.breusch_pagan_stat.toFixed(2)} (p={diagnostics.breusch_pagan_pvalue.toFixed(3)})</div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
