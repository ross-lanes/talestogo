export interface Persona {
  id: string;
  generalizationTitle: string;
  name: string;
  age: string;
  occupation: string;
  location: string;
  workplace: string;
  technologyAbility: string;
  technologyComfortability: string;
  profile: string;
  goals: string[];
  frustrations: string[];
  brandView: string;
  marketingStrategy: string;
  avatarBase64?: string;
}

export interface Source {
  title: string;
  uri: string;
}

export interface GenerationResult {
  personas: Persona[];
  sources: Source[];
}

export interface HeadsFormData {
  brand: string;
  brandAccount: string;
  accountDetails: string;
  occupations: string;
  targetCountries: string;
  ageRanges: string;
  website: string;
  archetypes: string[];
  numberOfPersonas: number;
  customCharacteristic1: string;
  customCharacteristic2: string;
  customCharacteristic3: string;
  customCharacteristic4: string;
}

export const ExportFormat = {
  JSON: 'json',
  MARKDOWN: 'md',
  TXT: 'txt'
} as const;

export type ExportFormat = typeof ExportFormat[keyof typeof ExportFormat];

export interface Archetype {
  id: string;
  description: string;
}

export const ARCHETYPES: Archetype[] = [
  { id: 'The Early Adopter', description: 'Risk-taker, tech-savvy, seeks novelty.' },
  { id: 'The Loyal Customer', description: 'Values consistency, trust, and relationship.' },
  { id: 'The Budget Conscious', description: 'Price-sensitive, value-seeker, compares options.' },
  { id: 'The Researcher', description: 'Detail-oriented, reads reviews, needs specs.' },
  { id: 'The Skeptic', description: 'Hard to convert, needs social proof and guarantees.' },
  { id: 'The Power User', description: 'Demands advanced features and customizability.' }
];

export const DEFAULT_FORM_DATA: HeadsFormData = {
  brand: '',
  brandAccount: '',
  accountDetails: '',
  occupations: '',
  targetCountries: '',
  ageRanges: '',
  website: '',
  archetypes: [],
  numberOfPersonas: 3,
  customCharacteristic1: '',
  customCharacteristic2: '',
  customCharacteristic3: '',
  customCharacteristic4: ''
};
