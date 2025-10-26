import { create } from "zustand";

export interface DataRow {
  [key: string]: string | number;
}

export interface NamingConventionRow {
  [key: string]: string;
}

interface DataStore {
  // Main dataset
  data: DataRow[];
  setData: (data: DataRow[]) => void;

  // Naming convention data
  namingConvention: NamingConventionRow[];
  setNamingConvention: (data: NamingConventionRow[]) => void;

  // Available columns
  columns: string[];
  setColumns: (columns: string[]) => void;

  // Date column name (typically "Date" or "OBS")
  dateColumn: string;
  setDateColumn: (column: string) => void;

  // Global date range filter
  dateRangeStart: string | null;
  dateRangeEnd: string | null;
  setDateRange: (start: string | null, end: string | null) => void;
  clearDateRange: () => void;

  // Computed filtered data based on date range
  getFilteredData: () => DataRow[];

  // Loading states
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  error: string | null;
  setError: (error: string | null) => void;
}

export const useDataStore = create<DataStore>((set, get) => ({
  data: [],
  setData: (data) => set({ data }),

  namingConvention: [],
  setNamingConvention: (data) => set({ namingConvention: data }),

  columns: [],
  setColumns: (columns) => set({ columns }),

  dateColumn: "",
  setDateColumn: (column) => set({ dateColumn: column }),

  dateRangeStart: null,
  dateRangeEnd: null,
  setDateRange: (start, end) => set({ dateRangeStart: start, dateRangeEnd: end }),
  clearDateRange: () => set({ dateRangeStart: null, dateRangeEnd: null }),

  // Computed filtered data based on date range
  getFilteredData: () => {
    const state = get();
    const { data, dateColumn, dateRangeStart, dateRangeEnd } = state;

    console.log('[Store] getFilteredData called', {
      dataLength: data.length,
      dateColumn,
      dateRangeStart,
      dateRangeEnd
    });

    // If no date range is set, return all data
    if (!dateRangeStart || !dateRangeEnd || !dateColumn) {
      console.log('[Store] No filter active, returning all data');
      return data;
    }

    // Parse the filter dates
    const filterStart = new Date(dateRangeStart);
    const filterEnd = new Date(dateRangeEnd);

    console.log('[Store] Filter dates:', { filterStart, filterEnd });

    // Filter data by date range
    const filtered = data.filter((row) => {
      const dateValue = row[dateColumn];
      if (!dateValue) return false;

      // Parse the date from the row
      let rowDate: Date;

      // Try different date parsing strategies
      const dateStr = String(dateValue).trim();

      // Try ISO format (YYYY-MM-DD)
      if (/^\d{4}-\d{2}-\d{2}/.test(dateStr)) {
        rowDate = new Date(dateStr);
      }
      // Try MM/DD/YYYY or DD/MM/YYYY
      else if (/^\d{1,2}\/\d{1,2}\/\d{4}/.test(dateStr)) {
        rowDate = new Date(dateStr);
      }
      // Try other common formats
      else {
        rowDate = new Date(dateStr);
      }

      // Check if date is valid
      if (isNaN(rowDate.getTime())) {
        console.warn('[Store] Invalid date:', dateValue);
        return false;
      }

      // Normalize to start of day for comparison
      const rowDateStart = new Date(rowDate.getFullYear(), rowDate.getMonth(), rowDate.getDate());
      const filterStartNorm = new Date(filterStart.getFullYear(), filterStart.getMonth(), filterStart.getDate());
      const filterEndNorm = new Date(filterEnd.getFullYear(), filterEnd.getMonth(), filterEnd.getDate());

      return rowDateStart >= filterStartNorm && rowDateStart <= filterEndNorm;
    });

    console.log('[Store] Filtered data:', { originalLength: data.length, filteredLength: filtered.length });
    return filtered;
  },

  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),

  error: null,
  setError: (error) => set({ error }),
}));
