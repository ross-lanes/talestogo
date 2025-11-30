import React from 'react';
import { Typography } from '@mui/material';

// Helper function to render markdown-style formatting
export const formatMarkdown = (text: string): React.ReactNode => {
  // Split by lines to handle headers
  const lines = text.split('\n');

  return lines.map((line, lineIndex) => {
    // Check for headers (## or ###)
    if (line.startsWith('### ')) {
      return (
        <Typography key={lineIndex} variant="subtitle1" sx={{ fontWeight: 600, mt: 2, mb: 1 }}>
          {formatInlineText(line.substring(4))}
        </Typography>
      );
    }
    if (line.startsWith('## ')) {
      return (
        <Typography key={lineIndex} variant="h6" sx={{ fontWeight: 600, mt: 2, mb: 1 }}>
          {formatInlineText(line.substring(3))}
        </Typography>
      );
    }
    if (line.startsWith('# ')) {
      return (
        <Typography key={lineIndex} variant="h5" sx={{ fontWeight: 600, mt: 2, mb: 1 }}>
          {formatInlineText(line.substring(2))}
        </Typography>
      );
    }

    // Regular line with inline formatting
    return (
      <span key={lineIndex}>
        {formatInlineText(line)}
        {lineIndex < lines.length - 1 && '\n'}
      </span>
    );
  });
};

// Helper to handle inline formatting (bold, italic)
export const formatInlineText = (text: string): React.ReactNode => {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Look for **bold** text
    const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
    // Look for *italic* text (single asterisk)
    const italicMatch = remaining.match(/(?<!\*)\*(?!\*)([^*]+)\*(?!\*)/);

    if (boldMatch && boldMatch.index !== undefined) {
      // Add text before the match
      if (boldMatch.index > 0) {
        parts.push(<span key={key++}>{remaining.substring(0, boldMatch.index)}</span>);
      }
      // Add the bold text
      parts.push(<strong key={key++}>{boldMatch[1]}</strong>);
      remaining = remaining.substring(boldMatch.index + boldMatch[0].length);
    } else if (italicMatch && italicMatch.index !== undefined) {
      // Add text before the match
      if (italicMatch.index > 0) {
        parts.push(<span key={key++}>{remaining.substring(0, italicMatch.index)}</span>);
      }
      // Add the italic text
      parts.push(<em key={key++}>{italicMatch[1]}</em>);
      remaining = remaining.substring(italicMatch.index + italicMatch[0].length);
    } else {
      // No more matches, add remaining text
      parts.push(<span key={key++}>{remaining}</span>);
      break;
    }
  }

  return parts.length > 0 ? parts : text;
};
