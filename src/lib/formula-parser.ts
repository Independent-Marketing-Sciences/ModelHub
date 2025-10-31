/**
 * Formula Parser for Variable Transformations
 * Parses expressions like: adstock(kpi, 0.5), log(dimret_adstock(var, 0.3, 0.4))
 */

import { VariableTransformation } from "./api/modelling-client";

export interface ParsedFormula {
  variable: string;
  transformations: {
    type: string;
    params: any[];
  }[];
}

/**
 * Parse a transformation formula string into structured transformation
 * Examples:
 * - "sales" → no transformation
 * - "log(sales)" → pre_transform: log
 * - "adstock(sales, 0.5)" → adstock: 0.5
 * - "lag(sales, 2)" → lag: 2
 * - "log(adstock(sales, 0.5))" → pre_transform: log, adstock: 0.5
 * - "dimret_adstock(sales, 0.3, 0.4)" → dimret_adstock: true, adstock: 0.3, dimret: 0.4
 */
export function parseFormula(formula: string): VariableTransformation | null {
  if (!formula || formula.trim() === "") {
    return null;
  }

  formula = formula.trim();

  // Extract the base variable name (innermost variable)
  const variableMatch = formula.match(/\b([a-z_][a-z0-9_\.]*)\b/i);
  if (!variableMatch) {
    return null;
  }

  const variable = variableMatch[1];

  // Initialize transformation object
  const transformation: VariableTransformation = {
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

  // Parse transformations from inside-out
  let currentFormula = formula;

  // Check for lag/lead
  const lagMatch = currentFormula.match(/lag\([^,]+,\s*(\d+)\)/);
  if (lagMatch) {
    transformation.lag = parseInt(lagMatch[1]);
    currentFormula = currentFormula.replace(lagMatch[0], variable);
  }

  const leadMatch = currentFormula.match(/lead\([^,]+,\s*(\d+)\)/);
  if (leadMatch) {
    transformation.lead = parseInt(leadMatch[1]);
    currentFormula = currentFormula.replace(leadMatch[0], variable);
  }

  // Check for adstock
  const adstockMatch = currentFormula.match(/adstock\([^,]+,\s*([\d.]+)\)/);
  if (adstockMatch) {
    transformation.adstock = parseFloat(adstockMatch[1]);
    currentFormula = currentFormula.replace(adstockMatch[0], variable);
  }

  const nAdstockMatch = currentFormula.match(/n_adstock\([^,]+,\s*([\d.]+)\)/);
  if (nAdstockMatch) {
    transformation.adstock = parseFloat(nAdstockMatch[1]);
    currentFormula = currentFormula.replace(nAdstockMatch[0], variable);
  }

  // Check for dimret
  const dimretMatch = currentFormula.match(/dimret\([^,]+,\s*([\d.]+)\)/);
  if (dimretMatch) {
    transformation.dimret = parseFloat(dimretMatch[1]);
    currentFormula = currentFormula.replace(dimretMatch[0], variable);
  }

  const nDimretMatch = currentFormula.match(/n_dimret\([^,]+,\s*([\d.]+)\)/);
  if (nDimretMatch) {
    transformation.dimret = parseFloat(nDimretMatch[1]);
    currentFormula = currentFormula.replace(nDimretMatch[0], variable);
  }

  // Check for combined dimret_adstock
  const dimretAdstockMatch = currentFormula.match(/dimret_adstock\([^,]+,\s*([\d.]+),\s*([\d.]+)\)/);
  if (dimretAdstockMatch) {
    transformation.dimret_adstock = true;
    transformation.adstock = parseFloat(dimretAdstockMatch[1]);
    transformation.dimret = parseFloat(dimretAdstockMatch[2]);
    currentFormula = currentFormula.replace(dimretAdstockMatch[0], variable);
  }

  const nDimretAdstockMatch = currentFormula.match(/n_dimret_adstock\([^,]+,\s*([\d.]+),\s*([\d.]+)\)/);
  if (nDimretAdstockMatch) {
    transformation.dimret_adstock = true;
    transformation.adstock = parseFloat(nDimretAdstockMatch[1]);
    transformation.dimret = parseFloat(nDimretAdstockMatch[2]);
    currentFormula = currentFormula.replace(nDimretAdstockMatch[0], variable);
  }

  // Check for pre-transform (outermost function)
  const preTransforms = ["log", "sqrt", "exp"];
  for (const transform of preTransforms) {
    const regex = new RegExp(`^${transform}\\(`);
    if (regex.test(currentFormula)) {
      transformation.pre_transform = transform;
      break;
    }
  }

  return transformation;
}

/**
 * Convert transformation object back to formula string
 */
export function transformationToFormula(transformation: VariableTransformation): string {
  let formula = transformation.variable;

  // Apply lag/lead first
  if (transformation.lag > 0) {
    formula = `lag(${formula}, ${transformation.lag})`;
  } else if (transformation.lead > 0) {
    formula = `lead(${formula}, ${transformation.lead})`;
  }

  // Apply adstock/dimret
  if (transformation.dimret_adstock) {
    formula = `dimret_adstock(${formula}, ${transformation.adstock}, ${transformation.dimret})`;
  } else {
    if (transformation.adstock > 0) {
      formula = `adstock(${formula}, ${transformation.adstock})`;
    }
    if (transformation.dimret > 0) {
      formula = `dimret(${formula}, ${transformation.dimret})`;
    }
  }

  // Apply pre-transform (outermost)
  if (transformation.pre_transform) {
    formula = `${transformation.pre_transform}(${formula})`;
  }

  return formula;
}

/**
 * Validate a formula string
 */
export function validateFormula(formula: string, availableVariables: string[]): { valid: boolean; error?: string } {
  if (!formula || formula.trim() === "") {
    return { valid: false, error: "Formula cannot be empty" };
  }

  // Extract variable name
  const variableMatch = formula.match(/\b([a-z_][a-z0-9_\.]*)\b/i);
  if (!variableMatch) {
    return { valid: false, error: "No variable found in formula" };
  }

  const variable = variableMatch[1];
  if (!availableVariables.includes(variable)) {
    return { valid: false, error: `Variable '${variable}' not found in dataset` };
  }

  // Check for balanced parentheses
  let depth = 0;
  for (const char of formula) {
    if (char === "(") depth++;
    if (char === ")") depth--;
    if (depth < 0) {
      return { valid: false, error: "Unbalanced parentheses" };
    }
  }
  if (depth !== 0) {
    return { valid: false, error: "Unbalanced parentheses" };
  }

  // Check for valid function names
  const validFunctions = ["log", "sqrt", "exp", "lag", "lead", "adstock", "n_adstock", "dimret", "n_dimret", "dimret_adstock", "n_dimret_adstock"];
  const functionMatches = formula.match(/\b([a-z_]+)\(/gi);
  if (functionMatches) {
    for (const match of functionMatches) {
      const funcName = match.slice(0, -1).toLowerCase();
      if (!validFunctions.includes(funcName)) {
        return { valid: false, error: `Unknown function '${funcName}'` };
      }
    }
  }

  return { valid: true };
}

/**
 * Get formula examples
 */
export function getFormulaExamples(): string[] {
  return [
    "sales",
    "log(sales)",
    "adstock(tv_spend, 0.5)",
    "lag(temperature, 1)",
    "dimret(marketing, 0.3)",
    "dimret_adstock(tv_spend, 0.4, 0.2)",
    "log(adstock(sales, 0.6))",
    "sqrt(dimret(impressions, 0.25))",
  ];
}
