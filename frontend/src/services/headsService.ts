import type { Persona, HeadsFormData, GenerationResult, Source } from '../types/heads';

const generateId = () => Math.random().toString(36).substr(2, 9);

const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

export const generatePersonas = async (
  formData: HeadsFormData,
  apiKey: string
): Promise<GenerationResult> => {
  if (!apiKey) {
    throw new Error('Gemini API Key is required. Please add it in Settings.');
  }

  const archetypeInstruction =
    formData.archetypes && formData.archetypes.length > 0
      ? `Include personas matching these specific archetypes: ${formData.archetypes.join(', ')}.`
      : '';

  const customTraits = [
    formData.customCharacteristic1,
    formData.customCharacteristic2,
    formData.customCharacteristic3,
    formData.customCharacteristic4,
  ].filter(Boolean);

  const customTraitsInstruction =
    customTraits.length > 0
      ? `MANDATORY CHARACTERISTICS: Ensure the generated personas incorporate the following specific traits/characteristics where appropriate: ${customTraits.join(', ')}.`
      : '';

  const count = formData.numberOfPersonas || 3;
  const brandAccountInstruction = formData.brandAccount
    ? `The specific brand account or focus area is: "${formData.brandAccount}".`
    : '';
  const accountDetailsInstruction = formData.accountDetails
    ? `Contextual Account Details & Goals: "${formData.accountDetails}".`
    : '';

  const prompt = `
    You are an expert marketing strategist. Create detailed user personas for the brand: "${formData.brand}".
    ${formData.website ? `The brand's website is: ${formData.website}.` : ''}
    ${brandAccountInstruction}
    ${accountDetailsInstruction}

    Target Occupations: ${formData.occupations}
    Target Countries: ${formData.targetCountries || 'Global / Relevant to brand'}
    Target Age Ranges: ${formData.ageRanges || 'Varies based on occupation'}

    ${archetypeInstruction}
    ${customTraitsInstruction}

    QUANTITY REQUIREMENT:
    You MUST generate a JSON list containing EXACTLY ${count} distinct personas.
    Do not stop after one. Ensure the array has ${count} items.

    CRITICAL INSTRUCTIONS FOR ACCURACY:
    1. Ensure occupation details, salary expectations, and industry trends are accurate.
    2. Assign a specific "location" (City, Country) to each persona${formData.targetCountries ? ` based on the requested countries: ${formData.targetCountries}` : ''}.
    3. Assign a specific "workplace".
       - IF the occupation is a medical professional (e.g., Doctor, Nurse, Surgeon), use a REAL, EXISTING medical facility (Hospital, Clinic) in that specific "location".
       - For other occupations, generate a plausible company name or use a real one if relevant.
    4. Determine "technologyAbility" - Provide a descriptive rating (e.g., "Expert - Highly proficient with industry software").
    5. Determine "technologyComfortability" - Provide a sentiment (e.g., "Early Adopter - Always tries new features", "Skeptic - Prefers established tools").

    OUTPUT FORMAT:
    Return ONLY a valid JSON array. Do not include markdown formatting (like \`\`\`json).
    The output must be a raw JSON array of objects.

    Structure:
    [
      {
        "generalizationTitle": "The Pioneer",
        "name": "Alex Chen",
        "age": "28",
        "occupation": "UX Designer",
        "location": "Seattle, WA",
        "workplace": "Amazon",
        "technologyAbility": "Expert - Proficient in code & design",
        "technologyComfortability": "Digital Native - Early Adopter",
        "profile": "...",
        "goals": ["..."],
        "frustrations": ["..."],
        "brandView": "...",
        "marketingStrategy": "..."
      },
      ... (${count} total objects)
    ]
  `;

  const response = await fetch(`${GEMINI_API_URL}?key=${apiKey}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      contents: [
        {
          parts: [{ text: prompt }],
        },
      ],
      generationConfig: {
        temperature: 0.9,
        topK: 40,
        topP: 0.95,
        maxOutputTokens: 8192,
      },
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.error?.message || `API request failed with status ${response.status}`
    );
  }

  const data = await response.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text;

  if (!text) {
    throw new Error('No response from AI');
  }

  let personas: Persona[] = [];
  try {
    const cleanedText = text.replace(/```json/g, '').replace(/```/g, '').trim();
    let parsedData = JSON.parse(cleanedText);

    if (!Array.isArray(parsedData) && typeof parsedData === 'object' && parsedData !== null) {
      const keys = Object.keys(parsedData);
      const arrayKey = keys.find((k) => Array.isArray(parsedData[k]));
      if (arrayKey) {
        parsedData = parsedData[arrayKey];
      }
    }

    if (!Array.isArray(parsedData)) {
      throw new Error('Response is not an array');
    }

    personas = parsedData.map((p: Persona) => ({ ...p, id: generateId() }));
  } catch (e) {
    console.error('Failed to parse JSON', e);
    console.log('Raw text:', text);
    throw new Error('Failed to parse persona data. The model might have returned invalid JSON.');
  }

  const sources: Source[] = [];

  return {
    personas,
    sources,
  };
};

export const generatePersonaImage = async (
  persona: Persona,
  apiKey: string,
  styleKeywords?: string
): Promise<string> => {
  if (!apiKey) {
    throw new Error('Gemini API Key is required');
  }

  const styleBase =
    styleKeywords && styleKeywords.trim() !== ''
      ? `Visual Style: ${styleKeywords}.`
      : `Visual Style: Photorealistic, professional lighting.`;

  const prompt = `
    Generate a professional portrait avatar for a user persona.

    Persona Details:
    - Name: ${persona.name}
    - Age: ${persona.age}
    - Occupation: ${persona.occupation}
    - Description: ${persona.profile}

    STRICT COMPOSITION REQUIREMENTS:
    1. The subject MUST look directly straight into the camera (direct eye contact).
    2. The framing MUST be a strict head-and-shoulders shot (head, neck, and tops of shoulders only).
    3. Center the subject.
    4. Neutral, clean background.

    ${styleBase}
  `;

  const imageApiUrl =
    'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent';

  const response = await fetch(`${imageApiUrl}?key=${apiKey}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      contents: [
        {
          parts: [{ text: prompt }],
        },
      ],
      generationConfig: {
        responseModalities: ['image', 'text'],
        responseMimeType: 'text/plain',
      },
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.error?.message || `Image generation failed with status ${response.status}`
    );
  }

  const data = await response.json();

  for (const part of data.candidates?.[0]?.content?.parts || []) {
    if (part.inlineData && part.inlineData.data) {
      return `data:${part.inlineData.mimeType};base64,${part.inlineData.data}`;
    }
  }

  throw new Error('No image data received');
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
