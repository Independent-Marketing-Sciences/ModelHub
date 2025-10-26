"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

export function StepwiseRegressionTab() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Stepwise Regression</CardTitle>
          <CardDescription>
            Automated variable selection for regression modeling
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <AlertCircle className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-lg mb-2">Coming Soon</p>
            <p className="text-sm">
              Stepwise regression functionality will be implemented in a future update
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
