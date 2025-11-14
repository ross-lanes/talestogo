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

/**
 * Capture and upload dashboard charts for report generation
 * This is automatically called after data collection completes
 * @param chartContainerIds - Map of chart names to their container element IDs
 * @param api - API instance for making requests
 * @returns Promise with upload result
 */
export const captureAndUploadCharts = async (
  chartContainerIds: Record<string, string>,
  api: any
): Promise<{ success: boolean; message: string }> => {
  try {
    console.log('📸 Capturing charts for report generation...');

    const chartImages: Record<string, string> = {};
    const timestamp = new Date().toISOString();

    // Capture each chart
    for (const [chartName, elementId] of Object.entries(chartContainerIds)) {
      try {
        const base64Image = await captureChart(elementId, {
          scale: 2,
          backgroundColor: '#ffffff',
          logging: false,
        });

        if (base64Image) {
          chartImages[chartName] = base64Image;
          console.log(`  ✓ Captured ${chartName} chart`);
        } else {
          console.warn(`  ⚠ Failed to capture ${chartName} chart`);
        }
      } catch (error) {
        console.error(`  ✗ Error capturing ${chartName}:`, error);
      }
    }

    // Upload to backend
    if (Object.keys(chartImages).length > 0) {
      const formData = new FormData();
      formData.append('timestamp', timestamp);

      // Add each chart image to form data
      for (const [chartName, base64Image] of Object.entries(chartImages)) {
        formData.append(chartName, base64Image);
      }

      const response = await api.post('/reports/upload-charts', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log(`✅ Uploaded ${Object.keys(chartImages).length} charts successfully`);
      return {
        success: true,
        message: response.data.message || 'Charts uploaded successfully',
      };
    } else {
      return {
        success: false,
        message: 'No charts were captured',
      };
    }
  } catch (error: any) {
    console.error('❌ Error uploading charts:', error);
    return {
      success: false,
      message: error.response?.data?.detail || error.message || 'Failed to upload charts',
    };
  }
};
