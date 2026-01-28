/**
 * Date utility functions for consistent EST timezone handling across the application.
 * ALL dates must be displayed in Eastern Standard Time (EST/EDT).
 */

/**
 * Converts a UTC date string to EST and formats it for display.
 * @param dateString - ISO date string from the backend (UTC)
 * @param format - Format type: 'short' (Jan 1, 2024), 'long' (January 1, 2024), or 'full' (January 1, 2024 at 3:45 PM)
 * @returns Formatted date string in EST timezone
 */
export function formatDateEST(
  dateString: string | Date,
  format: 'short' | 'long' | 'full' = 'short'
): string {
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;

  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'America/New_York', // EST/EDT
    month: format === 'short' ? 'short' : 'long',
    day: 'numeric',
    year: 'numeric',
  };

  if (format === 'full') {
    options.hour = 'numeric';
    options.minute = '2-digit';
  }

  return date.toLocaleString('en-US', options);
}

/**
 * Converts a UTC date string to EST Date object.
 * Use this when you need a Date object in EST timezone.
 * @param dateString - ISO date string from the backend (UTC)
 * @returns Date object adjusted for EST
 */
export function toESTDate(dateString: string | Date): Date {
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;

  // Get the date string in EST timezone
  const estString = date.toLocaleString('en-US', {
    timeZone: 'America/New_York'
  });

  return new Date(estString);
}

/**
 * Gets the current date/time in EST timezone.
 * @returns Current Date object in EST
 */
export function nowEST(): Date {
  return toESTDate(new Date());
}

/**
 * Formats a date for file downloads (MM_DD_YYYY format in EST).
 * @param date - Optional date (defaults to now)
 * @returns Formatted date string for filenames
 */
export function formatDateForFilename(date?: Date | string): string {
  const d = date ? (typeof date === 'string' ? new Date(date) : date) : new Date();

  const estDate = toESTDate(d);
  const month = String(estDate.getMonth() + 1).padStart(2, '0');
  const day = String(estDate.getDate()).padStart(2, '0');
  const year = estDate.getFullYear();

  return `${month}_${day}_${year}`;
}
