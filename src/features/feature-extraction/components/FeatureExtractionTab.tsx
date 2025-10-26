"use client";

import { useState, useMemo } from "react";
import { useDataStore } from "@/lib/store/index";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { Input } from "@/components/ui/input";
import { pythonClient } from "@/lib/api/python-client";
import { Loader2, Sparkles, TrendingUp, BarChart3, Filter } from "lucide-react";

export function FeatureExtractionTab() {
  const { columns, dateColumn, getFilteredData } = useDataStore();
  const [selectedKPI, setSelectedKPI] = useState("");
  const [nFeatures, setNFeatures] = useState(10);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [variableFilter, setVariableFilter] = useState("");
  const [regexError, setRegexError] = useState<string | null>(null);

  // Get data filtered by date range from store
  const data = getFilteredData();

  // Filter columns based on regex
  const filteredColumns = useMemo(() => {
    if (!variableFilter.trim()) {
      return columns.filter((col) => col !== dateColumn);
    }

    try {
      const regex = new RegExp(variableFilter, 'i');
      setRegexError(null);
      return columns.filter((col) => col !== dateColumn && regex.test(col));
    } catch (e) {
      setRegexError("Invalid regex pattern");
      return columns.filter((col) => col !== dateColumn);
    }
  }, [columns, dateColumn, variableFilter]);

  const handleExtract = async () => {
    if (!selectedKPI) {
      setError("Please select a KPI variable");
      return;
    }

    if (filteredColumns.length === 0) {
      setError("No variables match the filter. Please adjust your regex filter.");
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // Convert data array to column-based object
      // Only include filtered columns plus the selected KPI
      const dataByColumn: Record<string, number[]> = {};
      const columnsToInclude = new Set([...filteredColumns, selectedKPI, dateColumn]);

      columns.forEach((col) => {
        if (columnsToInclude.has(col)) {
          dataByColumn[col] = data.map((row) => {
            const value = row[col];
            return typeof value === "number" ? value : parseFloat(String(value)) || 0;
          });
        }
      });

      const response = await pythonClient.post("/api/feature-extraction/extract", {
        data: dataByColumn,
        kpi_var: selectedKPI,
        date_column: dateColumn,
        n_features: nFeatures,
        test_size: 0.1,
        random_state: 42,
        shuffle: false,
      });

      setResults(response);
    } catch (err: any) {
      console.error("Feature extraction error:", err);
      setError(err.message || "Failed to extract features");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <CardTitle>Feature Extraction</CardTitle>
          <CardDescription>
            Use XGBoost and Random Forest to identify the most important features for modeling
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* KPI Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Select KPI Variable</label>
              <SearchableSelect
                value={selectedKPI}
                onValueChange={setSelectedKPI}
                options={columns
                  .filter((col) => col !== dateColumn)
                  .map((col) => ({ value: col, label: col }))}
                placeholder="Choose target variable"
              />
            </div>

            {/* Number of Features */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Number of Top Features</label>
              <Input
                type="number"
                value={nFeatures}
                onChange={(e) => setNFeatures(parseInt(e.target.value) || 10)}
                min={1}
                max={50}
              />
            </div>
          </div>

          {/* Variable Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Filter Variables (Regex)
            </label>
            <Input
              placeholder="e.g., ^seas_|^media_ to filter variables starting with seas_ or media_"
              value={variableFilter}
              onChange={(e) => setVariableFilter(e.target.value)}
              className={regexError ? "border-destructive" : ""}
            />
            {regexError && (
              <p className="text-xs text-destructive">{regexError}</p>
            )}
            <p className="text-xs text-muted-foreground">
              {filteredColumns.length} variable(s) match the filter
              {variableFilter && ` (filtering out ${columns.filter(c => c !== dateColumn).length - filteredColumns.length})`}
            </p>
          </div>

          <Button onClick={handleExtract} disabled={loading || !selectedKPI} className="w-full">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Extracting Features...
              </>
            ) : (
              <>
                <TrendingUp className="mr-2 h-4 w-4" />
                Extract Features
              </>
            )}
          </Button>

          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Card */}
      {results && (
        <Card>
          <CardHeader>
            <CardTitle>Feature Extraction Results</CardTitle>
            <CardDescription>
              {results.n_features_selected} features selected from {results.n_features_total} total features
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Statistics */}
            <div className="grid grid-cols-4 gap-4">
              <div className="p-4 bg-muted/50 rounded-lg border">
                <p className="text-sm text-muted-foreground">Total Features</p>
                <p className="text-2xl font-bold">{results.n_features_total}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg border">
                <p className="text-sm text-muted-foreground">Selected Features</p>
                <p className="text-2xl font-bold">{results.n_features_selected}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg border">
                <p className="text-sm text-muted-foreground">Train Samples</p>
                <p className="text-2xl font-bold">{results.n_samples_train}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg border">
                <p className="text-sm text-muted-foreground">Test Samples</p>
                <p className="text-2xl font-bold">{results.n_samples_test}</p>
              </div>
            </div>

            {/* Combined Features Table */}
            <div>
              <h3 className="text-sm font-medium mb-3">Combined Top Features (Ranked by Importance)</h3>
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="p-3 text-left text-sm font-medium border-b">Rank</th>
                      <th className="p-3 text-left text-sm font-medium border-b">Feature</th>
                      <th className="p-3 text-right text-sm font-medium border-b">XGBoost</th>
                      <th className="p-3 text-right text-sm font-medium border-b">Random Forest</th>
                      <th className="p-3 text-right text-sm font-medium border-b">Average</th>
                    </tr>
                  </thead>
                  <tbody className="bg-background">
                    {results.feature_importances.map((item: any, idx: number) => (
                      <tr key={idx} className="border-b hover:bg-muted/50">
                        <td className="p-3 text-sm">{idx + 1}</td>
                        <td className="p-3 text-sm font-medium">{item.feature}</td>
                        <td className="p-3 text-right text-sm">{item.xgb_importance.toFixed(4)}</td>
                        <td className="p-3 text-right text-sm">{item.rf_importance.toFixed(4)}</td>
                        <td className="p-3 text-right text-sm font-semibold">{item.avg_importance.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Feature Lists */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium mb-2">Top Features (XGBoost)</h3>
                <div className="border rounded-lg p-4 space-y-1 bg-muted/30">
                  {results.top_features_xgb.map((feature: string, idx: number) => (
                    <div key={idx} className="text-sm flex items-center gap-2">
                      <span className="text-muted-foreground">{idx + 1}.</span>
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium mb-2">Top Features (Random Forest)</h3>
                <div className="border rounded-lg p-4 space-y-1 bg-muted/30">
                  {results.top_features_rf.map((feature: string, idx: number) => (
                    <div key={idx} className="text-sm flex items-center gap-2">
                      <span className="text-muted-foreground">{idx + 1}.</span>
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
