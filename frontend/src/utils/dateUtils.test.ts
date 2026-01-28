/**
 * Example test file for dateUtils.
 *
 * This demonstrates how to write unit tests for utility functions.
 * Run tests with: npm test
 */

import { describe, it, expect } from 'vitest';
import { formatDateEST, formatDateForFilename, toESTDate, nowEST } from './dateUtils';

describe('dateUtils', () => {
  describe('formatDateEST', () => {
    it('should format a date string in short format', () => {
      const date = '2024-01-15T12:00:00Z'; // UTC
      const result = formatDateEST(date, 'short');

      // Should be in EST (5 hours behind UTC, so 7 AM EST)
      expect(result).toContain('Jan');
      expect(result).toContain('15');
      expect(result).toContain('2024');
    });

    it('should format a Date object in long format', () => {
      const date = new Date('2024-01-15T12:00:00Z');
      const result = formatDateEST(date, 'long');

      expect(result).toContain('January');
      expect(result).toContain('15');
      expect(result).toContain('2024');
    });

    it('should include time in full format', () => {
      const date = '2024-01-15T17:30:00Z'; // 12:30 PM EST
      const result = formatDateEST(date, 'full');

      expect(result).toContain('January');
      expect(result).toContain('15');
      expect(result).toContain('2024');
      // Should include time
      expect(result).toMatch(/\d{1,2}:\d{2}\s*(AM|PM)/i);
    });
  });

  describe('formatDateForFilename', () => {
    it('should format date as MM_DD_YYYY', () => {
      const date = new Date('2024-01-15T12:00:00Z');
      const result = formatDateForFilename(date);

      // Result should be in EST, so might be 01_15_2024 or 01_14_2024 depending on timezone
      expect(result).toMatch(/^\d{2}_\d{2}_\d{4}$/);
    });

    it('should use current date when no argument provided', () => {
      const result = formatDateForFilename();

      expect(result).toMatch(/^\d{2}_\d{2}_\d{4}$/);
    });
  });

  describe('toESTDate', () => {
    it('should convert UTC date to EST Date object', () => {
      const utcDate = '2024-01-15T17:00:00Z'; // 5 PM UTC = 12 PM EST
      const result = toESTDate(utcDate);

      expect(result).toBeInstanceOf(Date);
      // The result should be a valid date
      expect(result.getTime()).toBeGreaterThan(0);
    });

    it('should handle Date objects', () => {
      const date = new Date('2024-01-15T17:00:00Z');
      const result = toESTDate(date);

      expect(result).toBeInstanceOf(Date);
    });
  });

  describe('nowEST', () => {
    it('should return current date in EST', () => {
      const result = nowEST();

      expect(result).toBeInstanceOf(Date);
      // Should be close to current time (within 1 second)
      const now = new Date();
      const diff = Math.abs(result.getTime() - now.getTime());
      expect(diff).toBeLessThan(1000);
    });
  });
});
