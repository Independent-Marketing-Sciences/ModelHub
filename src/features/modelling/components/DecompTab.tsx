"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function DecompTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Decomposition</CardTitle>
        <CardDescription>Decompose the model into its components</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-12 text-muted-foreground">
          <p>Decomposition analysis coming soon</p>
        </div>
      </CardContent>
    </Card>
  );
}
