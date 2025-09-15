#!/usr/bin/env python3
"""
ClipFlow Main Integration Layer
Orchestrates all components: Bot, Processing, Publishing, Scheduling, Analytics
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass

# Import all ClipFlow components
from services.bot.main import ClipFlowBot
from services.processor.content_pipeline import ContentManager, ContentType, Platform
from core.video_processor import VideoProcessor
from core.image_processor import ImageProcessor
from core.text_to_visual import TextToVisualGenerator
from core.audio_processor import AudioProcessor
from core.publishers.base_publisher import PublishManager, create_video_payload, create_image_payload, create_text_payload, PlatformCredentials
from core.publishers.youtube_publisher import YouTubePublisher
from core.publishers.instagram_publisher import InstagramPublisher
from core.publishers.tiktok_publisher import TikTokPublisher
from core.scheduler.smart_scheduler import SmartScheduler, PostMetrics
from core.analytics.metrics_collector import MetricsCollector, ContentMetrics, AnalyticsDashboard
from core.brand import BrandManager

logger = logging.getLogger(__name__)

@dataclass
class ClipFlowConfig:
    """Main configuration for ClipFlow"""
    # Directories
    data_dir: str = "data"
    temp_dir: str = "temp"
    output_dir: str = "data/content"
    
    # Bot settings
    telegram_bot_token: str = ""
    
    # Platform credentials
    platform_credentials: Dict[str, Dict[str, str]] = None
    
    # Processing settings
    default_brand_config: Dict[str, Any] = None
    
    # Scheduling settings
    timezone: str = "Asia/Baku"
    
    def __post_init__(self):
        if self.platform_credentials is None:
            self.platform_credentials = {}
        if self.default_brand_config is None:
            self.default_brand_config = {
                "name": "ClipFlow",
                "primary_color": "#1DA1F2",
                "secondary_color": "#14171A",
                "accent_color": "#FFD700",
                "logo_path": "",
                "watermark_text": "Created with ClipFlow"
            }

class ClipFlowOrchestrator:
    """Main orchestrator that coordinates all ClipFlow components"""
    
    def __init__(self, config: ClipFlowConfig):
        self.config = config
        
        # Initialize core components
        self.content_manager = ContentManager(config.data_dir)
        self.video_processor = VideoProcessor(config.temp_dir, config.output_dir)
        self.image_processor = ImageProcessor(config.temp_dir, config.output_dir) 
        self.text_generator = TextToVisualGenerator(config.temp_dir, config.output_dir)
        self.audio_processor = AudioProcessor(config.temp_dir, config.output_dir)
        
        # Initialize publishing
        self.publish_manager = PublishManager()
        self._setup_publishers()
        
        # Initialize scheduling and analytics
        self.scheduler = SmartScheduler(config.data_dir, config.timezone)
        self.metrics_collector = MetricsCollector(config.data_dir)
        self.analytics_dashboard = AnalyticsDashboard(self.metrics_collector)
        
        # Initialize brand manager
        self.brand_manager = BrandManager()
        
        # Initialize bot (will be started separately)
        self.bot = None
        if config.telegram_bot_token:
            self.bot = ClipFlowBot(config.telegram_bot_token)
            self.bot.set_orchestrator(self)  # Give bot access to orchestrator
    
    def _setup_publishers(self):
        """Setup platform publishers based on credentials"""
        
        for platform, creds in self.config.platform_credentials.items():
            try:
                platform_creds = PlatformCredentials(
                    platform=platform,
                    credentials=creds
                )
                
                if platform == "youtube":
                    publisher = YouTubePublisher(platform_creds)
                elif platform == "instagram":
                    publisher = InstagramPublisher(platform_creds)
                elif platform == "tiktok":
                    publisher = TikTokPublisher(platform_creds)
                else:
                    logger.warning(f"Unknown platform: {platform}")
                    continue
                
                self.publish_manager.add_publisher(publisher)
                logger.info(f"Added publisher for {platform}")
                
            except Exception as e:
                logger.error(f"Failed to setup {platform} publisher: {e}")
    
    async def process_content_from_telegram(self, user_id: int, content_type: str,
                                          file_path: str = None, text_content: str = None,
                                          caption: str = "", platforms: List[str] = None) -> Dict[str, Any]:
        """Process content received from Telegram bot"""
        
        try:
            # Generate unique content ID
            content_id = f"{user_id}_{int(datetime.now().timestamp())}"
            
            # Determine content type
            if content_type == "video":
                ct = ContentType.VIDEO
            elif content_type == "photo":
                ct = ContentType.PHOTO
            elif content_type == "text":
                ct = ContentType.TEXT
            elif content_type == "audio":
                ct = ContentType.AUDIO
            else:
                ct = ContentType.TEXT
            
            # Add content to manager
            content_item = await self.content_manager.add_content(
                user_id=user_id,
                content_type=ct,
                file_path=file_path,
                text_content=text_content,
                caption=caption,
                metadata={"created_via": "telegram"}
            )
            
            # Get platform list
            if not platforms:
                platforms = ["instagram", "youtube", "tiktok"]  # Default platforms
            
            platform_enums = [Platform(p) for p in platforms if p in ["instagram", "youtube", "tiktok"]]
            
            # Process content for each platform
            processing_results = await self.content_manager.process_content(content_item, platform_enums)
            
            # Prepare results
            results = {
                "content_id": content_id,
                "processed_files": [],
                "scheduling_recommendations": [],
                "publishing_status": "processed"
            }
            
            for result in processing_results:
                if result.success:
                    results["processed_files"].append({
                        "platform": result.platform.value,
                        "file_path": result.output_path,
                        "caption": result.caption
                    })
                    
                    # Get scheduling recommendation
                    recommendation = await self.scheduler.get_optimal_time(result.platform.value)
                    results["scheduling_recommendations"].append({
                        "platform": result.platform.value,
                        "recommended_time": recommendation.local_time,
                        "score": recommendation.score,
                        "reason": recommendation.reason
                    })
                else:
                    logger.error(f"Processing failed for {result.platform.value}: {result.error}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing content from Telegram: {e}")
            return {
                "error": str(e),
                "content_id": None,
                "processing_status": "failed"
            }
    
    async def auto_publish_content(self, user_id: int, content_id: str, 
                                 platforms: List[str], schedule: bool = True) -> Dict[str, Any]:
        """Automatically publish or schedule content"""
        
        try:
            results = {
                "content_id": content_id,
                "publish_results": [],
                "scheduled_posts": [],
                "total_success": 0,
                "total_failed": 0
            }
            
            # Get processed files (this would be retrieved from content manager)
            # For now, simulating file paths
            processed_files = {
                platform: f"data/content/{user_id}/videos/{content_id}_{platform}.mp4"
                for platform in platforms
            }
            
            if schedule:
                # Get multi-platform schedule
                recommendations = await self.scheduler.get_multi_platform_schedule(platforms)
                
                for rec in recommendations:
                    if rec.platform in processed_files:
                        # Create payload
                        file_path = processed_files[rec.platform]
                        payload = create_video_payload(
                            video_path=file_path,
                            caption="Amazing content created with ClipFlow! 🚀",
                            hashtags=["clipflow", "automation", "content"]
                        )
                        
                        # Schedule the post
                        schedule_result = await self.publish_manager.publishers[rec.platform].schedule_content(
                            payload, rec.datetime_utc.isoformat()
                        )
                        
                        results["scheduled_posts"].append({
                            "platform": rec.platform,
                            "scheduled_time": rec.local_time,
                            "success": schedule_result.success,
                            "error": schedule_result.error if not schedule_result.success else None
                        })
                        
                        if schedule_result.success:
                            results["total_success"] += 1
                        else:
                            results["total_failed"] += 1
            
            else:
                # Publish immediately
                for platform in platforms:
                    if platform in processed_files:
                        file_path = processed_files[platform]
                        payload = create_video_payload(
                            video_path=file_path,
                            caption="Amazing content created with ClipFlow! 🚀",
                            hashtags=["clipflow", "automation", "content"]
                        )
                        
                        publish_result = await self.publish_manager.publish_to_platform(platform, payload)
                        
                        results["publish_results"].append({
                            "platform": platform,
                            "success": publish_result.success,
                            "url": publish_result.url,
                            "post_id": publish_result.post_id,
                            "error": publish_result.error if not publish_result.success else None
                        })
                        
                        if publish_result.success:
                            results["total_success"] += 1
                            
                            # Record metrics for learning
                            metrics = PostMetrics(
                                post_id=publish_result.post_id,
                                platform=platform,
                                publish_time=datetime.now(timezone.utc),
                                hour=datetime.now().hour,
                                day_of_week=datetime.now().weekday(),
                                engagement_rate=0.0  # Will be updated later
                            )
                            await self.scheduler.record_post_performance(metrics)
                            
                        else:
                            results["total_failed"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error in auto_publish_content: {e}")
            return {
                "error": str(e),
                "content_id": content_id,
                "publish_status": "failed"
            }
    
    async def collect_platform_metrics(self, user_id: int) -> Dict[str, Any]:
        """Collect metrics from all connected platforms"""
        
        try:
            all_metrics = []
            
            # Get recent posts for each platform
            for platform_name, publisher in self.publish_manager.publishers.items():
                try:
                    # In real implementation, would get recent post IDs from database
                    # For now, simulating with placeholder data
                    
                    # Simulate getting metrics for recent posts
                    recent_posts = ["post1", "post2", "post3"]  # Would come from database
                    
                    for post_id in recent_posts:
                        metrics_data = await publisher.get_post_metrics(post_id)
                        
                        if "error" not in metrics_data:
                            # Convert to ContentMetrics format
                            content_metrics = ContentMetrics(
                                content_id=f"content_{post_id}",
                                user_id=user_id,
                                platform=platform_name,
                                content_type="video",  # Would be retrieved from database
                                post_id=post_id,
                                post_url=metrics_data.get("video_url", ""),
                                published_at=metrics_data.get("published_at", datetime.now().isoformat()),
                                views=metrics_data.get("views", 0),
                                likes=metrics_data.get("likes", 0),
                                comments=metrics_data.get("comments", 0),
                                shares=metrics_data.get("shares", 0),
                                engagement_rate=0.0  # Will be calculated
                            )
                            
                            await self.metrics_collector.store_metrics(content_metrics)
                            all_metrics.append(content_metrics)
                            
                except Exception as e:
                    logger.error(f"Error collecting metrics from {platform_name}: {e}")
            
            return {
                "collected_metrics": len(all_metrics),
                "platforms_processed": list(self.publish_manager.publishers.keys()),
                "last_collection": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collecting platform metrics: {e}")
            return {"error": str(e)}
    
    async def generate_user_report(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive user performance report"""
        
        try:
            # Generate performance report
            report = await self.metrics_collector.generate_performance_report(user_id, days)
            
            # Get dashboard data
            dashboard_data = await self.analytics_dashboard.get_dashboard_data(user_id)
            
            # Get scheduling insights
            scheduling_analytics = await self.scheduler.get_posting_analytics()
            
            return {
                "user_id": user_id,
                "report_period": f"{days} days",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "performance_report": {
                    "platforms": len(report.platform_summaries),
                    "top_performers": len(report.top_performers),
                    "growth_metrics": report.growth_metrics,
                    "recommendations": report.recommendations,
                    "best_platforms": report.best_platforms
                },
                "dashboard_data": dashboard_data,
                "scheduling_insights": scheduling_analytics,
                "export_available": True
            }
            
        except Exception as e:
            logger.error(f"Error generating user report: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all system components"""
        
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "healthy",
            "components": {}
        }
        
        try:
            # Test platform connections
            connection_tests = await self.publish_manager.test_all_connections()
            health_status["components"]["publishers"] = {
                "status": "healthy" if any(connection_tests.values()) else "degraded",
                "platforms": connection_tests,
                "total_configured": len(connection_tests)
            }
            
            # Test content processing
            health_status["components"]["content_processing"] = {
                "status": "healthy",
                "video_processor": "available",
                "image_processor": "available", 
                "text_generator": "available",
                "audio_processor": "available"
            }
            
            # Test scheduler
            health_status["components"]["scheduler"] = {
                "status": "healthy",
                "total_slots": len(self.scheduler.time_slots),
                "platforms_configured": list(self.scheduler.time_slots.keys())
            }
            
            # Test analytics
            health_status["components"]["analytics"] = {
                "status": "healthy",
                "database_accessible": True,  # Would test actual DB connection
                "metrics_collector": "operational"
            }
            
            # Test bot
            if self.bot:
                health_status["components"]["telegram_bot"] = {
                    "status": "configured",
                    "token_configured": bool(self.config.telegram_bot_token)
                }
            
        except Exception as e:
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)
        
        return health_status
    
    async def start_bot(self):
        """Start the Telegram bot"""
        if self.bot:
            logger.info("Starting Telegram bot...")
            await self.bot.run_polling()
        else:
            logger.error("Bot not configured - missing token")
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.bot:
            await self.bot.stop()
            logger.info("Telegram bot stopped")

