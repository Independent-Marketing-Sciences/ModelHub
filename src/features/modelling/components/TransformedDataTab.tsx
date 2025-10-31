"use client";

import { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useModellingStore } from "@/lib/store/modelling-store";
import { AlertCircle } from "lucide-react";

export function TransformedDataTab() {
  const { regressionResults, modelConfig } = useModellingStore();

  // Prepare table data
  const tableData = useMemo(() => {
    if (!regressionResults?.transformed_data) return { columns: [], rows: [] };

    const data = regressionResults.transformed_data;
    const columns = Object.keys(data);
    const rowCount = data[columns[0]]?.length || 0;

    const rows = Array.from({ length: rowCount }, (_, idx) => {
      const row: Record<string, any> = {};
      columns.forEach((col) => {
        row[col] = data[col][idx];
      });
      return row;
    });

    return { columns, rows };
  }, [regressionResults]);

  if (!regressionResults) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transformed Data</CardTitle>
          <CardDescription>View transformed variables after applying adstock, lags, and other transformations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
              Please run the regression first to see transformed data.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transformed Data</CardTitle>
        <CardDescription>
          Variables after applying transformations (adstock, lags, leads, diminishing returns)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="text-muted-foreground mb-1">Observations</div>
              <div className="text-2xl font-semibold">{tableData.rows.length}</div>
            </div>
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="text-muted-foreground mb-1">Variables</div>
              <div className="text-2xl font-semibold">{tableData.columns.length}</div>
            </div>
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="text-muted-foreground mb-1">KPI</div>
              <div className="text-lg font-semibold">{modelConfig?.kpi || 'N/A'}</div>
            </div>
          </div>

          {/* Data Table */}
          <div className="border rounded-md overflow-hidden">
            <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted sticky top-0 z-10">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium border-r">#</th>
                    {tableData.columns.map((col) => (
                      <th key={col} className="px-4 py-3 text-right font-medium whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableData.rows.map((row, idx) => (
                    <tr key={idx} className="border-t hover:bg-muted/50">
                      <td className="px-4 py-2 text-left font-mono text-muted-foreground border-r">
                        {idx + 1}
                      </td>
                      {tableData.columns.map((col) => (
                        <td key={col} className="px-4 py-2 text-right font-mono">
                          {typeof row[col] === 'number'
                            ? row[col].toFixed(4)
                            : row[col]
                          }
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="text-xs text-muted-foreground">
            <p>This data shows all variables after transformation pipeline:</p>
            <p>Pre-transform → Lag/Lead → Adstock/Diminishing Returns → Post-transform</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
