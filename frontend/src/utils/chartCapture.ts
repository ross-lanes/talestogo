import html2canvas from 'html2canvas';

/**
 * Capture a chart element as a base64 image
 * @param elementId - The ID of the element to capture
 * @param options - Optional html2canvas options
 * @returns Promise with base64 image string
 */
export const captureChart = async (
  elementId: string,
  options?: Partial<{
    scale: number;
    backgroundColor: string;
    logging: boolean;
  }>
): Promise<string | null> => {
  try {
    const element = document.getElementById(elementId);
    if (!element) {
      console.error(`Element with ID "${elementId}" not found`);
      return null;
    }

    const canvas = await html2canvas(element, {
      scale: options?.scale || 2, // Higher quality
      backgroundColor: options?.backgroundColor || '#ffffff',
      logging: options?.logging || false,
      useCORS: true,
      allowTaint: true,
    });

    return canvas.toDataURL('image/png');
  } catch (error) {
    console.error(`Error capturing chart "${elementId}":`, error);
    return null;
  }
};

/**
 * Capture multiple charts and return them as a map
 * @param chartIds - Array of element IDs to capture
 * @returns Promise with map of chartId -> base64 image
 */
export const captureMultipleCharts = async (
  chartIds: string[]
): Promise<Record<string, string>> => {
  const chartImages: Record<string, string> = {};

  for (const chartId of chartIds) {
    const image = await captureChart(chartId);
    if (image) {
      chartImages[chartId] = image;
    }
  }

  return chartImages;
};

/**
 * Convert base64 to Blob for file upload
 * @param base64 - Base64 image string
 * @returns Blob object
 */
export const base64ToBlob = (base64: string): Blob => {
  const parts = base64.split(';base64,');
  const contentType = parts[0].split(':')[1];
  const raw = window.atob(parts[1]);
  const rawLength = raw.length;
  const uInt8Array = new Uint8Array(rawLength);

  for (let i = 0; i < rawLength; ++i) {
    uInt8Array[i] = raw.charCodeAt(i);
  }

  return new Blob([uInt8Array], { type: contentType });
};
