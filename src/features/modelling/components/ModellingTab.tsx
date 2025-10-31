"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import { useDataStore } from "@/lib/store";

// Import sub-components
import { ModelDetailsTab } from "./ModelDetailsTab";
import { VariableDetailsTab } from "./VariableDetailsTab";
import { XSDetailsTab } from "./XSDetailsTab";
import { TransformedDataTab } from "./TransformedDataTab";
import { ContributionTab } from "./ContributionTab";
import { ModelStatsTab } from "./ModelStatsTab";
import { DecompTab } from "./DecompTab";
import { AvMTab } from "./AvMTab";
import { ResidualCorrelationTab } from "./ResidualCorrelationTab";

export function ModellingTab() {
  const { data } = useDataStore();
  const [modelConfigured, setModelConfigured] = useState(false);
  const [regressionRun, setRegressionRun] = useState(false);

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Econometric Modelling</CardTitle>
          <CardDescription>
            Build and analyze regression models with advanced transformations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
              No data loaded. Please upload a dataset first to begin modelling.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Econometric Modelling</CardTitle>
          <CardDescription>
            Build and analyze regression models with advanced transformations, adstock, and diminishing returns
          </CardDescription>
        </CardHeader>
      </Card>

      <Tabs defaultValue="model-details" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 lg:grid-cols-9">
          <TabsTrigger value="model-details">Model Details</TabsTrigger>
          <TabsTrigger value="variable-details">Variable Details</TabsTrigger>
          <TabsTrigger value="xs-details">XS Details</TabsTrigger>
          <TabsTrigger value="transformed-data" disabled={!regressionRun}>
            Transformed Data
          </TabsTrigger>
          <TabsTrigger value="contribution" disabled={!regressionRun}>
            Contribution
          </TabsTrigger>
          <TabsTrigger value="model-stats" disabled={!regressionRun}>
            Model Stats
          </TabsTrigger>
          <TabsTrigger value="decomp" disabled={!regressionRun}>
            Decomp
          </TabsTrigger>
          <TabsTrigger value="avm" disabled={!regressionRun}>
            AvM
          </TabsTrigger>
          <TabsTrigger value="residual-correlation" disabled={!regressionRun}>
            Residual Corr
          </TabsTrigger>
        </TabsList>

        <TabsContent value="model-details">
          <ModelDetailsTab onModelConfigured={setModelConfigured} />
        </TabsContent>

        <TabsContent value="variable-details">
          <VariableDetailsTab
            modelConfigured={modelConfigured}
            onRegressionComplete={() => setRegressionRun(true)}
          />
        </TabsContent>

        <TabsContent value="xs-details">
          <XSDetailsTab modelConfigured={modelConfigured} />
        </TabsContent>

        <TabsContent value="transformed-data">
          <TransformedDataTab />
        </TabsContent>

        <TabsContent value="contribution">
          <ContributionTab />
        </TabsContent>

        <TabsContent value="model-stats">
          <ModelStatsTab />
        </TabsContent>

        <TabsContent value="decomp">
          <DecompTab />
        </TabsContent>

        <TabsContent value="avm">
          <AvMTab />
        </TabsContent>

        <TabsContent value="residual-correlation">
          <ResidualCorrelationTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
