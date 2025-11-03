"""
Centralized analytics calculation and caching service.

This module calculates all analytics metrics once and caches them, preventing
redundant calculations across different endpoints (dashboard, analysis pages, reports).
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from typing import Dict, List, Any, Optional, Tuple
import datetime
from datetime import timedelta
from .. import models
from . import metrics


class AnalyticsCache:
    """
    Centralized analytics calculation service that computes all metrics once
    and provides them to different parts of the application.
    """

    def __init__(self, db: Session, user_id: int, brand_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        self.brand_id = brand_id
        self._cache: Dict[str, Any] = {}
        self._calculated = False

    def _apply_filters(self, query, include_brand_in_query: bool = True):
        """
        Apply user and brand filters to a query.

        Args:
            query: SQLAlchemy query to filter
            include_brand_in_query: If False, exclude queries where brand_in_query=True
        """
        # Apply user and brand filters first
        query = query.filter(models.Response.user_id == self.user_id)
        if self.brand_id:
            query = query.filter(models.Response.brand_id == self.brand_id)

        # Only try to filter by brand_in_query if Query table has data
        if not include_brand_in_query:
            # Check if any queries exist for this user/brand
            query_count = self.db.query(func.count(models.Query.id)).filter(
                models.Query.user_id == self.user_id
            )
            if self.brand_id:
                query_count = query_count.filter(models.Query.brand_id == self.brand_id)

            if query_count.scalar() > 0:
                # Queries exist, so we can filter by brand_in_query
                query = query.join(
                    models.Query,
                    (models.Response.query_id == models.Query.query_id) &
                    (models.Response.user_id == models.Query.user_id) &
                    (models.Response.brand_id == models.Query.brand_id),
                    isouter=False  # INNER JOIN
                ).filter(
                    models.Query.brand_in_query == False
                )
            # If no queries exist, don't filter - show all responses

        return query

    def calculate_all(self) -> Dict[str, Any]:
        """
        Calculate all analytics metrics at once and cache the results.

        Returns a comprehensive dictionary containing:
        - Basic counts (total responses, mentions, etc.)
        - Mention metrics (rate, trend, positioning breakdown)
        - Sentiment metrics (breakdown, positive rate, etc.)
        - Descriptor metrics (match rate, top performers)
        - Share of voice metrics
        - Competitive metrics
        - Trend data (30-day trends)
        """
        if self._calculated:
            return self._cache

        # Calculate all base counts
        self._calculate_base_counts()

        # Calculate mention metrics
        self._calculate_mention_metrics()

        # Calculate sentiment metrics
        self._calculate_sentiment_metrics()

        # Calculate descriptor metrics
        self._calculate_descriptor_metrics()

        # Calculate share of voice
        self._calculate_share_of_voice()

        # Calculate positioning breakdown
        self._calculate_positioning_breakdown()

        # Calculate trend data
        self._calculate_trends()

        self._calculated = True
        return self._cache

    def _calculate_base_counts(self):
        """Calculate base counts that are used across multiple metrics."""
        # Total responses (excluding brand_in_query for mention-based metrics)
        self._cache['total_responses_for_mentions'] = self._apply_filters(
            self.db.query(func.count(models.Response.id)),
            include_brand_in_query=False
        ).scalar() or 0

        # Total responses (including all for sentiment/descriptor metrics)
        self._cache['total_responses_all'] = self._apply_filters(
            self.db.query(func.count(models.Response.id)),
            include_brand_in_query=True
        ).scalar() or 0

        # Total mentions (excluding brand_in_query)
        self._cache['total_mentions_for_positioning'] = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            ),
            include_brand_in_query=False
        ).scalar() or 0

        # Total mentions (including all)
        self._cache['total_mentions_all'] = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            ),
            include_brand_in_query=True
        ).scalar() or 0

    def _calculate_mention_metrics(self):
        """Calculate mention-related metrics (excludes brand_in_query)."""
        total = self._cache['total_responses_for_mentions']
        mentions = self._cache['total_mentions_for_positioning']

        self._cache['mention_rate'] = (mentions / total * 100) if total > 0 else 0.0
        self._cache['mention_count'] = mentions

    def _calculate_sentiment_metrics(self):
        """Calculate sentiment metrics (includes all responses)."""
        # Positive sentiment count
        positive_count = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                and_(
                    models.Response.brand_mentioned == 'Yes',
                    models.Response.sentiment.in_(['Very Positive', 'Positive'])
                )
            ),
            include_brand_in_query=True
        ).scalar() or 0

        # Sentiment breakdown (only for direct mentions)
        sentiment_breakdown = self._apply_filters(
            self.db.query(
                models.Response.sentiment,
                func.count(models.Response.id).label('count')
            ).filter(
                models.Response.brand_mentioned == 'Yes'
            ).group_by(models.Response.sentiment),
            include_brand_in_query=True
        ).all()

        total_mentions = self._cache['total_mentions_all']

        self._cache['positive_sentiment_rate'] = (positive_count / total_mentions * 100) if total_mentions > 0 else 0.0
        self._cache['positive_sentiment_count'] = positive_count
        self._cache['sentiment_breakdown'] = {
            sentiment: count for sentiment, count in sentiment_breakdown if sentiment
        }

    def _calculate_descriptor_metrics(self):
        """Calculate descriptor match metrics (includes all responses)."""
        # Get target descriptors
        target_descriptors_query = self.db.query(models.TargetDescriptor).filter(
            models.TargetDescriptor.user_id == self.user_id,
            models.TargetDescriptor.is_target == True
        )
        if self.brand_id:
            target_descriptors_query = target_descriptors_query.filter(
                models.TargetDescriptor.brand_id == self.brand_id
            )

        target_descriptors = target_descriptors_query.all()
        total_target_descriptors = len(target_descriptors)

        # Get responses with mentions
        responses_with_mentions = self._apply_filters(
            self.db.query(models.Response).filter(
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            ),
            include_brand_in_query=True
        ).all()

        # Count descriptor matches
        matched_descriptors = set()
        descriptor_counts: Dict[str, int] = {}

        for response in responses_with_mentions:
            if response.descriptors:
                response_descriptors = [d.strip().lower() for d in response.descriptors.split(',')]
                for target_desc in target_descriptors:
                    target_lower = target_desc.descriptor.lower()
                    if any(target_lower in resp_desc or resp_desc in target_lower
                           for resp_desc in response_descriptors):
                        matched_descriptors.add(target_desc.descriptor)
                        descriptor_counts[target_desc.descriptor] = descriptor_counts.get(
                            target_desc.descriptor, 0
                        ) + 1

        # Calculate match rate
        descriptor_match_rate = (len(matched_descriptors) / total_target_descriptors * 100) if total_target_descriptors > 0 else 0.0

        # Top descriptors
        top_descriptors = sorted(
            [{'descriptor': k, 'count': v, 'match_rate': (v / len(responses_with_mentions) * 100) if responses_with_mentions else 0}
             for k, v in descriptor_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]

        self._cache['descriptor_match_rate'] = descriptor_match_rate
        self._cache['matched_descriptors_count'] = len(matched_descriptors)
        self._cache['total_target_descriptors'] = total_target_descriptors
        self._cache['top_descriptors'] = top_descriptors
        self._cache['descriptor_counts'] = descriptor_counts

    def _calculate_share_of_voice(self):
        """Calculate share of voice metrics (excludes brand_in_query)."""
        # Get brand name
        brand = self.db.query(models.BrandInfo).filter(
            models.BrandInfo.user_id == self.user_id
        )
        if self.brand_id:
            brand = brand.filter(models.BrandInfo.id == self.brand_id)
        brand = brand.first()

        brand_name = brand.brand_name if brand else "Your Brand"

        # Get all responses with mentions
        responses_with_mentions = self._apply_filters(
            self.db.query(models.Response).filter(
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            ),
            include_brand_in_query=False
        ).all()

        # Count mentions per organization AND track positioning
        org_counts: Dict[str, int] = {brand_name: len(responses_with_mentions)}
        org_leader_counts: Dict[str, int] = {}
        org_top3_counts: Dict[str, int] = {}

        # Count brand's leadership positions
        brand_leader = sum(1 for r in responses_with_mentions if r.brand_position == 'Leader')
        brand_top3 = sum(1 for r in responses_with_mentions if r.brand_position == 'Top 3')
        org_leader_counts[brand_name] = brand_leader
        org_top3_counts[brand_name] = brand_top3

        # Parse competitors from responses
        for response in responses_with_mentions:
            if response.competitors:
                competitors = [c.strip() for c in response.competitors.split(',')]
                for competitor in competitors:
                    if competitor and competitor != brand_name:
                        org_counts[competitor] = org_counts.get(competitor, 0) + 1
                        # Note: We can't track competitor positioning from current data structure
                        # They're just mentioned, not positioned
                        if competitor not in org_leader_counts:
                            org_leader_counts[competitor] = 0
                            org_top3_counts[competitor] = 0

        # Calculate total mentions (brand + competitors)
        total_mentions = sum(org_counts.values())

        # Build share of voice list with leadership visibility
        sov_list = []
        for org, count in org_counts.items():
            is_brand = (org == brand_name)
            leader_count = org_leader_counts.get(org, 0)
            top3_count = org_top3_counts.get(org, 0)

            # Leadership visibility: only calculate for brand using centralized function
            if is_brand:
                # Get all responses and queries for centralized calculation
                all_responses_obj = self._apply_filters(
                    self.db.query(models.Response),
                    include_brand_in_query=True
                ).all()
                all_queries_obj = self.db.query(models.Query).filter(
                    models.Query.brand_id == self.brand_id
                ).all()
                leadership_visibility = metrics.calculate_leadership_visibility(all_responses_obj, all_queries_obj)
            else:
                # Not tracked for competitors
                leadership_visibility = 0.0

            sov_list.append({
                'organization': org,
                'mention_count': count,
                'total_mentions': count,  # Alias for frontend compatibility
                'percentage': (count / total_mentions * 100) if total_mentions > 0 else 0.0,
                'share_of_voice': (count / total_mentions * 100) if total_mentions > 0 else 0.0,  # Alias
                'leadership_visibility': leadership_visibility,
                'leader_count': leader_count,
                'top3_count': top3_count,
                'is_brand': is_brand
            })

        sov_list.sort(key=lambda x: x['percentage'], reverse=True)

        # Brand's share of voice
        brand_sov = next((item['percentage'] for item in sov_list if item['organization'] == brand_name), 0.0)

        self._cache['share_of_voice'] = brand_sov
        self._cache['share_of_voice_breakdown'] = sov_list

    def _calculate_positioning_breakdown(self):
        """Calculate positioning breakdown (excludes brand_in_query)."""
        positioning_data = self._apply_filters(
            self.db.query(
                models.Response.brand_position,
                func.count(models.Response.id).label('count')
            ).filter(
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            ).group_by(models.Response.brand_position),
            include_brand_in_query=False
        ).all()

        positioning_breakdown = {position: count for position, count in positioning_data if position}

        # Most common positioning
        leading_position = max(positioning_breakdown.items(), key=lambda x: x[1])[0] if positioning_breakdown else "N/A"

        self._cache['positioning_breakdown'] = positioning_breakdown
        self._cache['leading_position'] = leading_position

    def _calculate_trends(self):
        """Calculate 30-day trend data."""
        end_date = datetime.datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        mid_date = end_date - timedelta(days=15)

        # Recent period (last 15 days) - excluding brand_in_query
        recent_responses = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.timestamp >= mid_date
            ),
            include_brand_in_query=False
        ).scalar() or 0

        recent_mentions = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.timestamp >= mid_date,
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            ),
            include_brand_in_query=False
        ).scalar() or 0

        # Previous period (15-30 days ago) - excluding brand_in_query
        prev_responses = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.timestamp >= start_date,
                models.Response.timestamp < mid_date
            ),
            include_brand_in_query=False
        ).scalar() or 0

        prev_mentions = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.timestamp >= start_date,
                models.Response.timestamp < mid_date,
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            ),
            include_brand_in_query=False
        ).scalar() or 0

        # Calculate mention rate change
        recent_mention_rate = (recent_mentions / recent_responses * 100) if recent_responses > 0 else 0.0
        prev_mention_rate = (prev_mentions / prev_responses * 100) if prev_responses > 0 else 0.0
        mention_rate_change = recent_mention_rate - prev_mention_rate

        # Sentiment trends (including all responses)
        recent_positive = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.timestamp >= mid_date,
                models.Response.brand_mentioned == 'Yes',
                models.Response.sentiment.in_(['Very Positive', 'Positive'])
            ),
            include_brand_in_query=True
        ).scalar() or 0

        recent_mentions_all = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.timestamp >= mid_date,
                models.Response.brand_mentioned == 'Yes'
            ),
            include_brand_in_query=True
        ).scalar() or 0

        prev_positive = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.timestamp >= start_date,
                models.Response.timestamp < mid_date,
                models.Response.brand_mentioned == 'Yes',
                models.Response.sentiment.in_(['Very Positive', 'Positive'])
            ),
            include_brand_in_query=True
        ).scalar() or 0

        prev_mentions_all = self._apply_filters(
            self.db.query(func.count(models.Response.id)).filter(
                models.Response.timestamp >= start_date,
                models.Response.timestamp < mid_date,
                models.Response.brand_mentioned == 'Yes'
            ),
            include_brand_in_query=True
        ).scalar() or 0

        recent_sentiment_rate = (recent_positive / recent_mentions_all * 100) if recent_mentions_all > 0 else 0.0
        prev_sentiment_rate = (prev_positive / prev_mentions_all * 100) if prev_mentions_all > 0 else 0.0
        sentiment_change = recent_sentiment_rate - prev_sentiment_rate

        self._cache['trends'] = {
            'mention_rate_change': round(mention_rate_change, 2),
            'sentiment_change': round(sentiment_change, 2),
            'descriptor_change': 0.0  # Can be calculated if needed
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data specifically formatted for the dashboard."""
        if not self._calculated:
            self.calculate_all()

        return {
            'mention_rate': round(self._cache.get('mention_rate', 0), 2),
            'mention_count': self._cache.get('mention_count', 0),
            'total_responses': self._cache.get('total_responses_for_mentions', 0),
            'positive_sentiment': round(self._cache.get('positive_sentiment_rate', 0), 2),
            'descriptor_match': round(self._cache.get('descriptor_match_rate', 0), 2),
            'share_of_voice': round(self._cache.get('share_of_voice', 0), 2),
            'change_mention_rate': self._cache.get('trends', {}).get('mention_rate_change', 0),
            'change_sentiment': self._cache.get('trends', {}).get('sentiment_change', 0),
            'change_descriptor': self._cache.get('trends', {}).get('descriptor_change', 0),
            'leading_position': self._cache.get('leading_position', 'N/A')
        }

    def get_sentiment_data(self) -> Dict[str, Any]:
        """Get data specifically formatted for sentiment analysis page."""
        if not self._calculated:
            self.calculate_all()

        breakdown = self._cache.get('sentiment_breakdown', {})
        total = sum(breakdown.values())

        # Get negative statements for detailed review
        negative_responses = self._apply_filters(
            self.db.query(models.Response).filter(
                models.Response.brand_mentioned == 'Yes',
                models.Response.sentiment.in_(['Negative', 'Very Negative'])
            ),
            include_brand_in_query=True
        ).all()

        negative_statements = [
            {
                'query': resp.query_text or 'Unknown',
                'platform': resp.platform,
                'text': resp.response_text
            }
            for resp in negative_responses
        ]

        # Generate insights for each sentiment category
        sentiment_insights = {}
        for sentiment_name, count in breakdown.items():
            percentage = round((count / total * 100) if total > 0 else 0, 1)

            # Create contextual insights based on sentiment type and percentage
            if sentiment_name == 'Very Positive':
                if percentage > 30:
                    insight = f"Strong positive sentiment: {count} mentions ({percentage}%) show your brand is being described in highly favorable terms. This indicates strong brand reputation."
                elif percentage > 10:
                    insight = f"Good positive sentiment: {count} mentions ({percentage}%) are very positive. Continue reinforcing the narratives that generate this strong response."
                else:
                    insight = f"{count} mentions ({percentage}%) are very positive. Consider amplifying the factors that drive this exceptional sentiment."

            elif sentiment_name == 'Positive':
                if percentage > 40:
                    insight = f"Dominant positive sentiment: {count} mentions ({percentage}%) are positive. Your brand messaging is resonating well."
                elif percentage > 20:
                    insight = f"Healthy positive sentiment: {count} mentions ({percentage}%) show favorable brand perception."
                else:
                    insight = f"{count} mentions ({percentage}%) are positive. Opportunity to increase positive sentiment through targeted messaging."

            elif sentiment_name == 'Neutral':
                if percentage > 50:
                    insight = f"High neutral sentiment: {count} mentions ({percentage}%) are neutral. This suggests opportunities to strengthen brand differentiation and emotional connection."
                elif percentage > 30:
                    insight = f"Moderate neutral sentiment: {count} mentions ({percentage}%). Consider emphasizing unique value propositions to shift sentiment more positive."
                else:
                    insight = f"{count} mentions ({percentage}%) are neutral. Relatively low neutral sentiment suggests clear brand perception."

            elif sentiment_name == 'Mixed':
                if percentage > 20:
                    insight = f"High mixed sentiment: {count} mentions ({percentage}%) contain both positive and negative elements. Review these for nuanced brand positioning opportunities."
                else:
                    insight = f"{count} mentions ({percentage}%) show mixed sentiment, indicating both strengths and areas for improvement are being recognized."

            elif sentiment_name == 'Negative':
                if percentage > 15:
                    insight = f"Concerning negative sentiment: {count} mentions ({percentage}%) are negative. Priority action needed to address perception issues. Review negative statements below for specific concerns."
                elif percentage > 5:
                    insight = f"Moderate negative sentiment: {count} mentions ({percentage}%). Monitor and address the specific issues mentioned in these responses."
                else:
                    insight = f"Low negative sentiment: {count} mentions ({percentage}%). While concerning, this represents a small portion of overall mentions."

            elif sentiment_name == 'Very Negative':
                if count > 0:
                    insight = f"Critical: {count} mentions ({percentage}%) are very negative. Immediate attention required. Review these statements to identify and address serious perception issues."
                else:
                    insight = "No very negative mentions detected."
            else:
                insight = f"{count} mentions ({percentage}%)"

            # Use lowercase with underscores for the key (matching frontend expectations)
            key = sentiment_name.lower().replace(' ', '_')
            sentiment_insights[key] = insight

        return {
            'positive_rate': round(self._cache.get('positive_sentiment_rate', 0), 2),
            'breakdown': breakdown,
            'total_mentions': self._cache.get('total_mentions_all', 0),
            # Total count
            'total': total,
            # Raw counts (for SentimentAnalysis.tsx)
            'very_positive': breakdown.get('Very Positive', 0),
            'positive': breakdown.get('Positive', 0),
            'neutral': breakdown.get('Neutral', 0),
            'mixed': breakdown.get('Mixed', 0),
            'negative': breakdown.get('Negative', 0),
            'very_negative': breakdown.get('Very Negative', 0),
            # Percentage fields (for Dashboard.tsx)
            'very_positive_pct': round((breakdown.get('Very Positive', 0) / total * 100) if total > 0 else 0, 2),
            'positive_pct': round((breakdown.get('Positive', 0) / total * 100) if total > 0 else 0, 2),
            'neutral_pct': round((breakdown.get('Neutral', 0) / total * 100) if total > 0 else 0, 2),
            'mixed_pct': round((breakdown.get('Mixed', 0) / total * 100) if total > 0 else 0, 2),
            'negative_pct': round((breakdown.get('Negative', 0) / total * 100) if total > 0 else 0, 2),
            'very_negative_pct': round((breakdown.get('Very Negative', 0) / total * 100) if total > 0 else 0, 2),
            # Additional data for Sentiment Analysis page
            'sentiment_insights': sentiment_insights,
            'negative_statements': negative_statements,
        }

    def get_descriptor_data(self) -> List[Dict[str, Any]]:
        """Get data specifically formatted for descriptor performance page."""
        if not self._calculated:
            self.calculate_all()

        return self._cache.get('top_descriptors', [])

    def get_share_of_voice_data(self) -> List[Dict[str, Any]]:
        """Get data specifically formatted for share of voice page."""
        if not self._calculated:
            self.calculate_all()

        return self._cache.get('share_of_voice_breakdown', [])

    def get_positioning_data(self) -> Dict[str, Any]:
        """Get data specifically formatted for positioning breakdown page."""
        if not self._calculated:
            self.calculate_all()

        breakdown = self._cache.get('positioning_breakdown', {})
        total = sum(breakdown.values())

        # Return format expected by dashboard
        return {
            'total': total,
            'leader': breakdown.get('Leader', 0),
            'top_3': breakdown.get('Top 3', 0),
            'featured': breakdown.get('Featured', 0),
            'listed': breakdown.get('Listed', 0),
            'not_mentioned': breakdown.get('Not Mentioned', 0),
            # Also include the detailed breakdown for other pages
            'breakdown': {
                position: {
                    'count': count,
                    'percentage': round((count / total * 100) if total > 0 else 0, 2)
                }
                for position, count in breakdown.items()
            }
        }

    def invalidate(self):
        """Clear the cache to force recalculation."""
        self._cache = {}
        self._calculated = False
