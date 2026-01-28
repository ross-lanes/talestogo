import { api } from './api';
import type { Persona, HeadsFormData, GenerationResult, Source } from '../types/heads';

/**
 * Generate marketing personas using the backend API.
 * The Gemini API key is stored securely on the server.
 */
export const generatePersonas = async (
  formData: HeadsFormData
): Promise<GenerationResult> => {
  const response = await api.post<GenerationResult>('/api/heads/generate-personas', formData);
  return response.data;
};

/**
 * Generate an avatar image for a persona using the backend API.
 * The Gemini API key is stored securely on the server.
 */
export const generatePersonaImage = async (
  persona: Persona,
  styleKeywords?: string
): Promise<string> => {
  const response = await api.post<{ imageBase64: string }>('/api/heads/generate-image', {
    persona,
    styleKeywords,
  });
  return response.data.imageBase64;
};

/**
 * Check if the Gemini API is configured on the server.
 */
export const checkApiStatus = async (): Promise<{ gemini_configured: boolean; message: string }> => {
  const response = await api.get<{ gemini_configured: boolean; message: string }>('/api/heads/api-status');
  return response.data;
};

const HEADS_STORAGE_KEY = 'heads_latest_generation';

export const saveGenerationToStorage = (
  personas: Persona[],
  sources: Source[],
  formData: HeadsFormData
): void => {
  const dataToSave = {
    personas,
    sources,
    formData,
    timestamp: new Date().toISOString(),
  };
  localStorage.setItem(HEADS_STORAGE_KEY, JSON.stringify(dataToSave));
};

export const loadGenerationFromStorage = (): {
  personas: Persona[];
  sources: Source[];
  formData: HeadsFormData;
  timestamp: string;
} | null => {
  const saved = localStorage.getItem(HEADS_STORAGE_KEY);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch {
      return null;
    }
  }
  return null;
};

export const hasStoredGeneration = (): boolean => {
  return !!localStorage.getItem(HEADS_STORAGE_KEY);
};
