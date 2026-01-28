/**
 * Barrel export for all manage pages.
 *
 * This allows imports like:
 *   import { BrandInfo, Competitors, Descriptors, Queries } from '@/pages/manage'
 *
 * Instead of:
 *   import BrandInfo from '@/pages/manage/BrandInfo'
 *   import Competitors from '@/pages/manage/Competitors'
 *   import Descriptors from '@/pages/manage/Descriptors'
 *   import Queries from '@/pages/manage/Queries'
 */

export { default as BrandInfo } from './BrandInfo';
export { default as Competitors } from './Competitors';
export { default as Descriptors } from './Descriptors';
export { default as Queries } from './Queries';
