"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { AlertCircle, Play, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import { useDataStore } from "@/lib/store";
import { useModellingStore } from "@/lib/store/modelling-store";
import { modellingClient, convertDataForAPI, VariableTransformation } from "@/lib/api/modelling-client";

interface VariableDetailsTabProps {
  modelConfigured: boolean;
  onRegressionComplete: () => void;
}

export function VariableDetailsTab({ modelConfigured, onRegressionComplete }: VariableDetailsTabProps) {
  const { data } = useDataStore();
  const {
    modelConfig,
    variableTransformations,
    updateVariableTransformation,
    setRegressionResults,
    setRegressionRunning,
    setRegressionComplete,
    regressionRunning,
    setError,
  } = useModellingStore();

  const [expandedVariable, setExpandedVariable] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState("");

  // Filter variables based on search
  const filteredTransformations = useMemo(() => {
    if (!searchFilter) return variableTransformations;
    return variableTransformations.filter((t) =>
      t.variable.toLowerCase().includes(searchFilter.toLowerCase())
    );
  }, [variableTransformations, searchFilter]);

  // Toggle variable expansion
  const toggleExpand = (variable: string) => {
    setExpandedVariable(expandedVariable === variable ? null : variable);
  };

  // Update transformation field
  const updateField = (variable: string, field: keyof VariableTransformation, value: any) => {
    updateVariableTransformation(variable, { [field]: value });
  };

  // Run regression
  const handleRunRegression = async () => {
    if (!modelConfig) {
      setError("Please configure model details first");
      return;
    }

    setRegressionRunning(true);
    setError(null);

    try {
      // Check backend availability
      const isAvailable = await modellingClient.isAvailable();
      if (!isAvailable) {
        throw new Error("Python backend is not running. Please ensure the backend is started.");
      }

      // Prepare request
      const request = {
        model_configuration: modelConfig,
        variable_transformations: variableTransformations,
        data: convertDataForAPI(data),
      };

      // Run regression
      const results = await modellingClient.runRegression(request);

      // Store results
      setRegressionResults(results);
      setRegressionComplete(true);
      onRegressionComplete();
    } catch (error) {
      console.error("Regression error:", error);
      setError(error instanceof Error ? error.message : "Regression failed");
    } finally {
      setRegressionRunning(false);
    }
  };

  if (!modelConfigured) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Variable Details</CardTitle>
          <CardDescription>Configure transformations for each variable</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
              Please configure Model Details first before setting up variable transformations.
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
          <CardTitle>Variable Transformations</CardTitle>
          <CardDescription>
            Configure transformations, adstock, and diminishing returns for each variable
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search and Run Regression */}
          <div className="flex items-center gap-4">
            <Input
              placeholder="Search variables..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="flex-1"
            />
            <Button
              onClick={handleRunRegression}
              disabled={regressionRunning || variableTransformations.filter(t => t.include).length === 0}
              size="lg"
            >
              {regressionRunning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running Regression...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Run Regression
                </>
              )}
            </Button>
          </div>

          {/* Variables List */}
          <div className="space-y-2 max-h-[600px] overflow-y-auto border rounded-md">
            {filteredTransformations.map((transformation) => (
              <div key={transformation.variable} className="border-b last:border-b-0">
                {/* Variable Header */}
                <div
                  className="flex items-center gap-3 p-3 hover:bg-muted/50 cursor-pointer"
                  onClick={() => toggleExpand(transformation.variable)}
                >
                  <Checkbox
                    checked={transformation.include}
                    onCheckedChange={(checked) =>
                      updateField(transformation.variable, "include", checked)
                    }
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="flex-1 font-medium">{transformation.variable}</div>
                  <div className="text-xs text-muted-foreground flex items-center gap-2">
                    {transformation.adstock > 0 && <span>Adstock: {transformation.adstock}</span>}
                    {transformation.dimret > 0 && <span>DimRet: {transformation.dimret}</span>}
                    {transformation.lag > 0 && <span>Lag: {transformation.lag}</span>}
                    {transformation.lead > 0 && <span>Lead: {transformation.lead}</span>}
                  </div>
                  {expandedVariable === transformation.variable ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </div>

                {/* Expanded Transformation Controls */}
                {expandedVariable === transformation.variable && (
                  <div className="p-4 bg-muted/30 space-y-4 border-t">
                    <div className="grid grid-cols-2 gap-4">
                      {/* Pre-Transform */}
                      <div className="space-y-2">
                        <Label className="text-xs">Pre-Transform</Label>
                        <Select
                          value={transformation.pre_transform || "none"}
                          onValueChange={(value) =>
                            updateField(transformation.variable, "pre_transform", value === "none" ? null : value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">None</SelectItem>
                            <SelectItem value="log">log(x)</SelectItem>
                            <SelectItem value="sqrt">sqrt(x)</SelectItem>
                            <SelectItem value="exp">exp(x)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Post-Transform */}
                      <div className="space-y-2">
                        <Label className="text-xs">Post-Transform</Label>
                        <Select
                          value={transformation.post_transform || "none"}
                          onValueChange={(value) =>
                            updateField(transformation.variable, "post_transform", value === "none" ? null : value)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">None</SelectItem>
                            <SelectItem value="log">log(x)</SelectItem>
                            <SelectItem value="sqrt">sqrt(x)</SelectItem>
                            <SelectItem value="exp">exp(x)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Lag */}
                      <div className="space-y-2">
                        <Label className="text-xs">Lag</Label>
                        <Input
                          type="number"
                          min="0"
                          max="52"
                          value={transformation.lag}
                          onChange={(e) =>
                            updateField(transformation.variable, "lag", parseInt(e.target.value) || 0)
                          }
                        />
                      </div>

                      {/* Lead */}
                      <div className="space-y-2">
                        <Label className="text-xs">Lead</Label>
                        <Input
                          type="number"
                          min="0"
                          max="52"
                          value={transformation.lead}
                          onChange={(e) =>
                            updateField(transformation.variable, "lead", parseInt(e.target.value) || 0)
                          }
                        />
                      </div>

                      {/* Adstock */}
                      <div className="space-y-2">
                        <Label className="text-xs">Adstock Rate (0-1)</Label>
                        <Input
                          type="number"
                          min="0"
                          max="1"
                          step="0.01"
                          value={transformation.adstock}
                          onChange={(e) =>
                            updateField(transformation.variable, "adstock", parseFloat(e.target.value) || 0)
                          }
                        />
                      </div>

                      {/* Diminishing Returns */}
                      <div className="space-y-2">
                        <Label className="text-xs">Diminishing Returns (0-1)</Label>
                        <Input
                          type="number"
                          min="0"
                          max="1"
                          step="0.01"
                          value={transformation.dimret}
                          onChange={(e) =>
                            updateField(transformation.variable, "dimret", parseFloat(e.target.value) || 0)
                          }
                        />
                      </div>
                    </div>

                    {/* Combined Dimret + Adstock */}
                    <div className="flex items-center gap-2">
                      <Checkbox
                        checked={transformation.dimret_adstock}
                        onCheckedChange={(checked) =>
                          updateField(transformation.variable, "dimret_adstock", checked)
                        }
                      />
                      <Label className="text-xs cursor-pointer">
                        Combined Adstock + Diminishing Returns
                      </Label>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="text-sm text-muted-foreground">
            {variableTransformations.filter((t) => t.include).length} of {variableTransformations.length} variables included
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
