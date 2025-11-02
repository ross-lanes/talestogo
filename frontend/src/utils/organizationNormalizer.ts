/**
 * Normalize organization names to combine related entities.
 *
 * UKAEA, STEP, and MAST-U are all combined under "UKAEA"
 * Tokamak Energy and ST40 are combined under "Tokamak Energy"
 */
export function normalizeOrganizationName(name: string): string {
  const nameLower = name.toLowerCase().trim();

  // UKAEA variants (STEP and MAST-U are machines made by UKAEA)
  if (nameLower.includes('step') || nameLower.includes('mast-u') || nameLower.includes('mast u') || nameLower.includes('ukaea')) {
    return 'UKAEA';
  }

  // Tokamak Energy variants (ST40 is a machine made by Tokamak Energy)
  if (nameLower.includes('st40') || nameLower.includes('st-40') || nameLower.includes('tokamak energy')) {
    return 'Tokamak Energy';
  }

  // Return original name if no normalization needed
  return name;
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
