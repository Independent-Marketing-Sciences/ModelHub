"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function ModelStatsTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Model Statistics</CardTitle>
        <CardDescription>Regression diagnostics and model fit statistics</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-12 text-muted-foreground">
          <p>Model statistics coming soon</p>
          <p className="text-sm mt-2">R², Adjusted R², F-statistic, and diagnostic tests</p>
        </div>
      </CardContent>
    </Card>
  );
}
