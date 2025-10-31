/**
 * TypeScript client for Modelling API
 * Handles communication with Python backend for econometric modelling
 */

const API_BASE_URL = "http://localhost:8000/api/modelling";

// ============================================================================
// Types
// ============================================================================

export interface VariableTransformation {
  variable: string;
  include: boolean;
  pre_transform?: string | null; // 'log', 'sqrt', 'exp', null
  lag: number;
  lead: number;
  adstock: number; // 0-1
  dimret: number; // 0-1
  dimret_adstock: boolean;
  post_transform?: string | null;
}

export interface ModelConfiguration {
  kpi: string;
  start_date: string;
  end_date: string;
  xs_weights: string;
  log_trans_bias: boolean;
  take_anti_logs_at_midpoints: boolean;
}

export interface RegressionRequest {
  model_configuration: ModelConfiguration;
  variable_transformations: VariableTransformation[];
  data: Record<string, any[]>;
}

export interface RegressionResult {
  coefficients: Record<string, number>;
  p_values: Record<string, number>;
  t_stats: Record<string, number>;
  r_squared: number;
  adjusted_r_squared: number;
  f_statistic: number;
  f_pvalue: number;
  aic: number;
  bic: number;
  durbin_watson: number;
  residuals: number[];
  fitted_values: number[];
  transformed_data: Record<string, number[]>;
  variable_contributions: Record<string, number[]>;
  diagnostics: ModelDiagnostics;
  n_observations: number;
  degrees_of_freedom: number;
}

export interface ModelDiagnostics {
  jarque_bera_stat: number;
  jarque_bera_pvalue: number;
  ljung_box_stat: number;
  ljung_box_pvalue: number;
  breusch_pagan_stat: number;
  breusch_pagan_pvalue: number;
  white_test_stat: number;
  white_test_pvalue: number;
  condition_number: number;
  vif_values: Record<string, number>;
}

export interface TransformPreviewRequest {
  variable_name: string;
  data: number[];
  transformation: VariableTransformation;
}

export interface TransformPreviewResult {
  variable: string;
  original: number[];
  transformed: number[];
}

export interface TransformationTypes {
  pre_transforms: string[];
  post_transforms: string[];
  special_transforms: Record<string, any>;
  temporal: Record<string, string>;
}

// ============================================================================
// API Client
// ============================================================================

class ModellingClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Check if the modelling backend is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch("http://localhost:8000/health");
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Run regression with variable transformations
   */
  async runRegression(request: RegressionRequest): Promise<RegressionResult> {
    console.log('[ModellingClient] Sending regression request:', request);

    const response = await fetch(`${this.baseUrl}/regression`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const error = await response.json();
        console.error('[ModellingClient] Regression error:', error);
        errorMessage = error.detail || errorMessage;
      } catch (e) {
        console.error('[ModellingClient] Could not parse error response');
      }
      throw new Error(errorMessage);
    }

    const result = await response.json();
    console.log('[ModellingClient] Regression successful:', result);
    return result;
  }

  /**
   * Preview transformation on a single variable
   */
  async previewTransformation(
    request: TransformPreviewRequest
  ): Promise<TransformPreviewResult> {
    const response = await fetch(`${this.baseUrl}/transform-preview`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Transformation preview failed");
    }

    return response.json();
  }

  /**
   * Get available transformation types
   */
  async getTransformationTypes(): Promise<TransformationTypes> {
    const response = await fetch(`${this.baseUrl}/transformation-types`);

    if (!response.ok) {
      throw new Error("Failed to fetch transformation types");
    }

    return response.json();
  }
}

// Export singleton instance
export const modellingClient = new ModellingClient();

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Create default variable transformation
 */
export function createDefaultTransformation(
  variable: string
): VariableTransformation {
  return {
    variable,
    include: true,
    pre_transform: null,
    lag: 0,
    lead: 0,
    adstock: 0,
    dimret: 0,
    dimret_adstock: false,
    post_transform: null,
  };
}

/**
 * Convert data store format to API format
 */
export function convertDataForAPI(data: any[]): Record<string, any[]> {
  if (data.length === 0) return {};

  const result: Record<string, any[]> = {};
  const keys = Object.keys(data[0]);

  keys.forEach((key) => {
    result[key] = data.map((row) => row[key]);
  });

  return result;
}

/**
 * Format p-value for display
 */
export function formatPValue(pvalue: number): string {
  if (pvalue < 0.001) return "< 0.001 ***";
  if (pvalue < 0.01) return `${pvalue.toFixed(4)} **`;
  if (pvalue < 0.05) return `${pvalue.toFixed(4)} *`;
  return pvalue.toFixed(4);
}

/**
 * Format coefficient for display
 */
export function formatCoefficient(coef: number): string {
  if (Math.abs(coef) < 0.001) {
    return coef.toExponential(3);
  }
  return coef.toFixed(4);
}

/**
 * Get significance stars
 */
export function getSignificanceStars(pvalue: number): string {
  if (pvalue < 0.001) return "***";
  if (pvalue < 0.01) return "**";
  if (pvalue < 0.05) return "*";
  return "";
}
