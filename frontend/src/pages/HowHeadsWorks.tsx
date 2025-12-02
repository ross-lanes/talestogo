import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Divider,
} from '@mui/material';

export default function HowHeadsWorks() {
  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
          How Heads Works
        </Typography>
      </Box>

      {/* Overview */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Overview
        </Typography>
        <Typography variant="body1" paragraph>
          Heads is the Persona Intelligence Platform within the Solstice AI suite. It generates detailed, realistic personas for patients, healthcare providers (HCPs), and other stakeholders to help you understand your audience deeply and craft targeted messaging strategies.
        </Typography>
        <Typography variant="body1" paragraph>
          By leveraging advanced AI models, Heads creates comprehensive persona profiles that include demographics, psychographics, behaviors, motivations, pain points, and communication preferences. These personas serve as powerful tools for marketing teams, product developers, and researchers.
        </Typography>
      </Paper>

      {/* Persona Generation Process */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Persona Generation Process
        </Typography>
        <Typography variant="body1" paragraph>
          The persona generation process in Heads follows a systematic approach:
        </Typography>
        <Box component="ol" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Input Configuration:</strong> You provide key parameters such as therapeutic area, condition focus, target demographic, geographic region, and any specific characteristics you want the personas to embody.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>AI-Powered Generation:</strong> Our AI models synthesize your inputs with extensive knowledge of patient journeys, healthcare provider workflows, and market dynamics to create realistic, nuanced personas.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Profile Construction:</strong> Each persona includes a complete profile with name, background story, demographics, healthcare journey, decision-making factors, information sources, and communication preferences.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Validation & Refinement:</strong> Generated personas can be reviewed, edited, and refined to better match your specific needs and market understanding.
          </Typography>
        </Box>
      </Paper>

      {/* Patient Personas */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Patient Personas
        </Typography>
        <Typography variant="body1" paragraph>
          Patient personas capture the full patient journey and experience:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Demographics:</strong> Age, gender, location, occupation, family status, insurance coverage
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Condition Journey:</strong> Diagnosis story, symptoms experienced, treatments tried, current management
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Emotional State:</strong> Fears, hopes, frustrations, and motivations related to their health condition
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Information Seeking:</strong> How they research health information, trusted sources, digital literacy
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Decision Factors:</strong> What influences their treatment decisions, role of caregivers, financial considerations
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Communication Preferences:</strong> Preferred channels, messaging tone, content formats that resonate
          </Typography>
        </Box>
      </Paper>

      {/* HCP Personas */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Healthcare Provider (HCP) Personas
        </Typography>
        <Typography variant="body1" paragraph>
          HCP personas focus on professional context and prescribing behavior:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Professional Profile:</strong> Specialty, years of experience, practice setting, patient volume
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Prescribing Patterns:</strong> Treatment philosophy, preferred therapies, openness to new treatments
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Information Sources:</strong> Journals read, conferences attended, KOL influences, digital engagement
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Decision Drivers:</strong> What evidence they value, formulary considerations, patient feedback influence
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Practice Challenges:</strong> Time constraints, administrative burden, patient communication challenges
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Engagement Preferences:</strong> Preferred rep interactions, content formats, meeting preferences
          </Typography>
        </Box>
      </Paper>

      {/* Use Cases */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Use Cases
        </Typography>
        <Typography variant="body1" paragraph>
          Heads personas can be used across many functions:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Marketing Strategy:</strong> Develop targeted messaging and campaigns that resonate with specific audience segments
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Content Development:</strong> Create educational materials, website content, and social media posts tailored to persona needs
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Sales Enablement:</strong> Train sales teams on different HCP types and how to engage them effectively
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Product Development:</strong> Understand user needs and pain points to inform product features and positioning
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>User Research:</strong> Use personas as screener criteria for recruiting actual research participants
          </Typography>
        </Box>
      </Paper>

      {/* Best Practices */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Best Practices
        </Typography>
        <Typography variant="body1" paragraph>
          To get the most value from Heads:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Be Specific:</strong> The more detailed your input parameters, the more relevant and useful your personas will be
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Generate Multiple:</strong> Create several personas to capture the diversity within your target audience
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Validate with Data:</strong> Compare generated personas against your existing market research and customer data
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Iterate:</strong> Refine personas over time as you learn more about your actual customers
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Share Widely:</strong> Make personas accessible across your organization to align teams on audience understanding
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
}
