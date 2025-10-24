// Query types
export interface Query {
  id: number;
  query_id: string;
  query_text: string;
  category: string;
  priority: string;
  target_outcome: string;
  active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface QueryCreate {
  query_id: string;
  query_text: string;
  category: string;
  priority: string;
  target_outcome: string;
  active: boolean;
  notes?: string;
}

export interface QueryUpdate {
  query_text?: string;
  category?: string;
  priority?: string;
  target_outcome?: string;
  active?: boolean;
  notes?: string;
}

// Competitor types
export interface Competitor {
  id: number;
  organization: string;
  type: string;
  focus_area?: string;
  track: boolean;
  key_descriptors?: string;
  website?: string;
  notes?: string;
  created_at: string;
}

export interface CompetitorCreate {
  organization: string;
  type: string;
  focus_area?: string;
  track: boolean;
  key_descriptors?: string;
  website?: string;
  notes?: string;
}

export interface CompetitorUpdate {
  organization?: string;
  type?: string;
  focus_area?: string;
  track?: boolean;
  key_descriptors?: string;
  website?: string;
  notes?: string;
}

// Descriptor types
export interface TargetDescriptor {
  id: number;
  descriptor: string;
  category: string;
  target_for_pppl: boolean;
  current_ownership?: string;
  priority: string;
  notes?: string;
  created_at: string;
}

export interface TargetDescriptorCreate {
  descriptor: string;
  category: string;
  target_for_pppl: boolean;
  current_ownership?: string;
  priority: string;
  notes?: string;
}

export interface TargetDescriptorUpdate {
  descriptor?: string;
  category?: string;
  target_for_pppl?: boolean;
  current_ownership?: string;
  priority?: string;
  notes?: string;
}

// Response types
export interface Response {
  id: number;
  query_id: string;
  query_text: string;
  platform: string;
  response_text: string;
  timestamp: string;
  pppl_mentioned?: string;
  pppl_position?: string;
  sentiment?: string;
  descriptors?: string;
  competitors?: string;
  sources?: string;
  notes?: string;
  analyzed_at?: string;
}

// Dashboard metrics types
export interface DashboardMetrics {
  mention_rate: number;
  positive_sentiment_rate: number;
  descriptor_match_rate: number;
  share_of_voice: number;
  avg_positioning: number;
  trends: {
    mention_rate_change: number;
    sentiment_change: number;
    descriptor_change: number;
  };
}

// Share of Voice types
export interface ShareOfVoice {
  organization: string;
  percentage: number;
  mention_count: number;
}

// Positioning breakdown types
export interface PositioningBreakdown {
  featured: number;
  top_3: number;
  listed: number;
  indirect: number;
  not_mentioned: number;
}

// Descriptor performance types
export interface DescriptorPerformance {
  descriptor: string;
  match_rate: number;
  count: number;
}

// Threat analysis types
export interface ThreatAnalysis {
  public_threat: {
    organization: string;
    description: string;
  };
  private_threat: {
    organization: string;
    description: string;
  };
  narrative_threat: {
    title: string;
    description: string;
  };
}

// Strategic priorities types
export interface StrategicPriority {
  title: string;
  description: string;
  supporting_data?: any;
}