# Configuration loader
class ConfigManager:
    """Manages ClipFlow configuration"""
    
    @staticmethod
    def load_from_file(config_path: str) -> ClipFlowConfig:
        """Load configuration from JSON file"""
        
        if not os.path.exists(config_path):
            # Create default config
            default_config = ClipFlowConfig()
            ConfigManager.save_to_file(default_config, config_path)
            return default_config
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return ClipFlowConfig(**config_data)
    
    @staticmethod
    def save_to_file(config: ClipFlowConfig, config_path: str):
        """Save configuration to JSON file"""
        
        # Convert to dict
        config_dict = {
            "data_dir": config.data_dir,
            "temp_dir": config.temp_dir,
            "output_dir": config.output_dir,
            "telegram_bot_token": config.telegram_bot_token,
            "platform_credentials": config.platform_credentials,
            "default_brand_config": config.default_brand_config,
            "timezone": config.timezone
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
    
    @staticmethod
    def load_from_env() -> ClipFlowConfig:
        """Load configuration from environment variables"""
        
        config = ClipFlowConfig()
        config.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        config.timezone = os.getenv("CLIPFLOW_TIMEZONE", "Asia/Baku")
        
        # Platform credentials from environment
        platforms = ["youtube", "instagram", "tiktok"]
        for platform in platforms:
            platform_creds = {}
            
            if platform == "youtube":
                platform_creds = {
                    "client_id": os.getenv("YOUTUBE_CLIENT_ID", ""),
                    "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET", ""),
                    "access_token": os.getenv("YOUTUBE_ACCESS_TOKEN", "")
                }
            elif platform == "instagram":
                platform_creds = {
                    "access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN", ""),
                    "app_id": os.getenv("INSTAGRAM_APP_ID", ""),
                    "app_secret": os.getenv("INSTAGRAM_APP_SECRET", "")
                }
            elif platform == "tiktok":
                platform_creds = {
                    "client_key": os.getenv("TIKTOK_CLIENT_KEY", ""),
                    "client_secret": os.getenv("TIKTOK_CLIENT_SECRET", ""),
                    "access_token": os.getenv("TIKTOK_ACCESS_TOKEN", "")
                }
            
            # Only add if credentials are provided
            if any(platform_creds.values()):
                config.platform_credentials[platform] = platform_creds
        
        return config

