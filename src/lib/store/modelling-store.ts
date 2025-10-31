import { create } from "zustand";
import {
  ModelConfiguration,
  VariableTransformation,
  RegressionResult,
  createDefaultTransformation,
} from "@/lib/api/modelling-client";

interface ModellingStore {
  // Model Configuration
  modelConfig: ModelConfiguration | null;
  setModelConfig: (config: ModelConfiguration) => void;

  // Variable Transformations
  variableTransformations: VariableTransformation[];
  setVariableTransformations: (transformations: VariableTransformation[]) => void;
  updateVariableTransformation: (variable: string, updates: Partial<VariableTransformation>) => void;
  initializeVariableTransformations: (variables: string[]) => void;

  // Regression Results
  regressionResults: RegressionResult | null;
  setRegressionResults: (results: RegressionResult | null) => void;

  // Regression Status
  regressionRunning: boolean;
  setRegressionRunning: (running: boolean) => void;
  regressionComplete: boolean;
  setRegressionComplete: (complete: boolean) => void;

  // Error State
  error: string | null;
  setError: (error: string | null) => void;

  // Reset functions
  resetModelConfig: () => void;
  resetAll: () => void;
}

export const useModellingStore = create<ModellingStore>((set, get) => ({
  // Initial state
  modelConfig: null,
  variableTransformations: [],
  regressionResults: null,
  regressionRunning: false,
  regressionComplete: false,
  error: null,

  // Model Configuration
  setModelConfig: (config) => set({ modelConfig: config }),

  // Variable Transformations
  setVariableTransformations: (transformations) =>
    set({ variableTransformations: transformations }),

  updateVariableTransformation: (variable, updates) => {
    const { variableTransformations } = get();
    const updated = variableTransformations.map((t) =>
      t.variable === variable ? { ...t, ...updates } : t
    );
    set({ variableTransformations: updated });
  },

  initializeVariableTransformations: (variables) => {
    const transformations = variables.map((v) => createDefaultTransformation(v));
    set({ variableTransformations: transformations });
  },

  // Regression Results
  setRegressionResults: (results) => set({ regressionResults: results }),

  // Regression Status
  setRegressionRunning: (running) => set({ regressionRunning: running }),
  setRegressionComplete: (complete) => set({ regressionComplete: complete }),

  // Error State
  setError: (error) => set({ error }),

  // Reset functions
  resetModelConfig: () => set({ modelConfig: null }),

  resetAll: () =>
    set({
      modelConfig: null,
      variableTransformations: [],
      regressionResults: null,
      regressionRunning: false,
      regressionComplete: false,
      error: null,
    }),
}));
