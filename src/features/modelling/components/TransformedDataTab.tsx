"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function TransformedDataTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Transformed Data</CardTitle>
        <CardDescription>View transformed variables after applying adstock, lags, and other transformations</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-12 text-muted-foreground">
          <p>Transformed data view coming soon</p>
        </div>
      </CardContent>
    </Card>
  );
}