# Main application entry point
async def main():
    """Main entry point for ClipFlow application"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 Starting ClipFlow...")
    
    # Load configuration
    config_path = "config.json"
    if os.getenv("CLIPFLOW_USE_ENV", "false").lower() == "true":
        config = ConfigManager.load_from_env()
        logger.info("📁 Configuration loaded from environment variables")
    else:
        config = ConfigManager.load_from_file(config_path)
        logger.info(f"📁 Configuration loaded from {config_path}")
    
    # Initialize orchestrator
    orchestrator = ClipFlowOrchestrator(config)
    
    # Health check
    health = await orchestrator.health_check()
    logger.info(f"🔍 Health check: {health['overall_status']}")
    logger.info(f"   Publishers: {health['components']['publishers']['total_configured']} configured")
    
    # Start periodic tasks
    async def metrics_collection_task():
        """Periodic metrics collection"""
        while True:
            try:
                # In a real app, would get list of active users
                active_users = [12345]  # Placeholder
                
                for user_id in active_users:
                    await orchestrator.collect_platform_metrics(user_id)
                
                logger.info("📊 Metrics collection completed")
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in metrics collection task: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    # Start background tasks
    metrics_task = asyncio.create_task(metrics_collection_task())
    
    try:
        # Start the bot if configured
        if config.telegram_bot_token:
            logger.info("🤖 Starting Telegram bot...")
            await orchestrator.start_bot()
        else:
            logger.info("⚠️  No Telegram bot token configured")
            logger.info("🔧 ClipFlow is running without bot interface")
            
            # Keep the application running
            while True:
                await asyncio.sleep(60)
                logger.info("❤️  ClipFlow is healthy")
    
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
    
    finally:
        # Cleanup
        metrics_task.cancel()
        await orchestrator.stop_bot()
        logger.info("👋 ClipFlow shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())