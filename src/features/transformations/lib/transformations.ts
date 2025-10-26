/**
 * Data transformation utilities
 * Replicates the transformation logic from the Dash app
 */

export type TransformationType =
  | "log"
  | "lag_lead"
  | "adstock"
  | "diminishing_returns_absolute"
  | "diminishing_returns_exponential"
  | "moving_average";

export interface Transformation {
  type: TransformationType;
  amount: number;
}

/**
 * Apply log transformation: log(x + amount)
 */
export function applyLog(data: number[], amount: number): number[] {
  return data.map((x) => Math.log(x + amount));
}

/**
 * Apply lag or lead transformation
 * Positive amount = lag (shift forward), negative = lead (shift backward)
 */
export function applyLagLead(data: number[], periods: number): number[] {
  if (periods === 0) return [...data];

  const result = new Array(data.length).fill(NaN);

  if (periods > 0) {
    // Lag: shift forward
    for (let i = periods; i < data.length; i++) {
      result[i] = data[i - periods];
    }
  } else {
    // Lead: shift backward
    const absPeriods = Math.abs(periods);
    for (let i = 0; i < data.length - absPeriods; i++) {
      result[i] = data[i + absPeriods];
    }
  }

  return result;
}

/**
 * Apply adstock transformation with decay rate
 * x[i] = x[i] + decay * x[i-1]
 */
export function applyAdstock(data: number[], decayRate: number): number[] {
  const result = [...data];

  for (let i = 1; i < result.length; i++) {
    result[i] = result[i] + decayRate * result[i - 1];
  }

  return result;
}

/**
 * Apply diminishing returns (absolute)
 * Formula: x / (x + saturation_point)
 */
export function applyDiminishingReturnsAbsolute(
  data: number[],
  saturationPoint: number
): number[] {
  return data.map((x) => x / (x + Math.abs(saturationPoint)));
}

/**
 * Apply diminishing returns (exponential) - Hill curve
 * Formula: 1 - exp(-slope * x)
 */
export function applyDiminishingReturnsExponential(
  data: number[],
  slope: number
): number[] {
  return data.map((x) => 1 - Math.exp(-slope * x));
}

/**
 * Apply simple moving average
 */
export function applyMovingAverage(data: number[], windowSize: number): number[] {
  const result = new Array(data.length).fill(NaN);
  const window = Math.floor(windowSize);

  if (window < 1) return result;

  for (let i = window - 1; i < data.length; i++) {
    let sum = 0;
    for (let j = 0; j < window; j++) {
      sum += data[i - j];
    }
    result[i] = sum / window;
  }

  return result;
}

/**
 * Apply a transformation based on type
 */
export function applyTransformation(
  data: number[],
  transformation: Transformation
): number[] {
  switch (transformation.type) {
    case "log":
      return applyLog(data, transformation.amount);
    case "lag_lead":
      return applyLagLead(data, Math.floor(transformation.amount));
    case "adstock":
      return applyAdstock(data, transformation.amount);
    case "diminishing_returns_absolute":
      return applyDiminishingReturnsAbsolute(data, transformation.amount);
    case "diminishing_returns_exponential":
      return applyDiminishingReturnsExponential(data, transformation.amount);
    case "moving_average":
      return applyMovingAverage(data, transformation.amount);
    default:
      return data;
  }
}

/**
 * Apply multiple transformations in sequence
 */
export function applyTransformations(
  data: number[],
  transformations: Transformation[]
): number[] {
  let result = [...data];

  for (const transformation of transformations) {
    result = applyTransformation(result, transformation);
  }

  return result;
}

/**
 * Calculate Pearson correlation coefficient
 */
export function calculateCorrelation(x: number[], y: number[]): number {
  const n = Math.min(x.length, y.length);

  // Filter out NaN values
  const validPairs: [number, number][] = [];
  for (let i = 0; i < n; i++) {
    if (!isNaN(x[i]) && !isNaN(y[i])) {
      validPairs.push([x[i], y[i]]);
    }
  }

  if (validPairs.length < 2) return NaN;

  const xValues = validPairs.map(p => p[0]);
  const yValues = validPairs.map(p => p[1]);

  const xMean = xValues.reduce((a, b) => a + b, 0) / xValues.length;
  const yMean = yValues.reduce((a, b) => a + b, 0) / yValues.length;

  let numerator = 0;
  let xDenominator = 0;
  let yDenominator = 0;

  for (let i = 0; i < xValues.length; i++) {
    const xDiff = xValues[i] - xMean;
    const yDiff = yValues[i] - yMean;

    numerator += xDiff * yDiff;
    xDenominator += xDiff * xDiff;
    yDenominator += yDiff * yDiff;
  }

  const denominator = Math.sqrt(xDenominator * yDenominator);

  if (denominator === 0) return NaN;

  return numerator / denominator;
}

/**
 * Calculate correlation matrix for multiple variables
 */
export function calculateCorrelationMatrix(
  variables: { name: string; data: number[] }[]
): { [key: string]: { [key: string]: number } } {
  const matrix: { [key: string]: { [key: string]: number } } = {};

  for (const var1 of variables) {
    matrix[var1.name] = {};
    for (const var2 of variables) {
      matrix[var1.name][var2.name] = calculateCorrelation(var1.data, var2.data);
    }
  }

  return matrix;
}
