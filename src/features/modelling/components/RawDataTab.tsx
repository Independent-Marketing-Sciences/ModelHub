"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useDataStore } from "@/lib/store";

export function RawDataTab() {
  const { data, columns } = useDataStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Raw Data</CardTitle>
        <CardDescription>View the raw input data for modelling</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground mb-4">
          {data.length} rows × {columns.length} columns
        </div>
        <div className="rounded-md border overflow-auto max-h-[600px]">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 sticky top-0">
              <tr>
                {columns.slice(0, 10).map((col) => (
                  <th key={col} className="px-4 py-2 text-left font-medium border-b">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 50).map((row, idx) => (
                <tr key={idx} className="hover:bg-muted/30">
                  {columns.slice(0, 10).map((col) => (
                    <td key={col} className="px-4 py-2 border-b">
                      {String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
