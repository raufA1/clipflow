#!/usr/bin/env python3
"""
Comprehensive Metrics Collection and Analytics System
Tracks performance across all platforms with advanced analytics
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import csv
import sqlite3
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class ContentMetrics:
    """Comprehensive content performance metrics"""
    content_id: str
    user_id: int
    platform: str
    content_type: str  # video, image, text, carousel
    post_id: str
    post_url: str
    published_at: str
    
    # Engagement metrics
    views: int = 0
    impressions: int = 0
    reach: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    
    # Time-based metrics
    engagement_rate: float = 0.0
    ctr: float = 0.0  # Click-through rate
    completion_rate: float = 0.0  # For videos
    watch_time: int = 0  # Total watch time in seconds
    
    # Publishing details
    publish_hour: int = 0
    publish_day_of_week: int = 0
    caption_length: int = 0
    hashtag_count: int = 0
    
    # Content details
    duration: float = 0.0  # For videos
    file_size: int = 0
    aspect_ratio: str = ""
    
    # Metadata
    collected_at: str = ""
    last_updated: str = ""

@dataclass
class PlatformSummary:
    """Platform performance summary"""
    platform: str
    total_posts: int
    total_views: int
    total_engagement: int
    avg_engagement_rate: float
    best_performing_post: str
    worst_performing_post: str
    best_posting_hours: List[int]
    trending_hashtags: List[str]

@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    user_id: int
    report_period: str
    generated_at: str
    
    platform_summaries: List[PlatformSummary]
    top_performers: List[ContentMetrics]
    growth_metrics: Dict[str, float]
    recommendations: List[str]
    
    # Cross-platform insights
    best_platforms: List[str]
    optimal_posting_times: Dict[str, List[int]]
    content_type_performance: Dict[str, float]

class MetricsCollector:
    """Collects and stores performance metrics from all platforms"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "metrics.db"
        self.exports_dir = self.data_dir / "exports"
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        asyncio.create_task(self._init_database())
    
    async def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Content metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    post_url TEXT,
                    published_at TEXT NOT NULL,
                    views INTEGER DEFAULT 0,
                    impressions INTEGER DEFAULT 0,
                    reach INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    saves INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    engagement_rate REAL DEFAULT 0.0,
                    ctr REAL DEFAULT 0.0,
                    completion_rate REAL DEFAULT 0.0,
                    watch_time INTEGER DEFAULT 0,
                    publish_hour INTEGER DEFAULT 0,
                    publish_day_of_week INTEGER DEFAULT 0,
                    caption_length INTEGER DEFAULT 0,
                    hashtag_count INTEGER DEFAULT 0,
                    duration REAL DEFAULT 0.0,
                    file_size INTEGER DEFAULT 0,
                    aspect_ratio TEXT DEFAULT "",
                    collected_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    UNIQUE(content_id, platform)
                )
            ''')
            
            # Platform summaries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS platform_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    date TEXT NOT NULL,
                    total_posts INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    total_engagement INTEGER DEFAULT 0,
                    avg_engagement_rate REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, platform, date)
                )
            ''')
            
            # Growth tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS growth_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Metrics database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    async def store_metrics(self, metrics: ContentMetrics):
        """Store content metrics in database"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate engagement rate
            total_engagement = metrics.likes + metrics.comments + metrics.shares + metrics.saves
            metrics.engagement_rate = total_engagement / max(metrics.views, 1)
            
            # Calculate CTR
            if metrics.impressions > 0:
                metrics.ctr = metrics.clicks / metrics.impressions
            
            # Set timestamps
            now = datetime.now(timezone.utc).isoformat()
            if not metrics.collected_at:
                metrics.collected_at = now
            metrics.last_updated = now
            
            # Insert or update metrics
            cursor.execute('''
                INSERT OR REPLACE INTO content_metrics
                (content_id, user_id, platform, content_type, post_id, post_url, published_at,
                 views, impressions, reach, likes, comments, shares, saves, clicks,
                 engagement_rate, ctr, completion_rate, watch_time,
                 publish_hour, publish_day_of_week, caption_length, hashtag_count,
                 duration, file_size, aspect_ratio, collected_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.content_id, metrics.user_id, metrics.platform, metrics.content_type,
                metrics.post_id, metrics.post_url, metrics.published_at,
                metrics.views, metrics.impressions, metrics.reach, metrics.likes,
                metrics.comments, metrics.shares, metrics.saves, metrics.clicks,
                metrics.engagement_rate, metrics.ctr, metrics.completion_rate, metrics.watch_time,
                metrics.publish_hour, metrics.publish_day_of_week, metrics.caption_length,
                metrics.hashtag_count, metrics.duration, metrics.file_size, metrics.aspect_ratio,
                metrics.collected_at, metrics.last_updated
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored metrics for {metrics.platform} post {metrics.post_id}")
            
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
    
    async def batch_store_metrics(self, metrics_list: List[ContentMetrics]):
        """Store multiple metrics efficiently"""
        
        for metrics in metrics_list:
            await self.store_metrics(metrics)
        
        logger.info(f"Batch stored {len(metrics_list)} metrics")
    
    async def get_content_metrics(self, user_id: int, platform: str = None,
                                 start_date: str = None, end_date: str = None,
                                 limit: int = 100) -> List[ContentMetrics]:
        """Retrieve content metrics with filters"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM content_metrics WHERE user_id = ?"
            params = [user_id]
            
            if platform:
                query += " AND platform = ?"
                params.append(platform)
            
            if start_date:
                query += " AND published_at >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND published_at <= ?"
                params.append(end_date)
            
            query += " ORDER BY published_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to ContentMetrics objects
            metrics_list = []
            for row in rows:
                metrics = ContentMetrics(
                    content_id=row["content_id"],
                    user_id=row["user_id"],
                    platform=row["platform"],
                    content_type=row["content_type"],
                    post_id=row["post_id"],
                    post_url=row["post_url"],
                    published_at=row["published_at"],
                    views=row["views"],
                    impressions=row["impressions"],
                    reach=row["reach"],
                    likes=row["likes"],
                    comments=row["comments"],
                    shares=row["shares"],
                    saves=row["saves"],
                    clicks=row["clicks"],
                    engagement_rate=row["engagement_rate"],
                    ctr=row["ctr"],
                    completion_rate=row["completion_rate"],
                    watch_time=row["watch_time"],
                    publish_hour=row["publish_hour"],
                    publish_day_of_week=row["publish_day_of_week"],
                    caption_length=row["caption_length"],
                    hashtag_count=row["hashtag_count"],
                    duration=row["duration"],
                    file_size=row["file_size"],
                    aspect_ratio=row["aspect_ratio"],
                    collected_at=row["collected_at"],
                    last_updated=row["last_updated"]
                )
                metrics_list.append(metrics)
            
            return metrics_list
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            return []
    
    async def get_platform_summary(self, user_id: int, platform: str,
                                  days: int = 30) -> PlatformSummary:
        """Get platform performance summary"""
        
        # Get metrics for the specified period
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        metrics = await self.get_content_metrics(
            user_id, platform, 
            start_date.isoformat(), 
            end_date.isoformat(),
            limit=1000
        )
        
        if not metrics:
            return PlatformSummary(
                platform=platform,
                total_posts=0,
                total_views=0,
                total_engagement=0,
                avg_engagement_rate=0.0,
                best_performing_post="",
                worst_performing_post="",
                best_posting_hours=[],
                trending_hashtags=[]
            )
        
        # Calculate summary statistics
        total_posts = len(metrics)
        total_views = sum(m.views for m in metrics)
        total_engagement = sum(m.likes + m.comments + m.shares + m.saves for m in metrics)
        avg_engagement_rate = statistics.mean(m.engagement_rate for m in metrics)
        
        # Find best and worst performing posts
        best_post = max(metrics, key=lambda m: m.engagement_rate)
        worst_post = min(metrics, key=lambda m: m.engagement_rate)
        
        # Find best posting hours
        hour_performance = defaultdict(list)
        for m in metrics:
            hour_performance[m.publish_hour].append(m.engagement_rate)
        
        avg_hour_performance = {
            hour: statistics.mean(rates)
            for hour, rates in hour_performance.items()
        }
        
        best_hours = sorted(avg_hour_performance.items(), key=lambda x: x[1], reverse=True)[:3]
        best_posting_hours = [hour for hour, _ in best_hours]
        
        # Analyze hashtag trends (simplified)
        hashtag_performance = defaultdict(list)
        trending_hashtags = ["trending1", "trending2", "trending3"]  # Placeholder
        
        return PlatformSummary(
            platform=platform,
            total_posts=total_posts,
            total_views=total_views,
            total_engagement=total_engagement,
            avg_engagement_rate=avg_engagement_rate,
            best_performing_post=best_post.post_id,
            worst_performing_post=worst_post.post_id,
            best_posting_hours=best_posting_hours,
            trending_hashtags=trending_hashtags
        )
    
    async def generate_performance_report(self, user_id: int, days: int = 30) -> PerformanceReport:
        """Generate comprehensive performance report"""
        
        platforms = await self._get_user_platforms(user_id)
        platform_summaries = []
        
        # Get summaries for each platform
        for platform in platforms:
            summary = await self.get_platform_summary(user_id, platform, days)
            platform_summaries.append(summary)
        
        # Get top performers across all platforms
        all_metrics = await self.get_content_metrics(
            user_id, limit=1000,
            start_date=(datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        )
        
        top_performers = sorted(all_metrics, key=lambda m: m.engagement_rate, reverse=True)[:10]
        
        # Calculate growth metrics
        growth_metrics = await self._calculate_growth_metrics(user_id, days)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(user_id, platform_summaries)
        
        # Analyze best platforms
        best_platforms = sorted(
            platform_summaries,
            key=lambda p: p.avg_engagement_rate,
            reverse=True
        )[:3]
        
        best_platform_names = [p.platform for p in best_platforms]
        
        # Optimal posting times
        optimal_times = {}
        for summary in platform_summaries:
            optimal_times[summary.platform] = summary.best_posting_hours
        
        # Content type performance
        content_type_performance = await self._analyze_content_type_performance(all_metrics)
        
        return PerformanceReport(
            user_id=user_id,
            report_period=f"Last {days} days",
            generated_at=datetime.now(timezone.utc).isoformat(),
            platform_summaries=platform_summaries,
            top_performers=top_performers,
            growth_metrics=growth_metrics,
            recommendations=recommendations,
            best_platforms=best_platform_names,
            optimal_posting_times=optimal_times,
            content_type_performance=content_type_performance
        )
    
    async def _get_user_platforms(self, user_id: int) -> List[str]:
        """Get platforms used by user"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT DISTINCT platform FROM content_metrics WHERE user_id = ?",
                (user_id,)
            )
            
            platforms = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return platforms
            
        except Exception as e:
            logger.error(f"Error getting user platforms: {e}")
            return []
    
    async def _calculate_growth_metrics(self, user_id: int, days: int) -> Dict[str, float]:
        """Calculate growth metrics"""
        
        # Get current period metrics
        end_date = datetime.now(timezone.utc)
        current_start = end_date - timedelta(days=days)
        
        current_metrics = await self.get_content_metrics(
            user_id, 
            start_date=current_start.isoformat(),
            end_date=end_date.isoformat(),
            limit=1000
        )
        
        # Get previous period metrics
        previous_start = current_start - timedelta(days=days)
        previous_metrics = await self.get_content_metrics(
            user_id,
            start_date=previous_start.isoformat(), 
            end_date=current_start.isoformat(),
            limit=1000
        )
        
        # Calculate growth rates
        current_views = sum(m.views for m in current_metrics)
        previous_views = sum(m.views for m in previous_metrics) or 1
        
        current_engagement = sum(m.likes + m.comments + m.shares for m in current_metrics)
        previous_engagement = sum(m.likes + m.comments + m.shares for m in previous_metrics) or 1
        
        view_growth = ((current_views - previous_views) / previous_views) * 100
        engagement_growth = ((current_engagement - previous_engagement) / previous_engagement) * 100
        
        return {
            "view_growth_percent": round(view_growth, 2),
            "engagement_growth_percent": round(engagement_growth, 2),
            "current_posts": len(current_metrics),
            "previous_posts": len(previous_metrics),
            "posting_frequency_change": len(current_metrics) - len(previous_metrics)
        }
    
    async def _generate_recommendations(self, user_id: int, summaries: List[PlatformSummary]) -> List[str]:
        """Generate AI-powered recommendations"""
        
        recommendations = []
        
        # Posting time recommendations
        all_best_hours = []
        for summary in summaries:
            all_best_hours.extend(summary.best_posting_hours)
        
        if all_best_hours:
            most_common_hour = max(set(all_best_hours), key=all_best_hours.count)
            recommendations.append(f"Your best posting time is {most_common_hour}:00. Consider scheduling more content at this hour.")
        
        # Platform performance recommendations
        if summaries:
            best_platform = max(summaries, key=lambda s: s.avg_engagement_rate)
            worst_platform = min(summaries, key=lambda s: s.avg_engagement_rate)
            
            if best_platform.avg_engagement_rate > worst_platform.avg_engagement_rate * 2:
                recommendations.append(f"Focus more effort on {best_platform.platform} - it's performing 2x better than {worst_platform.platform}")
        
        # Posting frequency recommendations
        for summary in summaries:
            if summary.total_posts < 7:  # Less than 1 post per day
                recommendations.append(f"Increase posting frequency on {summary.platform} for better visibility")
        
        # Engagement recommendations
        low_engagement_platforms = [s for s in summaries if s.avg_engagement_rate < 0.02]
        for platform in low_engagement_platforms:
            recommendations.append(f"Engagement is low on {platform.platform}. Try more interactive content like polls or questions")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    async def _analyze_content_type_performance(self, metrics: List[ContentMetrics]) -> Dict[str, float]:
        """Analyze performance by content type"""
        
        content_performance = defaultdict(list)
        
        for m in metrics:
            content_performance[m.content_type].append(m.engagement_rate)
        
        return {
            content_type: statistics.mean(rates)
            for content_type, rates in content_performance.items()
        }
    
    async def export_metrics_csv(self, user_id: int, filename: str = None) -> str:
        """Export metrics to CSV"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_export_{timestamp}.csv"
        
        export_path = self.exports_dir / filename
        
        # Get all metrics for user
        metrics = await self.get_content_metrics(user_id, limit=10000)
        
        # Write to CSV
        with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'content_id', 'platform', 'content_type', 'post_id', 'published_at',
                'views', 'likes', 'comments', 'shares', 'saves', 'engagement_rate',
                'publish_hour', 'publish_day_of_week', 'duration'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for m in metrics:
                writer.writerow({
                    'content_id': m.content_id,
                    'platform': m.platform,
                    'content_type': m.content_type,
                    'post_id': m.post_id,
                    'published_at': m.published_at,
                    'views': m.views,
                    'likes': m.likes,
                    'comments': m.comments,
                    'shares': m.shares,
                    'saves': m.saves,
                    'engagement_rate': m.engagement_rate,
                    'publish_hour': m.publish_hour,
                    'publish_day_of_week': m.publish_day_of_week,
                    'duration': m.duration
                })
        
        logger.info(f"Exported {len(metrics)} metrics to {export_path}")
        return str(export_path)
    
    async def export_report_json(self, report: PerformanceReport, filename: str = None) -> str:
        """Export performance report to JSON"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.json"
        
        export_path = self.exports_dir / filename
        
        # Convert to dict (handling dataclasses)
        report_dict = asdict(report)
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported performance report to {export_path}")
        return str(export_path)
    
    async def get_real_time_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get real-time dashboard metrics"""
        
        # Get recent metrics (last 24 hours)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        recent_metrics = await self.get_content_metrics(
            user_id,
            start_date=start_time.isoformat(),
            end_date=end_time.isoformat()
        )
        
        # Calculate real-time stats
        total_views_24h = sum(m.views for m in recent_metrics)
        total_engagement_24h = sum(m.likes + m.comments + m.shares for m in recent_metrics)
        posts_24h = len(recent_metrics)
        
        # Get trending post (best performing in last 24h)
        trending_post = max(recent_metrics, key=lambda m: m.engagement_rate) if recent_metrics else None
        
        return {
            "views_24h": total_views_24h,
            "engagement_24h": total_engagement_24h,
            "posts_24h": posts_24h,
            "avg_engagement_rate_24h": statistics.mean([m.engagement_rate for m in recent_metrics]) if recent_metrics else 0,
            "trending_post": {
                "post_id": trending_post.post_id,
                "platform": trending_post.platform,
                "engagement_rate": trending_post.engagement_rate,
                "views": trending_post.views
            } if trending_post else None,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

# Analytics Dashboard Data Provider
class AnalyticsDashboard:
    """Provides data for analytics dashboard"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    async def get_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Get complete dashboard data"""
        
        # Get performance report for last 30 days
        report = await self.collector.generate_performance_report(user_id, 30)
        
        # Get real-time metrics
        realtime = await self.collector.get_real_time_metrics(user_id)
        
        # Get weekly comparison
        weekly_comparison = await self._get_weekly_comparison(user_id)
        
        # Get platform breakdown
        platform_breakdown = await self._get_platform_breakdown(user_id)
        
        return {
            "user_id": user_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "realtime_metrics": realtime,
            "performance_report": asdict(report),
            "weekly_comparison": weekly_comparison,
            "platform_breakdown": platform_breakdown,
            "recommendations": report.recommendations
        }
    
    async def _get_weekly_comparison(self, user_id: int) -> Dict[str, Any]:
        """Get week-over-week comparison"""
        
        # Current week
        end_date = datetime.now(timezone.utc)
        current_week_start = end_date - timedelta(days=7)
        
        current_week = await self.collector.get_content_metrics(
            user_id,
            start_date=current_week_start.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Previous week  
        previous_week_start = current_week_start - timedelta(days=7)
        previous_week = await self.collector.get_content_metrics(
            user_id,
            start_date=previous_week_start.isoformat(),
            end_date=current_week_start.isoformat()
        )
        
        # Calculate comparison
        current_views = sum(m.views for m in current_week)
        previous_views = sum(m.views for m in previous_week) or 1
        
        current_engagement = sum(m.likes + m.comments for m in current_week)
        previous_engagement = sum(m.likes + m.comments for m in previous_week) or 1
        
        return {
            "views_change_percent": round(((current_views - previous_views) / previous_views) * 100, 2),
            "engagement_change_percent": round(((current_engagement - previous_engagement) / previous_engagement) * 100, 2),
            "posts_this_week": len(current_week),
            "posts_last_week": len(previous_week)
        }
    
    async def _get_platform_breakdown(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """Get detailed platform breakdown"""
        
        platforms = await self.collector._get_user_platforms(user_id)
        breakdown = {}
        
        for platform in platforms:
            metrics = await self.collector.get_content_metrics(user_id, platform, limit=100)
            
            if metrics:
                breakdown[platform] = {
                    "total_posts": len(metrics),
                    "total_views": sum(m.views for m in metrics),
                    "avg_engagement_rate": statistics.mean([m.engagement_rate for m in metrics]),
                    "best_content_type": max(
                        set(m.content_type for m in metrics),
                        key=lambda ct: statistics.mean([m.engagement_rate for m in metrics if m.content_type == ct])
                    ),
                    "recent_performance": [
                        {
                            "date": m.published_at[:10],
                            "engagement_rate": m.engagement_rate,
                            "views": m.views
                        }
                        for m in metrics[:7]  # Last 7 posts
                    ]
                }
        
        return breakdown

# Example usage
async def main():
    collector = MetricsCollector()
    dashboard = AnalyticsDashboard(collector)
    
    # Simulate storing some metrics
    test_metrics = ContentMetrics(
        content_id="test123",
        user_id=12345,
        platform="instagram",
        content_type="video",
        post_id="abc123",
        post_url="https://instagram.com/p/abc123",
        published_at=datetime.now(timezone.utc).isoformat(),
        views=1500,
        likes=45,
        comments=8,
        shares=3,
        saves=12,
        publish_hour=19,
        publish_day_of_week=2,  # Wednesday
        caption_length=120,
        hashtag_count=5,
        duration=30.0
    )
    
    await collector.store_metrics(test_metrics)
    print("✅ Test metrics stored")
    
    # Generate performance report
    report = await collector.generate_performance_report(12345, 30)
    print(f"📊 Generated report for {len(report.platform_summaries)} platforms")
    print(f"   Top performer: {report.top_performers[0].post_id if report.top_performers else 'None'}")
    print(f"   Recommendations: {len(report.recommendations)}")
    
    # Get dashboard data
    dashboard_data = await dashboard.get_dashboard_data(12345)
    print(f"📈 Dashboard data: {list(dashboard_data.keys())}")
    
    # Export to CSV
    csv_path = await collector.export_metrics_csv(12345)
    print(f"💾 Exported to: {csv_path}")

if __name__ == "__main__":
    asyncio.run(main())