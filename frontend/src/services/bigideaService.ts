import { api } from './api';
import type {
  BigIdeaFormData,
  GeneratedResponse,
  Idea,
  ClientProject,
} from '../types/bigidea';

/**
 * Generate marketing Big Ideas using the backend API.
 * The Gemini API key is stored securely on the server.
 */
export const generateBigIdeas = async (
  formData: BigIdeaFormData
): Promise<GeneratedResponse> => {
  const response = await api.post<GeneratedResponse>('/api/bigidea/generate-ideas', formData);
  return response.data;
};

/**
 * Expand an existing idea with more detail using the backend API.
 * The Gemini API key is stored securely on the server.
 */
export const expandIdea = async (
  formData: BigIdeaFormData,
  originalIdea: Idea
): Promise<GeneratedResponse> => {
  const response = await api.post<GeneratedResponse>('/api/bigidea/expand-idea', {
    formData,
    originalIdea,
  });
  return response.data;
};

/**
 * Check if the Gemini API is configured on the server.
 */
export const checkApiStatus = async (): Promise<{ gemini_configured: boolean; message: string }> => {
  const response = await api.get<{ gemini_configured: boolean; message: string }>('/api/bigidea/api-status');
  return response.data;
};

// --- Local Storage for Projects ---

const BIGIDEA_PROJECTS_KEY = 'bigidea_projects';
const BIGIDEA_LATEST_KEY = 'bigidea_latest_generation';

/**
 * Save projects to local storage
 */
export const saveProjects = (projects: ClientProject[]): void => {
  localStorage.setItem(BIGIDEA_PROJECTS_KEY, JSON.stringify(projects));
};

/**
 * Load projects from local storage
 */
export const getProjects = (): ClientProject[] => {
  const saved = localStorage.getItem(BIGIDEA_PROJECTS_KEY);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch {
      return [];
    }
  }
  return [];
};

/**
 * Save latest generation to local storage for persistence
 */
export const saveGenerationToStorage = (
  response: GeneratedResponse,
  formData: BigIdeaFormData
): void => {
  const dataToSave = {
    response,
    formData,
    timestamp: new Date().toISOString(),
  };
  localStorage.setItem(BIGIDEA_LATEST_KEY, JSON.stringify(dataToSave));
};

/**
 * Load latest generation from local storage
 */
export const loadGenerationFromStorage = (): {
  response: GeneratedResponse;
  formData: BigIdeaFormData;
  timestamp: string;
} | null => {
  const saved = localStorage.getItem(BIGIDEA_LATEST_KEY);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch {
      return null;
    }
  }
  return null;
};

/**
 * Check if there is a stored generation
 */
export const hasStoredGeneration = (): boolean => {
  return !!localStorage.getItem(BIGIDEA_LATEST_KEY);
};

/**
 * Clear stored generation
 */
export const clearStoredGeneration = (): void => {
  localStorage.removeItem(BIGIDEA_LATEST_KEY);
};
