"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function AvMTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Actual vs Model</CardTitle>
        <CardDescription>Compare actual values with model predictions</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-12 text-muted-foreground">
          <p>Actual vs Model comparison coming soon</p>
          <p className="text-sm mt-2">Time series chart showing fitted values vs actuals</p>
        </div>
      </CardContent>
    </Card>
  );
}
