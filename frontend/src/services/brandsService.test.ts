/**
 * Example test file for brandsService.
 *
 * This demonstrates how to test API service functions with mocked axios.
 * Run tests with: npm test
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { brandsService } from './brandsService';
import { api } from './api';

// Mock the api module
vi.mock('./api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('brandsService', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('should fetch all brands', async () => {
      const mockBrands = [
        { id: 1, user_id: 1, brand_name: 'Brand A', created_at: '2024-01-01', is_active: true },
        { id: 2, user_id: 1, brand_name: 'Brand B', created_at: '2024-01-02', is_active: false },
      ];

      // Mock the API response
      vi.mocked(api.get).mockResolvedValue({ data: mockBrands });

      // Call the service
      const result = await brandsService.list();

      // Verify the correct endpoint was called
      expect(api.get).toHaveBeenCalledWith('/brands');

      // Verify the result
      expect(result).toEqual(mockBrands);
      expect(result).toHaveLength(2);
      expect(result[0].brand_name).toBe('Brand A');
    });
  });

  describe('get', () => {
    it('should fetch a specific brand by ID', async () => {
      const mockBrand = {
        id: 1,
        user_id: 1,
        brand_name: 'Test Brand',
        created_at: '2024-01-01',
        is_active: true,
      };

      vi.mocked(api.get).mockResolvedValue({ data: mockBrand });

      const result = await brandsService.get(1);

      expect(api.get).toHaveBeenCalledWith('/brands/1');
      expect(result).toEqual(mockBrand);
      expect(result.brand_name).toBe('Test Brand');
    });
  });

  describe('create', () => {
    it('should create a new brand', async () => {
      const newBrand = { brand_name: 'New Brand', industry: 'Tech' };
      const createdBrand = {
        id: 3,
        user_id: 1,
        brand_name: 'New Brand',
        industry: 'Tech',
        created_at: '2024-01-03',
        is_active: true,
      };

      vi.mocked(api.post).mockResolvedValue({ data: createdBrand });

      const result = await brandsService.create(newBrand);

      expect(api.post).toHaveBeenCalledWith('/brands', newBrand);
      expect(result).toEqual(createdBrand);
      expect(result.id).toBe(3);
    });
  });

  describe('update', () => {
    it('should update an existing brand', async () => {
      const updateData = { brand_name: 'Updated Brand Name' };
      const updatedBrand = {
        id: 1,
        user_id: 1,
        brand_name: 'Updated Brand Name',
        created_at: '2024-01-01',
        is_active: true,
      };

      vi.mocked(api.put).mockResolvedValue({ data: updatedBrand });

      const result = await brandsService.update(1, updateData);

      expect(api.put).toHaveBeenCalledWith('/brands/1', updateData);
      expect(result.brand_name).toBe('Updated Brand Name');
    });
  });

  describe('delete', () => {
    it('should delete a brand', async () => {
      vi.mocked(api.delete).mockResolvedValue({ data: null });

      await brandsService.delete(1);

      expect(api.delete).toHaveBeenCalledWith('/brands/1');
    });
  });

  describe('setActive', () => {
    it('should set a brand as active', async () => {
      const activeBrand = {
        id: 1,
        user_id: 1,
        brand_name: 'Active Brand',
        created_at: '2024-01-01',
        is_active: true,
      };

      vi.mocked(api.post).mockResolvedValue({ data: activeBrand });

      const result = await brandsService.setActive(1);

      expect(api.post).toHaveBeenCalledWith('/brands/1/set-active');
      expect(result.is_active).toBe(true);
    });
  });

  describe('share', () => {
    it('should share a brand with another user', async () => {
      const shareRequest = { email: 'user@example.com' };
      const shareResponse = {
        id: 1,
        brand_id: 1,
        shared_with_user_id: 2,
        shared_by_user_id: 1,
        created_at: '2024-01-03',
        shared_with_email: 'user@example.com',
      };

      vi.mocked(api.post).mockResolvedValue({ data: shareResponse });

      const result = await brandsService.share(1, shareRequest);

      expect(api.post).toHaveBeenCalledWith('/brands/1/share', shareRequest);
      expect(result.shared_with_email).toBe('user@example.com');
    });
  });
});
