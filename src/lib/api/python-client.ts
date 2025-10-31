/**
 * Python Backend Client
 * Communicates with FastAPI backend for Prophet and advanced stats
 */

// Helper to get the dynamic Python backend port from Electron
async function getPythonBackendUrl(): Promise<string> {
  // Check if we're in Electron environment
  if (typeof window !== 'undefined' && (window as any).electron) {
    try {
      const port = await (window as any).electron.invoke('python:getPort');
      return `http://localhost:${port}`;
    } catch (error) {
      console.warn('Failed to get Python port from Electron, using default:', error);
    }
  }

  // Fallback to environment variable or default
  return process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL || 'http://localhost:8000';
}

const PYTHON_BACKEND_URL = process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL || 'http://localhost:8000';

export interface ProphetForecastRequest {
  dates: string[];
  values: number[];
  periods?: number;
  yearly_seasonality?: boolean;
  weekly_seasonality?: boolean;
  daily_seasonality?: boolean;
}

export interface ProphetForecastResponse {
  forecast: {
    dates: string[];
    yhat: number[];
    yhat_lower: number[];
    yhat_upper: number[];
  };
  components: {
    dates: string[];
    trend: number[];
    yearly?: number[];
    weekly?: number[];
  };
  model_info: {
    changepoint_prior_scale: number;
    seasonality_prior_scale: number;
  };
}

export interface StepwiseRequest {
  y: number[];
  X: Record<string, number[]>;
  method?: 'forward' | 'backward' | 'both';
  significance_level?: number;
}

export interface StepwiseResponse {
  selected_variables: string[];
  coefficients: {
    intercept: number;
    variables: Record<string, number>;
  };
  r_squared: number;
  adjusted_r_squared: number;
  p_values: Record<string, number>;
  steps: Array<{
    step: number;
    action: 'add' | 'remove';
    variable: string;
    p_value: number;
  }>;
  n_samples: number;
  n_features_original: number;
  n_features_selected: number;
}

export interface CorrelationRequest {
  variables: Record<string, number[]>;
}

export interface CorrelationResponse {
  pearson: Record<string, Record<string, number>>;
  spearman: Record<string, Record<string, number>>;
  p_values: Record<string, Record<string, number>>;
  n_samples: number;
  variables: string[];
}

export interface CorrelationRankedRequest {
  target_variable: string;
  variables: Record<string, number[]>;
}

export interface CorrelationResult {
  variable: string;
  correlation: number;
  p_value: number;
  strength: string;
}

export interface CorrelationRankedResponse {
  target_variable: string;
  correlations: CorrelationResult[];
  n_samples: number;
}

export interface TransformationStep {
  type: string;
  amount: number;
}

export interface VariableTransformRequest {
  variable_name: string;
  data: number[];
  transformations: TransformationStep[];
}

export interface VariableTransformResponse {
  variable_name: string;
  transformed_data: (number | null)[];
  n_transformations: number;
}

class PythonBackendClient {
  private baseUrl: string;
  private dynamicUrl: Promise<string> | null = null;

  constructor(baseUrl: string = PYTHON_BACKEND_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Get the current backend URL (checks for dynamic port)
   */
  private async getBaseUrl(): Promise<string> {
    if (!this.dynamicUrl) {
      this.dynamicUrl = getPythonBackendUrl();
    }
    return this.dynamicUrl;
  }

  /**
   * Check if Python backend is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const baseUrl = await this.getBaseUrl();
      const response = await fetch(`${baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(2000), // 2 second timeout
      });
      return response.ok;
    } catch (error) {
      console.warn('Python backend not available:', error);
      return false;
    }
  }

  /**
   * Check backend availability with detailed error info
   */
  async checkAvailability(): Promise<{ available: boolean; error?: string; details?: any }> {
    try {
      const baseUrl = await this.getBaseUrl();
      const response = await fetch(`${baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000), // 3 second timeout
      });

      if (response.ok) {
        const health = await response.json();
        return { available: true, details: health };
      } else {
        return {
          available: false,
          error: `Backend returned status ${response.status}: ${response.statusText}`
        };
      }
    } catch (error) {
      let errorMessage = 'Unknown error';

      if (error instanceof Error) {
        if (error.name === 'AbortError' || error.message.includes('aborted')) {
          errorMessage = 'Connection timeout - backend did not respond within 3 seconds';
        } else if (error.message.includes('fetch')) {
          errorMessage = 'Cannot connect to Python backend (connection refused)';
        } else {
          errorMessage = error.message;
        }
      }

      return {
        available: false,
        error: errorMessage,
        details: error
      };
    }
  }

  /**
   * Get backend health status
   */
  async getHealth(): Promise<any> {
    const baseUrl = await this.getBaseUrl();
    const response = await fetch(`${baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Generate Prophet forecast
   */
  async prophetForecast(
    request: ProphetForecastRequest
  ): Promise<ProphetForecastResponse> {
    try {
      const baseUrl = await this.getBaseUrl();
      const response = await fetch(`${baseUrl}/api/prophet/forecast`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Prophet forecast failed');
      }

      return response.json();
    } catch (error) {
      console.error('Prophet forecast error:', error);
      throw error;
    }
  }

  /**
   * Perform stepwise regression
   */
  async stepwiseRegression(request: StepwiseRequest): Promise<StepwiseResponse> {
    try {
      const baseUrl = await this.getBaseUrl();
      const response = await fetch(`${baseUrl}/api/regression/stepwise`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Stepwise regression failed');
      }

      return response.json();
    } catch (error) {
      console.error('Stepwise regression error:', error);
      throw error;
    }
  }

  /**
   * Calculate advanced correlation matrix
   */
  async correlationMatrix(request: CorrelationRequest): Promise<CorrelationResponse> {
    try {
      const baseUrl = await this.getBaseUrl();
      const response = await fetch(`${baseUrl}/api/correlation/matrix`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Correlation analysis failed');
      }

      return response.json();
    } catch (error) {
      console.error('Correlation analysis error:', error);
      throw error;
    }
  }

  /**
   * Calculate ranked correlations for a target variable
   */
  async correlationRanked(request: CorrelationRankedRequest): Promise<CorrelationRankedResponse> {
    try {
      const baseUrl = await this.getBaseUrl();
      const response = await fetch(`${baseUrl}/api/correlation/ranked`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Ranked correlation analysis failed');
      }

      return response.json();
    } catch (error) {
      console.error('Ranked correlation analysis error:', error);
      throw error;
    }
  }

  /**
   * Transform a variable with multiple transformation steps
   */
  async transformVariable(request: VariableTransformRequest): Promise<VariableTransformResponse> {
    try {
      const baseUrl = await this.getBaseUrl();
      const response = await fetch(`${baseUrl}/api/transform/variable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Variable transformation failed');
      }

      return response.json();
    } catch (error) {
      console.error('Variable transformation error:', error);
      throw error;
    }
  }

  /**
   * Generic POST method for any endpoint
   */
  async post(endpoint: string, data: any): Promise<any> {
    try {
      const baseUrl = await this.getBaseUrl();
      const response = await fetch(`${baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Request failed: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error(`POST ${endpoint} error:`, error);
      throw error;
    }
  }
}

// Export singleton instance
export const pythonClient = new PythonBackendClient();

// Export class for custom instances
export { PythonBackendClient };
