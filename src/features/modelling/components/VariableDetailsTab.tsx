"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertCircle, Play, Loader2, Plus, Trash2 } from "lucide-react";
import { useDataStore } from "@/lib/store";
import { useModellingStore } from "@/lib/store/modelling-store";
import { modellingClient, convertDataForAPI } from "@/lib/api/modelling-client";
import { parseFormula } from "@/lib/formula-parser";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface VariableDetailsTabProps {
  modelConfigured: boolean;
  onRegressionComplete: () => void;
}

interface VariableRow {
  id: string;
  variable: string;
  xsGrouping: string;
  referencePoint: string;
  interval: string;
  category: string;
  coeffMin: string;
  coeffMax: string;
  importance: string;
  shortVariableName: string;
  substitution: string;
  prior: string;
}

export function VariableDetailsTab({ modelConfigured, onRegressionComplete }: VariableDetailsTabProps) {
  const { data, columns } = useDataStore();
  const {
    modelConfig,
    setRegressionResults,
    setRegressionRunning,
    setRegressionComplete,
    regressionRunning,
    setError,
  } = useModellingStore();

  // Start with empty table
  const [variableRows, setVariableRows] = useState<VariableRow[]>([]);
  const [selectedVariable, setSelectedVariable] = useState<string>("");

  // Add variable from dropdown
  const addVariableFromDropdown = () => {
    if (!selectedVariable || variableRows.some(row => row.variable === selectedVariable)) {
      return;
    }

    const newId = `var-${Date.now()}`;
    setVariableRows((prev) => [
      ...prev,
      {
        id: newId,
        variable: selectedVariable, // Just the variable name
        xsGrouping: "",
        referencePoint: "",
        interval: "",
        category: "",
        coeffMin: "",
        coeffMax: "",
        importance: "",
        shortVariableName: selectedVariable,
        substitution: "", // Leave blank
        prior: "",
      },
    ]);
    setSelectedVariable("");
  };

  // Add empty row manually
  const addEmptyRow = () => {
    const newId = `var-${Date.now()}`;
    setVariableRows((prev) => [
      ...prev,
      {
        id: newId,
        variable: "",
        xsGrouping: "",
        referencePoint: "",
        interval: "",
        category: "",
        coeffMin: "",
        coeffMax: "",
        importance: "",
        shortVariableName: "",
        substitution: "",
        prior: "",
      },
    ]);
  };

  // Update cell value
  const updateCell = (id: string, field: keyof VariableRow, value: string) => {
    setVariableRows((prev) =>
      prev.map((row) => (row.id === id ? { ...row, [field]: value } : row))
    );
  };

  // Delete row
  const deleteRow = (id: string) => {
    setVariableRows((prev) => prev.filter((row) => row.id !== id));
  };

  // Run regression
  const handleRunRegression = async () => {
    if (!modelConfig) {
      setError("Please configure model details first");
      return;
    }

    if (variableRows.length === 0) {
      setError("Please add at least one variable");
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

      // Parse variable formulas into transformations
      const variableTransformations = variableRows
        .filter((row) => row.variable)
        .map((row) => {
          const parsed = parseFormula(row.variable);
          if (!parsed) {
            throw new Error(`Failed to parse variable formula: ${row.variable}`);
          }
          return parsed;
        });

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
          <CardDescription>Configure variable transformations and parameters</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 text-sm text-amber-800 dark:text-amber-300">
              Please configure Model Details first before setting up variables.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Get available columns not already added
  const availableColumns = columns.filter(
    col => !variableRows.some(row => row.variable === col)
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Variable Details</CardTitle>
        <CardDescription>
          Configure variables with transformations and parameters
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Add Variable Controls */}
        <div className="flex items-center gap-2">
          <Select value={selectedVariable} onValueChange={setSelectedVariable}>
            <SelectTrigger className="w-[250px]">
              <SelectValue placeholder="Add variable..." />
            </SelectTrigger>
            <SelectContent>
              {availableColumns.map((col) => (
                <SelectItem key={col} value={col}>
                  {col}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={addVariableFromDropdown}
            disabled={!selectedVariable}
            variant="outline"
            size="sm"
          >
            <Plus className="mr-1 h-4 w-4" />
            Add Selected
          </Button>
          <Button onClick={addEmptyRow} variant="outline" size="sm">
            <Plus className="mr-1 h-4 w-4" />
            Add Row
          </Button>
          <div className="flex-1" />
          <Button
            onClick={handleRunRegression}
            disabled={regressionRunning || variableRows.length === 0}
            size="lg"
          >
            {regressionRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Run Regression
              </>
            )}
          </Button>
        </div>

        {/* Variables Table */}
        {variableRows.length === 0 ? (
          <div className="border rounded-md p-12 text-center text-muted-foreground">
            <p>No variables added yet.</p>
            <p className="text-sm mt-2">
              Use &quot;Add variable...&quot; dropdown or &quot;Add Row&quot; button to begin.
            </p>
          </div>
        ) : (
          <div className="rounded-md border overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-3 py-2 text-left font-medium min-w-[120px]">Variable</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[100px]">XS Grouping</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[100px]">Reference Point</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[80px]">Interval</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[100px]">Category</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[80px]">Coeff Min</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[80px]">Coeff Max</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[100px]">Importance</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[120px]">Short Variable Name</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[200px]">Substitution</th>
                  <th className="px-3 py-2 text-left font-medium min-w-[100px]">Prior</th>
                  <th className="px-3 py-2 text-center font-medium w-16">Actions</th>
                </tr>
              </thead>
              <tbody>
                {variableRows.map((row) => (
                  <tr key={row.id} className="border-t hover:bg-muted/50">
                    <td className="px-3 py-2">
                      <Input
                        value={row.variable}
                        onChange={(e) => updateCell(row.id, "variable", e.target.value)}
                        className="h-8 text-xs font-mono"
                        placeholder="e.g., adstock(sales, 0.5)"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.xsGrouping}
                        onChange={(e) => updateCell(row.id, "xsGrouping", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.referencePoint}
                        onChange={(e) => updateCell(row.id, "referencePoint", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.interval}
                        onChange={(e) => updateCell(row.id, "interval", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.category}
                        onChange={(e) => updateCell(row.id, "category", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.coeffMin}
                        onChange={(e) => updateCell(row.id, "coeffMin", e.target.value)}
                        className="h-8 text-xs"
                        placeholder="Min"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.coeffMax}
                        onChange={(e) => updateCell(row.id, "coeffMax", e.target.value)}
                        className="h-8 text-xs"
                        placeholder="Max"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.importance}
                        onChange={(e) => updateCell(row.id, "importance", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.shortVariableName}
                        onChange={(e) => updateCell(row.id, "shortVariableName", e.target.value)}
                        className="h-8 text-xs"
                        placeholder="Short name"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.substitution}
                        onChange={(e) => updateCell(row.id, "substitution", e.target.value)}
                        className="h-8 text-xs"
                        placeholder="Optional"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <Input
                        value={row.prior}
                        onChange={(e) => updateCell(row.id, "prior", e.target.value)}
                        className="h-8 text-xs"
                      />
                    </td>
                    <td className="px-3 py-2 text-center">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteRow(row.id)}
                        className="h-7 w-7"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Instructions */}
        <div className="text-xs text-muted-foreground space-y-1 bg-muted/30 p-3 rounded-md">
          <p><strong>Variable formulas:</strong> adstock(sales, 0.5), log(dimret_adstock(marketing, 0.3, 0.4)), lag(price, 2)</p>
          <p><strong>Available functions:</strong> log, sqrt, exp, lag, lead, adstock, dimret, dimret_adstock</p>
          <p><strong>Enter transformation formulas in the Variable column</strong> - only Variable column is required for regression</p>
        </div>

        {/* Summary */}
        {variableRows.length > 0 && (
          <div className="text-sm text-muted-foreground">
            {variableRows.length} variable{variableRows.length !== 1 ? "s" : ""} configured
          </div>
        )}
      </CardContent>
    </Card>
  );
}
