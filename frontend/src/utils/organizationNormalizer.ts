/**
 * FRONTEND MIRROR of backend organization normalization.
 *
 * IMPORTANT: Keep this synchronized with app/services/metrics.py::normalize_organization_name()
 * The backend is the SINGLE SOURCE OF TRUTH. This frontend version exists for:
 * - Client-side filtering and display logic
 * - Immediate UI feedback without round-trip to backend
 *
 * When adding new normalization rules, update BOTH:
 * 1. app/services/metrics.py (primary source)
 * 2. This file (frontend mirror)
 *
 * Normalizes organization names for consistent grouping.
 * Examples:
 * - "STEP", "MAST-U", "UKAEA" -> "UKAEA"
 * - "ST40", "Tokamak Energy" -> "Tokamak Energy"
 * - "OpenAI", "Open AI" -> "OpenAI"
 * - "Google Cloud", "Google" -> "Google"
 */
export function normalizeOrganizationName(name: string): string {
  if (!name) return name;

  const nameLower = name.toLowerCase().trim();

  // UKAEA variants (STEP and MAST-U are machines/projects made by UKAEA)
  if (nameLower.includes('step') || nameLower.includes('mast-u') ||
      nameLower.includes('mast u') || nameLower.includes('ukaea')) {
    return 'UKAEA';
  }

  // Tokamak Energy variants (ST40 is a machine made by Tokamak Energy)
  if (nameLower.includes('st40') || nameLower.includes('st-40') ||
      nameLower.includes('tokamak energy')) {
    return 'Tokamak Energy';
  }

  // Tech company normalizations (exact matches)
  const normalizations: Record<string, string> = {
    // OpenAI variations
    'open ai': 'OpenAI',
    'openai': 'OpenAI',

    // Google variations
    'google': 'Google',
    'google cloud': 'Google',
    'google workspace': 'Google',

    // Microsoft variations
    'microsoft': 'Microsoft',
    'microsoft azure': 'Microsoft',
    'microsoft 365': 'Microsoft',

    // Amazon variations
    'aws': 'AWS',
    'amazon web services': 'AWS',
    'amazon aws': 'AWS',
  };

  // Check dictionary for exact match (case-insensitive)
  const normalized = normalizations[nameLower];
  if (normalized) {
    return normalized;
  }

  // Return original name if no normalization rule matched
  return name.trim();
}

/**
 * Check if a comma-separated list of competitors contains a specific organization,
 * accounting for normalization rules.
 */
export function competitorsInclude(competitorsList: string | null | undefined, targetOrg: string): boolean {
  if (!competitorsList) return false;

  const competitors = competitorsList.split(',').map(c => c.trim());
  const normalizedTarget = normalizeOrganizationName(targetOrg);

  return competitors.some(comp => normalizeOrganizationName(comp) === normalizedTarget);
}
