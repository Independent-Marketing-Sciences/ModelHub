import { useMemo } from "react";
import { useDataStore, DataRow } from "@/lib/store/index";

/**
 * Hook to get data filtered by the global date range
 *
 * @returns Filtered data based on the current date range selection
 */
export function useFilteredData(): DataRow[] {
  const { data, dateColumn, dateRangeStart, dateRangeEnd } = useDataStore();

  const filteredData = useMemo(() => {
    // If no date range is set, return all data
    if (!dateRangeStart || !dateRangeEnd) {
      return data;
    }

    // Filter data by date range
    return data.filter((row) => {
      const dateValue = row[dateColumn];

      if (!dateValue) {
        return false;
      }

      const dateStr = String(dateValue);

      // Simple string comparison works if dates are in sortable format
      // (e.g., "2024-01-01", "01/01/2024", etc.)
      return dateStr >= dateRangeStart && dateStr <= dateRangeEnd;
    });
  }, [data, dateColumn, dateRangeStart, dateRangeEnd]);

  return filteredData;
}

/**
 * Hook to check if date filtering is active
 */
export function useDateFilterActive(): boolean {
  const { dateRangeStart, dateRangeEnd } = useDataStore();
  return !!(dateRangeStart && dateRangeEnd);
}
