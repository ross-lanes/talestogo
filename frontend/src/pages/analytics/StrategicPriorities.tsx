import { Box, Typography, Paper, CircularProgress, Alert, Chip, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  Security,
  Campaign,
  Psychology,
  Group,
  CheckCircle
} from '@mui/icons-material';
import { api } from '../../services/api';

export default function StrategicPriorities() {
  const { data: dashboard, isLoading: loadingDash } = useQuery({
    queryKey: ['dashboard-priorities'],
    queryFn: async () => {
      const response = await api.get('/api/analytics/dashboard');
      return response.data;
    },
  });

  const { data: sentiment } = useQuery({
    queryKey: ['sentiment-priorities'],
    queryFn: async () => {
      const response = await api.get('/api/analytics/sentiment/breakdown');
      return response.data;
    },
  });

  const { data: positioning } = useQuery({
    queryKey: ['positioning-priorities'],
    queryFn: async () => {
      const response = await api.get('/api/analytics/positioning/breakdown');
      return response.data;
    },
  });

  const { data: shareOfVoice } = useQuery({
    queryKey: ['sov-priorities'],
    queryFn: async () => {
      const response = await api.get('/api/analytics/share-of-voice');
      return response.data;
    },
  });

  if (loadingDash) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Generate strategic priorities based on data
  const priorities = [];

  // Priority 1: Improve mention rate if low
  const mentionRate = dashboard?.mention_rate || 0;
  if (mentionRate < 50) {
    priorities.push({
      title: 'Increase Brand Visibility',
      description: `Your brand is only mentioned in ${Math.round(mentionRate)}% of AI responses. Focus on increasing your digital footprint and thought leadership to improve visibility.`,
      icon: TrendingUp,
      color: '#f44336',
      priority: 'High',
      actions: [
        'Increase content marketing efforts',
        'Publish more thought leadership articles',
        'Engage in industry forums and communities',
        'Optimize website SEO for AI crawlers'
      ]
    });
  }

  // Priority 2: Address negative sentiment
  const negativeSentiment = sentiment?.breakdown?.['Negative'] || 0 + sentiment?.breakdown?.['Very Negative'] || 0;
  if (negativeSentiment > 20) {
    priorities.push({
      title: 'Address Negative Sentiment',
      description: `${negativeSentiment} responses contain negative sentiment. Address pain points and improve customer perception.`,
      icon: Psychology,
      color: '#9FA8DA',  // Purple from extended palette
      priority: 'High',
      actions: [
        'Identify common negative themes',
        'Address customer pain points',
        'Improve product/service quality',
        'Enhance customer support',
        'Launch positive PR campaigns'
      ]
    });
  }

  // Priority 3: Improve positioning
  const leaderPosition = positioning?.breakdown?.['Leader'] || 0;
  const total = positioning?.total || 1;
  const leaderPercentage = (leaderPosition / total) * 100;
  if (leaderPercentage < 30) {
    priorities.push({
      title: 'Strengthen Market Leadership Position',
      description: `You're only positioned as a leader in ${Math.round(leaderPercentage)}% of mentions. Work on establishing stronger thought leadership.`,
      icon: Security,
      color: '#2196f3',
      priority: 'Medium',
      actions: [
        'Publish industry research and whitepapers',
        'Speak at industry conferences',
        'Win industry awards and recognition',
        'Build strategic partnerships',
        'Showcase customer success stories'
      ]
    });
  }

  // Priority 4: Increase share of voice
  const brandSov = shareOfVoice?.find((item: any) => item.is_brand)?.share_of_voice || 0;
  if (brandSov < 40) {
    priorities.push({
      title: 'Increase Share of Voice',
      description: `Your share of voice is ${Math.round(brandSov)}%. Competitors are dominating the conversation. Increase your presence in key channels.`,
      icon: Campaign,
      color: '#9c27b0',
      priority: 'High',
      actions: [
        'Increase social media presence',
        'Launch targeted PR campaigns',
        'Create more shareable content',
        'Engage with industry influencers',
        'Participate in podcast interviews'
      ]
    });
  }

  // Priority 5: Build community
  priorities.push({
    title: 'Build Stronger Community Engagement',
    description: 'Foster a loyal community around your brand to increase organic mentions and positive sentiment.',
    icon: Group,
    color: '#4caf50',
    priority: 'Medium',
    actions: [
      'Launch a user community or forum',
      'Create a brand ambassador program',
      'Host virtual events and webinars',
      'Encourage user-generated content',
      'Build active social media communities'
    ]
  });

  // Sort by priority
  const priorityOrder = { 'High': 0, 'Medium': 1, 'Low': 2 };
  priorities.sort((a, b) => priorityOrder[a.priority as keyof typeof priorityOrder] - priorityOrder[b.priority as keyof typeof priorityOrder]);

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Strategic Priorities
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Data-driven recommendations to improve your brand's performance in AI responses.
      </Typography>

      {/* Summary */}
      <Paper sx={{ p: 4, mb: 4, backgroundColor: '#003e60', color: 'white' }}>
        <Typography variant="body1">
          TALES has identified {priorities.length} strategic priorities to improve your brand's AI visibility and sentiment.
        </Typography>
      </Paper>

      {/* Priorities List */}
      {priorities.map((priority, index) => (
        <Paper key={index} sx={{ p: 4, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <Box
              sx={{
                backgroundColor: priority.color,
                borderRadius: '50%',
                p: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <priority.icon sx={{ color: 'white', fontSize: 32 }} />
            </Box>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Typography variant="h5">{index + 1}. {priority.title}</Typography>
                <Chip
                  label={priority.priority}
                  size="small"
                  sx={{
                    backgroundColor: priority.priority === 'High' ? '#EA4A4A' : '#9FA8DA',
                    color: 'white'
                  }}
                />
              </Box>
              <Typography variant="body1" color="text.secondary" paragraph>
                {priority.description}
              </Typography>

              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                Recommended Actions:
              </Typography>
              <List dense>
                {priority.actions.map((action, actionIndex) => (
                  <ListItem key={actionIndex}>
                    <ListItemIcon>
                      <CheckCircle sx={{ color: priority.color }} />
                    </ListItemIcon>
                    <ListItemText primary={action} />
                  </ListItem>
                ))}
              </List>
            </Box>
          </Box>
        </Paper>
      ))}
    </Box>
  );
}
