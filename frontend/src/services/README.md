# Typed API Services

This directory contains typed API service modules that provide type-safe interfaces to the backend API.

## Why Typed Services?

**Benefits:**
- ✅ Full TypeScript type safety for all API calls
- ✅ Auto-complete in IDEs (knows field names, types)
- ✅ Centralized API endpoint management
- ✅ Easier to test and mock
- ✅ Single source of truth for each resource's API
- ✅ Catches typos and type errors at compile time

**Before (Inline API Calls):**
```typescript
// ❌ No type safety, error-prone
const { data } = await api.get('/brands');
// What fields does data have? Who knows!

// ❌ Easy to make typos
await api.post('/brand', { brand_name: 'foo' }); // Wrong endpoint!

// ❌ No autocomplete
data[0].brand_nam // Typo! Runtime error!
```

**After (Typed Service):**
```typescript
// ✅ Full type safety
const brands = await brandsService.list();
// TypeScript knows it's Brand[]

// ✅ Autocomplete works
brands[0].brand_name // ✓ Autocomplete shows all fields!

// ✅ Type errors caught at compile time
await brandsService.create({ wrong_field: 'foo' });
// ^ Compile error: Property 'brand_name' is missing
```

## Current Services

### ✅ Implemented
- **`api.ts`** - Base axios instance with auth interceptors
- **`authAPI`** - Authentication endpoints (login, register, etc.)
- **`adminAPI`** - Admin-only endpoints
- **`brandsService.ts`** - Brand CRUD operations (TEMPLATE)

### 🔲 To Be Implemented
- `competitorsService.ts` - Competitor management
- `descriptorsService.ts` - Descriptor management
- `queriesService.ts` - Query management
- `responsesService.ts` - Response data
- `analyticsService.ts` - Analytics endpoints
- `reportsService.ts` - Report generation
- `schedulesService.ts` - Scheduled tasks

## Migration Strategy

**IMPORTANT: Do NOT migrate everything at once!** High risk of regressions.

### Phase 1: Foundation (DONE)
- [x] Create `brandsService.ts` as template
- [x] Document pattern in README

### Phase 2: Incremental Adoption (RECOMMENDED)
1. **Use typed services for NEW features only**
   - Writing a new page? Use typed services
   - Adding a new feature? Use typed services

2. **Migrate ONE page at a time**
   - Pick the smallest/simplest page first
   - Migrate all its API calls to typed services
   - Test thoroughly
   - Commit

3. **Migrate during bug fixes**
   - Touching a file for a bug fix? Migrate its API calls too
   - Combines refactoring with bug fixing (efficient!)

### Phase 3: Complete Migration (FUTURE)
- Only after most code uses typed services
- Low risk at this point

## How to Create a New Service

Use `brandsService.ts` as a template. Follow this pattern:

### 1. Define Types

```typescript
export interface MyResource {
  id: number;
  name: string;
  created_at: string;
}

export interface MyResourceCreate {
  name: string;
}

export interface MyResourceUpdate {
  name?: string;
}
```

### 2. Create Service Object

```typescript
export const myResourceService = {
  list: async (): Promise<MyResource[]> => {
    const response = await api.get<MyResource[]>('/my-resources');
    return response.data;
  },

  get: async (id: number): Promise<MyResource> => {
    const response = await api.get<MyResource>(`/my-resources/${id}`);
    return response.data;
  },

  create: async (data: MyResourceCreate): Promise<MyResource> => {
    const response = await api.post<MyResource>('/my-resources', data);
    return response.data;
  },

  update: async (id: number, data: MyResourceUpdate): Promise<MyResource> => {
    const response = await api.put<MyResource>(`/my-resources/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/my-resources/${id}`);
  },
};
```

### 3. Use in React Query

```typescript
import { myResourceService } from '@/services/myResourceService';

function MyComponent() {
  // List query
  const { data: items } = useQuery({
    queryKey: ['myResources'],
    queryFn: myResourceService.list
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: myResourceService.create,
    onSuccess: () => queryClient.invalidateQueries(['myResources'])
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => myResourceService.update(id, data)
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: myResourceService.delete
  });
}
```

## Best Practices

### ✅ DO

- **Export types** - Make types reusable
- **Use generics** - `api.get<Brand>()` for type inference
- **One service per resource** - Keep files focused
- **Document complex endpoints** - Add JSDoc comments
- **Return response.data** - Don't return the whole Axios response

### ❌ DON'T

- **Don't use `any`** - Defeats the purpose of type safety
- **Don't inline types** - Define types at the top
- **Don't mix concerns** - One service = one resource
- **Don't forget to update types** - When backend API changes, update types!

## Common Patterns

### Query with Parameters

```typescript
export const myResourceService = {
  list: async (params?: { brandId?: number; search?: string }): Promise<MyResource[]> => {
    const response = await api.get<MyResource[]>('/my-resources', { params });
    return response.data;
  },
};

// Usage:
myResourceService.list({ brandId: 123, search: 'foo' });
```

### File Upload

```typescript
export const myResourceService = {
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<UploadResponse>(
      '/my-resources/upload',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    );
    return response.data;
  },
};
```

### Nested Resources

```typescript
export const competitorsService = {
  // For brand-specific competitors
  listByBrand: async (brandId: number): Promise<Competitor[]> => {
    const response = await api.get<Competitor[]>(`/brands/${brandId}/competitors`);
    return response.data;
  },

  // For user's all competitors
  list: async (): Promise<Competitor[]> => {
    const response = await api.get<Competitor[]>('/competitors');
    return response.data;
  },
};
```

## Testing

Typed services are MUCH easier to mock for testing:

```typescript
// Mock the service
jest.mock('@/services/brandsService', () => ({
  brandsService: {
    list: jest.fn(() => Promise.resolve([
      { id: 1, brand_name: 'Test Brand', user_id: 1, created_at: '2024-01-01', is_active: true }
    ]))
  }
}));

// Test component using the service
test('displays brands', async () => {
  render(<BrandsPage />);
  await waitFor(() => {
    expect(screen.getByText('Test Brand')).toBeInTheDocument();
  });
});
```

## Questions?

- See `brandsService.ts` for a complete example with usage documentation
- Follow the same pattern for consistency
- When in doubt, keep it simple!
