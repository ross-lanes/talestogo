/**
 * Typed API Service for Brand operations.
 *
 * This is a TEMPLATE for how to create typed API services.
 * Benefits:
 * - Full TypeScript type safety
 * - Centralized API endpoint management
 * - Easier testing and mocking
 * - Auto-complete in IDEs
 *
 * MIGRATION STRATEGY:
 * 1. Use this service in NEW code
 * 2. Gradually migrate existing inline api.get/post/put/delete calls
 * 3. Do NOT migrate everything at once (high risk of regressions)
 *
 * PATTERN TO FOLLOW:
 * - Each resource gets its own service file (e.g., competitorsService.ts, descriptorsService.ts)
 * - All endpoints for that resource are in one place
 * - Use TypeScript types from @/types for request/response
 * - Export a single object with all CRUD methods
 */

import { api } from './api';

// ==================== TYPES ====================

export interface Brand {
  id: number;
  user_id: number;
  brand_name: string;
  industry?: string;
  created_at: string;
  is_active: boolean;
}

export interface BrandCreate {
  brand_name: string;
  industry?: string;
}

export interface BrandUpdate {
  brand_name?: string;
  industry?: string;
  is_active?: boolean;
}

export interface BrandShare {
  id: number;
  brand_id: number;
  shared_with_user_id: number;
  shared_by_user_id: number;
  created_at: string;
  shared_with_email?: string;
  shared_by_email?: string;
}

export interface ShareBrandRequest {
  email: string;
}

// ==================== SERVICE ====================

/**
 * Brand API Service
 *
 * All brand-related API calls centralized in one place.
 */
export const brandsService = {
  /**
   * Get all brands for the current user (owned + shared)
   */
  list: async (): Promise<Brand[]> => {
    const response = await api.get<Brand[]>('/brands');
    return response.data;
  },

  /**
   * Get a specific brand by ID
   */
  get: async (brandId: number): Promise<Brand> => {
    const response = await api.get<Brand>(`/brands/${brandId}`);
    return response.data;
  },

  /**
   * Create a new brand
   */
  create: async (data: BrandCreate): Promise<Brand> => {
    const response = await api.post<Brand>('/brands', data);
    return response.data;
  },

  /**
   * Update an existing brand
   */
  update: async (brandId: number, data: BrandUpdate): Promise<Brand> => {
    const response = await api.put<Brand>(`/brands/${brandId}`, data);
    return response.data;
  },

  /**
   * Delete a brand
   */
  delete: async (brandId: number): Promise<void> => {
    await api.delete(`/brands/${brandId}`);
  },

  /**
   * Set a brand as active for the current user
   */
  setActive: async (brandId: number): Promise<Brand> => {
    const response = await api.post<Brand>(`/brands/${brandId}/set-active`);
    return response.data;
  },

  /**
   * Get all users a brand is shared with
   */
  listShares: async (brandId: number): Promise<BrandShare[]> => {
    const response = await api.get<BrandShare[]>(`/brands/${brandId}/shares`);
    return response.data;
  },

  /**
   * Share a brand with another user by email
   */
  share: async (brandId: number, data: ShareBrandRequest): Promise<BrandShare> => {
    const response = await api.post<BrandShare>(`/brands/${brandId}/share`, data);
    return response.data;
  },

  /**
   * Remove a brand share (unshare)
   */
  unshare: async (brandId: number, shareId: number): Promise<void> => {
    await api.delete(`/brands/${brandId}/shares/${shareId}`);
  },
};

// ==================== USAGE EXAMPLES ====================

/**
 * EXAMPLE 1: Using in React Query
 *
 * // Before (inline API call):
 * const { data: brands } = useQuery({
 *   queryKey: ['brands'],
 *   queryFn: async () => {
 *     const response = await api.get('/brands');
 *     return response.data;
 *   }
 * });
 *
 * // After (typed service):
 * const { data: brands } = useQuery({
 *   queryKey: ['brands'],
 *   queryFn: brandsService.list
 * });
 *
 * // Now TypeScript knows that `brands` is Brand[]!
 * // Auto-complete works: brands[0].brand_name ✓
 */

/**
 * EXAMPLE 2: Creating a brand with mutation
 *
 * // Before:
 * const createMutation = useMutation({
 *   mutationFn: async (data: any) => {
 *     const response = await api.post('/brands', data);
 *     return response.data;
 *   }
 * });
 *
 * // After:
 * const createMutation = useMutation({
 *   mutationFn: brandsService.create
 * });
 *
 * // Now TypeScript ensures you pass BrandCreate data!
 * // createMutation.mutate({ brand_name: 'ACME' }) ✓
 * // createMutation.mutate({ wrong_field: 'foo' }) ✗ Type error!
 */

/**
 * EXAMPLE 3: Sharing a brand
 *
 * // Before:
 * await api.post(`/brands/${brandId}/share`, { email: userEmail });
 *
 * // After:
 * await brandsService.share(brandId, { email: userEmail });
 *
 * // Clearer intent, type-safe, easier to test!
 */
