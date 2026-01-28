import React from 'react';
import {
  Box,
  Typography,
  Paper,
} from '@mui/material';

export default function HowCanonWorks() {
  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
          How Canon Works
        </Typography>
      </Box>

      {/* Overview */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Overview
        </Typography>
        <Typography variant="body1" paragraph>
          Canon is the FDA Drug Data Research platform within the Solstice AI suite. It provides intelligent access to FDA drug approval data, labels, adverse event reports, and regulatory documents, enabling pharmaceutical researchers, medical affairs teams, and regulatory professionals to quickly find and analyze drug information.
        </Typography>
        <Typography variant="body1" paragraph>
          By combining structured FDA databases with AI-powered natural language querying, Canon makes it easy to research drug approvals, compare medications, understand safety profiles, and stay current with regulatory developments.
        </Typography>
      </Paper>

      {/* Data Sources */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Data Sources
        </Typography>
        <Typography variant="body1" paragraph>
          Canon integrates data from multiple FDA sources:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Drug Labels (DailyMed):</strong> Complete prescribing information including indications, dosing, contraindications, warnings, and drug interactions
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Drug Approvals (Drugs@FDA):</strong> Approval dates, application types (NDA, BLA, ANDA), approval pathways, and regulatory history
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Adverse Event Reports (FAERS):</strong> Post-market safety surveillance data including reported adverse events, outcomes, and patient demographics
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Orange Book:</strong> Therapeutic equivalence evaluations and patent/exclusivity information
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Clinical Trials (ClinicalTrials.gov):</strong> Related trial information for drugs under investigation
          </Typography>
        </Box>
      </Paper>

      {/* Key Features */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Key Features
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Look Up
        </Typography>
        <Typography variant="body1" paragraph>
          Quickly search for any drug by brand name, generic name, or active ingredient. Get instant access to the current label, approval status, manufacturer information, and key safety data.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Ask a Question
        </Typography>
        <Typography variant="body1" paragraph>
          Use natural language to ask questions about drugs. Canon's AI understands your question, searches relevant FDA data, and provides a comprehensive answer with citations. Examples:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body2">
            "What are the contraindications for Drug X in patients with renal impairment?"
          </Typography>
          <Typography component="li" variant="body2">
            "Which drugs in this class were approved via accelerated approval?"
          </Typography>
          <Typography component="li" variant="body2">
            "What post-marketing safety warnings have been issued for Drug Y?"
          </Typography>
        </Box>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Check a Document
        </Typography>
        <Typography variant="body1" paragraph>
          Upload regulatory documents, medical writing drafts, or promotional materials to check them against FDA data. Canon identifies claims that need verification, flags potential inconsistencies with label language, and suggests relevant FDA sources.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Compare Drugs
        </Typography>
        <Typography variant="body1" paragraph>
          Side-by-side comparison of multiple drugs across key dimensions including indications, dosing, safety profiles, approval history, and clinical trial data. Useful for competitive intelligence and treatment selection analysis.
        </Typography>
      </Paper>

      {/* Adverse Event Analysis */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Adverse Event Analysis
        </Typography>
        <Typography variant="body1" paragraph>
          Canon provides powerful tools for analyzing FDA Adverse Event Reporting System (FAERS) data:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Event Frequency:</strong> See the most commonly reported adverse events for any drug
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Outcome Analysis:</strong> Understand the severity distribution including hospitalizations, life-threatening events, and deaths
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Demographic Patterns:</strong> Analyze how adverse events vary by age, gender, and other patient characteristics
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Temporal Trends:</strong> Track how adverse event reports have changed over time since approval
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Comparative Safety:</strong> Compare adverse event profiles across drugs in the same class
          </Typography>
        </Box>
        <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
          Note: FAERS data has known limitations including underreporting, lack of causality confirmation, and potential duplicate reports. Canon provides this data for research purposes and it should not be used as the sole basis for clinical decisions.
        </Typography>
      </Paper>

      {/* Use Cases */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Use Cases
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Medical Affairs:</strong> Quickly answer HCP questions about drug labels, conduct competitive analysis, and prepare for advisory board meetings
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Regulatory Affairs:</strong> Research approval pathways, track competitor regulatory strategies, and prepare submission documents
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Pharmacovigilance:</strong> Monitor adverse event trends, prepare signal detection analyses, and benchmark safety profiles
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Commercial Strategy:</strong> Understand competitive landscape, identify market opportunities, and support launch planning
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Medical Writing:</strong> Verify claims against FDA sources, ensure label compliance, and cite regulatory documents accurately
          </Typography>
        </Box>
      </Paper>

      {/* Data Freshness */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Data Freshness
        </Typography>
        <Typography variant="body1" paragraph>
          Canon regularly updates its data from FDA sources:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1">
            Drug labels: Updated daily
          </Typography>
          <Typography component="li" variant="body1">
            Approval data: Updated weekly
          </Typography>
          <Typography component="li" variant="body1">
            Adverse event reports: Updated quarterly (as FDA releases new FAERS data)
          </Typography>
        </Box>
        <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
          Always verify critical information against FDA.gov for the most current official data.
        </Typography>
      </Paper>
    </Box>
  );
}
