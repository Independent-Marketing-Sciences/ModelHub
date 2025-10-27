"use client";

import { useEffect, useMemo, useState } from "react";
import { useDataStore } from "@/lib/store/index";
import { Button } from "@/components/ui/button";
import { Calendar, X } from "lucide-react";
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs, { Dayjs } from 'dayjs';

export function DateRangeSelector() {
  const { data, dateColumn, dateRangeStart, dateRangeEnd, setDateRange, clearDateRange, columns, setDateColumn } = useDataStore();
  const [startDate, setStartDate] = useState<Dayjs | null>(null);
  const [endDate, setEndDate] = useState<Dayjs | null>(null);

  // Auto-detect date column if not set
  const detectedDateColumn = useMemo(() => {
    if (dateColumn && data.length > 0 && dateColumn in data[0]) {
      return dateColumn;
    }

    if (!data.length || !columns.length) {
      return "";
    }

    // Try to find date column from common names
    const dateColumnNames = ['OBS', 'obs', 'Date', 'date', 'DATE', 'Observation', 'observation'];
    for (const name of dateColumnNames) {
      const found = columns.find(col => col.toLowerCase() === name.toLowerCase());
      if (found && found in data[0]) {
        console.log('[DateRangeSelector] Auto-detected date column:', found);
        return found;
      }
    }

    // Check if any column contains 'date' or 'obs'
    const containsDate = columns.find(col =>
      (col.toLowerCase().includes('date') || col.toLowerCase().includes('obs')) &&
      col in data[0]
    );
    if (containsDate) {
      console.log('[DateRangeSelector] Auto-detected date column (contains):', containsDate);
      return containsDate;
    }

    console.warn('[DateRangeSelector] No date column found');
    return "";
  }, [data, dateColumn, columns]);

  // Update store when detected column changes (separate from render)
  useEffect(() => {
    if (detectedDateColumn && detectedDateColumn !== dateColumn) {
      console.log('[DateRangeSelector] Updating store with detected date column:', detectedDateColumn);
      setDateColumn(detectedDateColumn);
    }
  }, [detectedDateColumn, dateColumn, setDateColumn]);

  // Get unique dates from the date column, sorted
  const availableDates = useMemo(() => {
    console.log('[DateRangeSelector] Computing available dates', {
      dataLength: data.length,
      dateColumn: detectedDateColumn,
      columns: columns.length
    });

    if (!data.length) {
      console.log('[DateRangeSelector] No data loaded');
      return [];
    }

    if (!detectedDateColumn) {
      console.log('[DateRangeSelector] No date column detected');
      return [];
    }

    const dates = data
      .map((row) => row[detectedDateColumn])
      .filter((date) => date != null && date !== "")
      .map((date) => String(date));

    // Remove duplicates and sort
    const uniqueDates = Array.from(new Set(dates)).sort();
    console.log('[DateRangeSelector] Found unique dates:', uniqueDates.length, 'First few:', uniqueDates.slice(0, 5));
    return uniqueDates;
  }, [data, detectedDateColumn]);

  // Sync local state with store
  useEffect(() => {
    setStartDate(dateRangeStart ? dayjs(dateRangeStart) : null);
    setEndDate(dateRangeEnd ? dayjs(dateRangeEnd) : null);
  }, [dateRangeStart, dateRangeEnd]);

  const handleApply = () => {
    if (startDate && endDate) {
      setDateRange(startDate.format('YYYY-MM-DD'), endDate.format('YYYY-MM-DD'));
    }
  };

  const handleClear = () => {
    setStartDate(null);
    setEndDate(null);
    clearDateRange();
  };

  const isActive = dateRangeStart && dateRangeEnd;

  // Show a placeholder message if no data is loaded yet
  if (!availableDates.length) {
    console.log('[DateRangeSelector] Rendering placeholder - no available dates');
    return (
      <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
        <Calendar className="h-4 w-4 text-amber-600 dark:text-amber-400" />
        <div className="flex-1">
          <span className="text-sm text-amber-800 dark:text-amber-300 font-medium block">
            Date range filter unavailable
          </span>
          <span className="text-xs text-amber-600 dark:text-amber-400">
            {!data.length
              ? 'No data loaded'
              : !detectedDateColumn
              ? `No date column found. Available columns: ${columns.join(', ')}`
              : `No dates in column "${detectedDateColumn}"`}
          </span>
        </div>
      </div>
    );
  }

  console.log('[DateRangeSelector] Rendering full date selector');

  // Get min and max dates - allow selection from 2000 onwards
  const minDate = dayjs('2000-01-01');
  const maxDate = availableDates.length > 0 ? dayjs(availableDates[availableDates.length - 1]) : dayjs();

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <div className="space-y-3">
        <DatePicker
          label="Start Date"
          value={startDate}
          onChange={(newValue) => setStartDate(newValue)}
          minDate={minDate}
          maxDate={maxDate}
          format="DD/MM/YYYY"
          slotProps={{
            textField: {
              size: 'small',
              fullWidth: true,
              InputProps: {
                style: {
                  color: '#ffffff',
                  backgroundColor: 'hsl(215, 20%, 20%)'
                }
              },
              inputProps: {
                style: {
                  color: '#ffffff',
                  WebkitTextFillColor: '#ffffff'
                }
              },
              sx: {
                '& .MuiInputBase-root': {
                  color: '#ffffff !important',
                  backgroundColor: 'hsl(215, 20%, 20%)',
                },
                '& .MuiInputBase-input': {
                  color: '#ffffff !important',
                  WebkitTextFillColor: '#ffffff !important',
                  '&::placeholder': {
                    color: '#ffffff !important',
                    opacity: '0.7 !important',
                    WebkitTextFillColor: '#ffffff !important',
                  },
                  '&::-webkit-input-placeholder': {
                    color: '#ffffff !important',
                    opacity: '0.7 !important',
                    WebkitTextFillColor: '#ffffff !important',
                  },
                  '&::-moz-placeholder': {
                    color: '#ffffff !important',
                    opacity: '0.7 !important',
                  },
                },
                '& .MuiInputLabel-root': {
                  color: 'hsl(214, 17%, 62%)',
                },
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'hsl(215, 25%, 35%)',
                },
                '& .MuiSvgIcon-root': {
                  color: '#ffffff',
                }
              }
            }
          }}
        />

        <DatePicker
          label="End Date"
          value={endDate}
          onChange={(newValue) => setEndDate(newValue)}
          minDate={startDate || minDate}
          maxDate={maxDate}
          format="DD/MM/YYYY"
          slotProps={{
            textField: {
              size: 'small',
              fullWidth: true,
              InputProps: {
                style: {
                  color: '#ffffff',
                  backgroundColor: 'hsl(215, 20%, 20%)'
                }
              },
              inputProps: {
                style: {
                  color: '#ffffff',
                  WebkitTextFillColor: '#ffffff'
                }
              },
              sx: {
                '& .MuiInputBase-root': {
                  color: '#ffffff !important',
                  backgroundColor: 'hsl(215, 20%, 20%)',
                },
                '& .MuiInputBase-input': {
                  color: '#ffffff !important',
                  WebkitTextFillColor: '#ffffff !important',
                  '&::placeholder': {
                    color: '#ffffff !important',
                    opacity: '0.7 !important',
                    WebkitTextFillColor: '#ffffff !important',
                  },
                  '&::-webkit-input-placeholder': {
                    color: '#ffffff !important',
                    opacity: '0.7 !important',
                    WebkitTextFillColor: '#ffffff !important',
                  },
                  '&::-moz-placeholder': {
                    color: '#ffffff !important',
                    opacity: '0.7 !important',
                  },
                },
                '& .MuiInputLabel-root': {
                  color: 'hsl(214, 17%, 62%)',
                },
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'hsl(215, 25%, 35%)',
                },
                '& .MuiSvgIcon-root': {
                  color: '#ffffff',
                }
              }
            }
          }}
        />

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={handleApply}
            disabled={!startDate || !endDate}
            className="flex-1"
          >
            Apply
          </Button>

          {isActive && (
            <Button
              size="sm"
              variant="ghost"
              onClick={handleClear}
              className="flex-1"
            >
              <X className="h-4 w-4 mr-1" />
              Clear
            </Button>
          )}
        </div>

        {isActive && (
          <div className="text-xs text-muted-foreground bg-muted/30 p-2 rounded border border-border">
            <span className="font-medium">Active:</span> {dateRangeStart} to {dateRangeEnd}
          </div>
        )}
      </div>
    </LocalizationProvider>
  );
}
