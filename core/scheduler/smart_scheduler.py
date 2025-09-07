#!/usr/bin/env python3
"""
Smart AI-Powered Content Scheduler
Optimizes posting times using machine learning and analytics
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import random
import math
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class TimeSlot:
    """Represents a time slot for posting"""
    hour: int
    day_of_week: int  # 0=Monday, 6=Sunday
    platform: str
    score: float = 0.0
    confidence: float = 0.0
    sample_count: int = 0
    last_updated: str = ""

@dataclass
class PostMetrics:
    """Metrics for a published post"""
    post_id: str
    platform: str
    publish_time: datetime
    hour: int
    day_of_week: int
    engagement_rate: float
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    reach: int = 0
    impressions: int = 0

@dataclass
class ScheduleRecommendation:
    """Recommended posting schedule"""
    platform: str
    datetime_utc: datetime
    local_time: str
    score: float
    confidence: float
    reason: str
    alternative_slots: List[Dict[str, Any]] = None

class SmartScheduler:
    """AI-powered content scheduler with learning capabilities"""
    
    def __init__(self, data_dir: str = "data", timezone_str: str = "UTC"):
        self.data_dir = Path(data_dir)
        self.timezone_str = timezone_str
        self.metrics_file = self.data_dir / "scheduling_metrics.json"
        self.slots_file = self.data_dir / "time_slots.json"
        self.user_patterns_file = self.data_dir / "user_patterns.json"
        
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data structures
        self.time_slots: Dict[str, Dict[Tuple[int, int], TimeSlot]] = defaultdict(dict)
        self.user_patterns: Dict[str, Any] = {}
        self.platform_defaults: Dict[str, List[Tuple[int, int]]] = {
            "instagram": [(19, 0), (19, 1), (19, 2), (19, 3), (19, 4)],  # 7PM weekdays
            "youtube": [(20, 6), (20, 0), (15, 6), (15, 0), (18, 2)],    # 8PM Sun/Mon, 3PM Sat/Sun, 6PM Wed  
            "tiktok": [(21, 1), (21, 2), (21, 3), (19, 4), (19, 5)],     # 9PM Tue/Wed/Thu, 7PM Fri/Sat
            "twitter": [(9, 1), (9, 2), (9, 3), (17, 1), (17, 2)],       # 9AM & 5PM weekdays
            "linkedin": [(8, 1), (8, 2), (8, 3), (12, 1), (17, 2)]       # 8AM, 12PM, 5PM business days
        }
        
        # Load existing data
        asyncio.create_task(self._load_data())
    
    async def _load_data(self):
        """Load existing scheduling data"""
        try:
            # Load time slots
            if self.slots_file.exists():
                with open(self.slots_file, 'r') as f:
                    slots_data = json.load(f)
                    for platform, slots in slots_data.items():
                        for slot_key, slot_data in slots.items():
                            hour, dow = eval(slot_key)  # Convert string back to tuple
                            self.time_slots[platform][(hour, dow)] = TimeSlot(**slot_data)
            
            # Load user patterns
            if self.user_patterns_file.exists():
                with open(self.user_patterns_file, 'r') as f:
                    self.user_patterns = json.load(f)
            
            logger.info("Scheduling data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading scheduling data: {e}")
            await self._initialize_default_slots()
    
    async def _initialize_default_slots(self):
        """Initialize with platform default time slots"""
        for platform, default_times in self.platform_defaults.items():
            for hour, dow in default_times:
                slot = TimeSlot(
                    hour=hour,
                    day_of_week=dow,
                    platform=platform,
                    score=0.5,  # Neutral starting score
                    confidence=0.1,  # Low confidence initially
                    sample_count=0,
                    last_updated=datetime.now(timezone.utc).isoformat()
                )
                self.time_slots[platform][(hour, dow)] = slot
        
        await self._save_data()
        logger.info("Initialized default time slots")
    
    async def _save_data(self):
        """Save scheduling data to disk"""
        try:
            # Save time slots
            slots_data = {}
            for platform, slots in self.time_slots.items():
                slots_data[platform] = {}
                for (hour, dow), slot in slots.items():
                    slots_data[platform][str((hour, dow))] = asdict(slot)
            
            with open(self.slots_file, 'w') as f:
                json.dump(slots_data, f, indent=2)
            
            # Save user patterns
            with open(self.user_patterns_file, 'w') as f:
                json.dump(self.user_patterns, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving scheduling data: {e}")
    
    async def get_optimal_time(self, platform: str, content_type: str = "general",
                             exclude_hours: List[int] = None,
                             min_gap_hours: int = 2) -> ScheduleRecommendation:
        """Get optimal posting time for platform"""
        
        exclude_hours = exclude_hours or []
        current_time = datetime.now(timezone.utc)
        
        # Get available slots for the next 7 days
        candidate_slots = await self._get_candidate_slots(
            platform, current_time, exclude_hours, min_gap_hours
        )
        
        if not candidate_slots:
            # Fallback to default times
            return await self._get_fallback_recommendation(platform, current_time)
        
        # Sort by score (highest first)
        candidate_slots.sort(key=lambda x: x["score"], reverse=True)
        best_slot = candidate_slots[0]
        
        # Calculate local time
        local_time = await self._convert_to_local_time(best_slot["datetime"])
        
        # Determine reason
        reason = await self._generate_recommendation_reason(best_slot, platform)
        
        return ScheduleRecommendation(
            platform=platform,
            datetime_utc=best_slot["datetime"],
            local_time=local_time,
            score=best_slot["score"],
            confidence=best_slot["confidence"],
            reason=reason,
            alternative_slots=candidate_slots[1:4]  # Top 3 alternatives
        )
    
    async def get_multi_platform_schedule(self, platforms: List[str],
                                        min_gap_hours: int = 2) -> List[ScheduleRecommendation]:
        """Get optimal schedule across multiple platforms"""
        
        recommendations = []
        used_times = []
        
        # Sort platforms by priority (most restrictive first)
        platform_priority = {"linkedin": 0, "twitter": 1, "instagram": 2, "youtube": 3, "tiktok": 4}
        sorted_platforms = sorted(platforms, key=lambda p: platform_priority.get(p, 999))
        
        for platform in sorted_platforms:
            # Exclude times too close to already scheduled posts
            exclude_hours = []
            for used_time in used_times:
                for hour_offset in range(-min_gap_hours, min_gap_hours + 1):
                    exclude_hour = (used_time.hour + hour_offset) % 24
                    exclude_hours.append(exclude_hour)
            
            recommendation = await self.get_optimal_time(platform, exclude_hours=exclude_hours)
            recommendations.append(recommendation)
            used_times.append(recommendation.datetime_utc)
        
        return recommendations
    
    async def _get_candidate_slots(self, platform: str, start_time: datetime,
                                 exclude_hours: List[int], min_gap_hours: int) -> List[Dict[str, Any]]:
        """Get candidate time slots for the next week"""
        
        candidates = []
        platform_slots = self.time_slots.get(platform, {})
        
        # Look at next 7 days
        for day_offset in range(7):
            target_date = start_time + timedelta(days=day_offset)
            day_of_week = target_date.weekday()
            
            # Check each slot for this day
            for (hour, dow), slot in platform_slots.items():
                if dow != day_of_week:
                    continue
                
                # Skip if in exclude hours
                if hour in exclude_hours:
                    continue
                
                # Create candidate datetime
                candidate_time = target_date.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
                
                # Must be in the future
                if candidate_time <= start_time:
                    continue
                
                # Check minimum gap
                if await self._violates_min_gap(candidate_time, min_gap_hours):
                    continue
                
                # Calculate dynamic score
                dynamic_score = await self._calculate_dynamic_score(slot, candidate_time)
                
                candidates.append({
                    "datetime": candidate_time,
                    "hour": hour,
                    "day_of_week": dow,
                    "score": dynamic_score,
                    "confidence": slot.confidence,
                    "base_slot": slot
                })
        
        return candidates
    
    async def _violates_min_gap(self, candidate_time: datetime, min_gap_hours: int) -> bool:
        """Check if candidate time violates minimum gap with recent posts"""
        
        # In a real implementation, this would check recent post times
        # For now, assume no violations
        return False
    
    async def _calculate_dynamic_score(self, slot: TimeSlot, target_time: datetime) -> float:
        """Calculate dynamic score considering current conditions"""
        
        base_score = slot.score
        
        # Time decay factor (recent performance weighs more)
        if slot.last_updated:
            last_update = datetime.fromisoformat(slot.last_updated)
            days_old = (target_time - last_update).days
            decay_factor = math.exp(-days_old / 30)  # 30-day half-life
        else:
            decay_factor = 0.1
        
        # Confidence boost
        confidence_boost = slot.confidence * 0.2
        
        # Sample size factor (more data = more reliable)
        sample_factor = min(slot.sample_count / 10, 1.0) * 0.1
        
        # Day-specific adjustments
        day_adjustment = await self._get_day_adjustment(target_time)
        
        # Holiday/special event adjustments
        event_adjustment = await self._get_event_adjustment(target_time)
        
        dynamic_score = (
            base_score * decay_factor +
            confidence_boost +
            sample_factor +
            day_adjustment +
            event_adjustment
        )
        
        return min(max(dynamic_score, 0.0), 1.0)  # Clamp between 0 and 1
    
    async def _get_day_adjustment(self, target_time: datetime) -> float:
        """Get adjustment based on day of week/month"""
        
        # Avoid Mondays for most content (-0.1)
        if target_time.weekday() == 0:  # Monday
            return -0.1
        
        # Boost Fridays for casual content (+0.05)
        if target_time.weekday() == 4:  # Friday
            return 0.05
        
        # Avoid first day of month (people busy)
        if target_time.day == 1:
            return -0.05
        
        return 0.0
    
    async def _get_event_adjustment(self, target_time: datetime) -> float:
        """Get adjustment based on holidays/events"""
        
        # This would integrate with holiday APIs or calendars
        # For now, basic weekend adjustment
        
        if target_time.weekday() >= 5:  # Weekend
            return 0.02  # Slight boost for weekend posting
        
        return 0.0
    
    async def _get_fallback_recommendation(self, platform: str, current_time: datetime) -> ScheduleRecommendation:
        """Get fallback recommendation when no optimal slots found"""
        
        # Use platform defaults
        default_times = self.platform_defaults.get(platform, [(12, 1)])  # Default to Tuesday noon
        hour, dow = default_times[0]
        
        # Find next occurrence of this day/hour
        days_ahead = (dow - current_time.weekday()) % 7
        if days_ahead == 0 and current_time.hour >= hour:
            days_ahead = 7
        
        target_time = current_time + timedelta(days=days_ahead)
        target_time = target_time.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        local_time = await self._convert_to_local_time(target_time)
        
        return ScheduleRecommendation(
            platform=platform,
            datetime_utc=target_time,
            local_time=local_time,
            score=0.5,
            confidence=0.1,
            reason=f"Using default {platform} posting time (no historical data available)"
        )
    
    async def _convert_to_local_time(self, utc_time: datetime) -> str:
        """Convert UTC time to local timezone"""
        
        # Simple conversion - in real implementation would use proper timezone handling
        local_hour = (utc_time.hour + 4) % 24  # Assuming +4 UTC (Azerbaijan)
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = day_names[utc_time.weekday()]
        
        time_str = f"{local_hour:02d}:00"
        return f"{day_name} {time_str} (Local Time)"
    
    async def _generate_recommendation_reason(self, slot: Dict[str, Any], platform: str) -> str:
        """Generate human-readable reason for recommendation"""
        
        reasons = []
        
        if slot["score"] > 0.7:
            reasons.append("High historical engagement")
        elif slot["score"] > 0.5:
            reasons.append("Good historical performance")
        else:
            reasons.append("Average performance expected")
        
        if slot["confidence"] > 0.7:
            reasons.append("high confidence")
        elif slot["confidence"] > 0.4:
            reasons.append("medium confidence")
        else:
            reasons.append("low confidence")
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = day_names[slot["day_of_week"]]
        
        reasons.append(f"optimal for {platform} on {day_name}s")
        
        return " • ".join(reasons)
    
    async def record_post_performance(self, metrics: PostMetrics):
        """Record performance data for learning"""
        
        try:
            # Calculate engagement rate
            total_interactions = metrics.likes + metrics.comments + metrics.shares + metrics.saves
            engagement_rate = total_interactions / max(metrics.views, 1)
            
            # Update time slot performance
            slot_key = (metrics.hour, metrics.day_of_week)
            platform = metrics.platform
            
            if platform not in self.time_slots:
                self.time_slots[platform] = {}
            
            if slot_key in self.time_slots[platform]:
                slot = self.time_slots[platform][slot_key]
            else:
                slot = TimeSlot(
                    hour=metrics.hour,
                    day_of_week=metrics.day_of_week,
                    platform=platform,
                    score=0.5,
                    confidence=0.1,
                    sample_count=0
                )
                self.time_slots[platform][slot_key] = slot
            
            # Update slot using exponential moving average
            alpha = min(0.3, 1.0 / (slot.sample_count + 1))  # Learning rate
            slot.score = (1 - alpha) * slot.score + alpha * engagement_rate
            slot.confidence = min(slot.confidence + 0.05, 0.95)  # Gradual confidence increase
            slot.sample_count += 1
            slot.last_updated = datetime.now(timezone.utc).isoformat()
            
            # Save updated data
            await self._save_data()
            
            logger.info(f"Recorded performance for {platform} at {metrics.hour}:00 on day {metrics.day_of_week}")
            
        except Exception as e:
            logger.error(f"Error recording post performance: {e}")
    
    async def get_posting_analytics(self, platform: str = None) -> Dict[str, Any]:
        """Get analytics about posting performance"""
        
        analytics = {
            "total_slots": 0,
            "high_performance_slots": 0,
            "average_score": 0.0,
            "most_confident_slots": [],
            "best_performing_times": [],
            "platform_breakdown": {}
        }
        
        all_slots = []
        
        if platform:
            platforms = [platform]
        else:
            platforms = self.time_slots.keys()
        
        for platform_name in platforms:
            platform_slots = self.time_slots.get(platform_name, {})
            platform_analytics = {
                "slot_count": len(platform_slots),
                "avg_score": 0.0,
                "avg_confidence": 0.0,
                "best_times": []
            }
            
            if platform_slots:
                scores = [slot.score for slot in platform_slots.values()]
                confidences = [slot.confidence for slot in platform_slots.values()]
                
                platform_analytics["avg_score"] = sum(scores) / len(scores)
                platform_analytics["avg_confidence"] = sum(confidences) / len(confidences)
                
                # Get best performing times
                sorted_slots = sorted(
                    platform_slots.items(),
                    key=lambda x: x[1].score * x[1].confidence,
                    reverse=True
                )
                
                day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                for (hour, dow), slot in sorted_slots[:5]:
                    platform_analytics["best_times"].append({
                        "time": f"{day_names[dow]} {hour:02d}:00",
                        "score": round(slot.score, 3),
                        "confidence": round(slot.confidence, 3),
                        "samples": slot.sample_count
                    })
                
                all_slots.extend(platform_slots.values())
            
            analytics["platform_breakdown"][platform_name] = platform_analytics
        
        # Overall analytics
        if all_slots:
            analytics["total_slots"] = len(all_slots)
            analytics["high_performance_slots"] = len([s for s in all_slots if s.score > 0.7])
            analytics["average_score"] = sum(s.score for s in all_slots) / len(all_slots)
            
            # Top slots across all platforms
            top_slots = sorted(all_slots, key=lambda x: x.score * x.confidence, reverse=True)[:10]
            
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for slot in top_slots:
                analytics["most_confident_slots"].append({
                    "platform": slot.platform,
                    "time": f"{day_names[slot.day_of_week]} {slot.hour:02d}:00",
                    "score": round(slot.score, 3),
                    "confidence": round(slot.confidence, 3)
                })
        
        return analytics
    
    async def optimize_schedule_for_week(self, platforms: List[str],
                                       posts_per_day: Dict[str, int] = None) -> Dict[str, List[ScheduleRecommendation]]:
        """Generate optimized weekly schedule"""
        
        posts_per_day = posts_per_day or {p: 1 for p in platforms}
        weekly_schedule = {}
        
        for platform in platforms:
            daily_posts = posts_per_day.get(platform, 1)
            platform_schedule = []
            
            for day_offset in range(7):
                for post_num in range(daily_posts):
                    # Stagger posts throughout the day
                    min_gap = 6 if daily_posts > 1 else 24  # 6 hours between posts same day
                    
                    recommendation = await self.get_optimal_time(
                        platform,
                        exclude_hours=[rec.datetime_utc.hour for rec in platform_schedule[-3:]],
                        min_gap_hours=min_gap
                    )
                    
                    platform_schedule.append(recommendation)
            
            weekly_schedule[platform] = platform_schedule
        
        return weekly_schedule

class ThompsonSamplingScheduler:
    """Advanced scheduler using Thompson Sampling for exploration/exploitation"""
    
    def __init__(self, base_scheduler: SmartScheduler):
        self.base_scheduler = base_scheduler
        self.exploration_rate = 0.1  # 10% exploration
    
    async def get_optimal_time_with_exploration(self, platform: str) -> ScheduleRecommendation:
        """Get optimal time using Thompson Sampling"""
        
        # Get all available slots
        platform_slots = self.base_scheduler.time_slots.get(platform, {})
        
        if not platform_slots:
            return await self.base_scheduler.get_optimal_time(platform)
        
        # Thompson Sampling: sample from Beta distribution
        slot_samples = {}
        for (hour, dow), slot in platform_slots.items():
            # Beta parameters based on performance
            alpha = max(1, slot.sample_count * slot.score + 1)
            beta = max(1, slot.sample_count * (1 - slot.score) + 1)
            
            # Sample from Beta distribution
            sampled_value = np.random.beta(alpha, beta)
            slot_samples[(hour, dow)] = sampled_value
        
        # Select best sampled slot
        best_slot_key = max(slot_samples.items(), key=lambda x: x[1])[0]
        
        # Create recommendation
        hour, dow = best_slot_key
        current_time = datetime.now(timezone.utc)
        
        # Find next occurrence
        days_ahead = (dow - current_time.weekday()) % 7
        if days_ahead == 0 and current_time.hour >= hour:
            days_ahead = 7
        
        target_time = current_time + timedelta(days=days_ahead)
        target_time = target_time.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        slot = platform_slots[best_slot_key]
        local_time = await self.base_scheduler._convert_to_local_time(target_time)
        
        return ScheduleRecommendation(
            platform=platform,
            datetime_utc=target_time,
            local_time=local_time,
            score=slot.score,
            confidence=slot.confidence,
            reason=f"Thompson Sampling selected time (exploration/exploitation balance)"
        )

# Example usage and testing
async def main():
    scheduler = SmartScheduler()
    
    # Get optimal time for Instagram
    recommendation = await scheduler.get_optimal_time("instagram")
    print(f"📅 Instagram: {recommendation.local_time}")
    print(f"   Score: {recommendation.score:.2f}")
    print(f"   Reason: {recommendation.reason}")
    
    # Get multi-platform schedule
    platforms = ["instagram", "youtube", "tiktok"]
    recommendations = await scheduler.get_multi_platform_schedule(platforms)
    
    print("\n🗓️ Multi-platform Schedule:")
    for rec in recommendations:
        print(f"{rec.platform.capitalize()}: {rec.local_time} (Score: {rec.score:.2f})")
    
    # Simulate recording performance
    test_metrics = PostMetrics(
        post_id="test123",
        platform="instagram",
        publish_time=datetime.now(timezone.utc),
        hour=19,
        day_of_week=2,  # Wednesday
        engagement_rate=0.05,
        views=1000,
        likes=45,
        comments=5,
        shares=2
    )
    
    await scheduler.record_post_performance(test_metrics)
    print("\n✅ Performance recorded")
    
    # Get analytics
    analytics = await scheduler.get_posting_analytics("instagram")
    print(f"\n📊 Instagram Analytics:")
    print(f"   Best times: {analytics['platform_breakdown']['instagram']['best_times'][:3]}")

if __name__ == "__main__":
    asyncio.run(main())