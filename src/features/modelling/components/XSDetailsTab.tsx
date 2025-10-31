"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface XSDetailsTabProps {
  modelConfigured: boolean;
}

export function XSDetailsTab({ modelConfigured }: XSDetailsTabProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Cross-Section Details</CardTitle>
        <CardDescription>Configure cross-section specific parameters</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-12 text-muted-foreground">
          <p>Cross-section configuration coming soon</p>
        </div>
      </CardContent>
    </Card>
  );
}
