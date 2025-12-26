/**
 * Big Idea Generator Types
 *
 * Types for the marketing idea generation feature.
 */

// --- Constants (replacing enums for erasableSyntaxOnly compatibility) ---

export const IdeaScale = {
  SAFE: 'Safe',
  AMBITIOUS: 'Ambitious',
  VERY_AMBITIOUS: 'Very Ambitious',
  INCREDIBLY_AMBITIOUS: 'Incredibly Ambitious',
} as const;

export type IdeaScale = (typeof IdeaScale)[keyof typeof IdeaScale];

export const CampaignGoal = {
  BRAND_AWARENESS: 'Brand Awareness',
  LEAD_GENERATION: 'Lead Generation',
  SALES_GROWTH: 'Sales Growth',
  CUSTOMER_RETENTION: 'Customer Retention',
  MARKET_EXPANSION: 'Market Expansion',
  PRODUCT_LAUNCH: 'Product Launch',
  WEBSITE_TRAFFIC: 'Website Traffic',
  APP_INSTALLS: 'App Installs',
  ENGAGEMENT: 'Engagement',
  OTHER: 'Other',
} as const;

export type CampaignGoal = (typeof CampaignGoal)[keyof typeof CampaignGoal];

export const BudgetIndicator = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
  PREMIUM: 'Premium',
} as const;

export type BudgetIndicator = (typeof BudgetIndicator)[keyof typeof BudgetIndicator];

// --- Interfaces ---

/**
 * Form data for big idea generation
 */
export interface BigIdeaFormData {
  clientName: string;
  accountName?: string;
  clientDescription: string;
  competitors?: string;
  strategicImperatives?: string;
  numberOfIdeas: number;
  ideaAreas: string;
  ideaScale: IdeaScale;
  targetAudience: string;
  countryRegion?: string;
  campaignGoal: CampaignGoal;
  budget: BudgetIndicator;
}

/**
 * A single generated marketing idea
 */
export interface Idea {
  id: string;
  title: string;
  description: string;
  area: string;
  scale: string;
  rationale: string;
}

/**
 * Market share data for a competitor
 */
export interface MarketShareDataItem {
  name: string;
  percentage: number;
}

/**
 * Competitor analysis from AI generation
 */
export interface CompetitorAnalysis {
  competitors: string[];
  competitorStrategies: string;
  differentiationStrategies: string;
  marketShareData?: MarketShareDataItem[];
}

/**
 * URL from Google Search grounding
 */
export interface GroundingUrl {
  uri: string;
  title?: string;
}

/**
 * Full response from idea generation
 */
export interface GeneratedResponse {
  ideas: Idea[];
  competitorAnalysis: CompetitorAnalysis;
  groundingUrls?: GroundingUrl[];
}

/**
 * A saved idea in the user's library
 */
export interface SavedIdea extends Idea {
  savedAt: number;
  notes: string;
  tags: string[];
  projectId: string;
}

/**
 * A project that groups saved ideas
 */
export interface ClientProject {
  id: string;
  name: string;
  ideas: SavedIdea[];
}

// --- Dropdown Options ---

export const IDEA_SCALE_OPTIONS: { value: IdeaScale; label: string }[] = [
  { value: IdeaScale.SAFE, label: 'Safe (Incremental, low risk)' },
  { value: IdeaScale.AMBITIOUS, label: 'Ambitious (Innovative, moderate risk)' },
  { value: IdeaScale.VERY_AMBITIOUS, label: 'Very Ambitious (Disruptive, higher risk)' },
  { value: IdeaScale.INCREDIBLY_AMBITIOUS, label: 'Incredibly Ambitious (Moonshot, high risk, high reward)' },
];

export const NUMBER_OF_IDEAS_OPTIONS: { value: number; label: string }[] = Array.from({ length: 10 }, (_, i) => ({
  value: i + 1,
  label: `${i + 1} idea${i === 0 ? '' : 's'}`,
}));

export const CAMPAIGN_GOAL_OPTIONS: { value: CampaignGoal; label: string }[] = [
  { value: CampaignGoal.BRAND_AWARENESS, label: 'Brand Awareness' },
  { value: CampaignGoal.LEAD_GENERATION, label: 'Lead Generation' },
  { value: CampaignGoal.SALES_GROWTH, label: 'Sales Growth' },
  { value: CampaignGoal.CUSTOMER_RETENTION, label: 'Customer Retention' },
  { value: CampaignGoal.MARKET_EXPANSION, label: 'Market Expansion' },
  { value: CampaignGoal.PRODUCT_LAUNCH, label: 'Product Launch' },
  { value: CampaignGoal.WEBSITE_TRAFFIC, label: 'Website Traffic' },
  { value: CampaignGoal.APP_INSTALLS, label: 'App Installs' },
  { value: CampaignGoal.ENGAGEMENT, label: 'Engagement' },
  { value: CampaignGoal.OTHER, label: 'Other' },
];

export const BUDGET_INDICATOR_OPTIONS: { value: BudgetIndicator; label: string }[] = [
  { value: BudgetIndicator.LOW, label: 'Low (Minimal budget)' },
  { value: BudgetIndicator.MEDIUM, label: 'Medium (Standard budget)' },
  { value: BudgetIndicator.HIGH, label: 'High (Significant budget)' },
  { value: BudgetIndicator.PREMIUM, label: 'Premium (Top-tier budget)' },
];

// --- Default Values ---

export const DEFAULT_FORM_DATA: BigIdeaFormData = {
  clientName: '',
  accountName: '',
  clientDescription: '',
  competitors: '',
  strategicImperatives: '',
  numberOfIdeas: 3,
  ideaAreas: '',
  ideaScale: IdeaScale.SAFE,
  targetAudience: '',
  countryRegion: '',
  campaignGoal: CampaignGoal.BRAND_AWARENESS,
  budget: BudgetIndicator.MEDIUM,
};
