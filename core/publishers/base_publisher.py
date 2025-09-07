#!/usr/bin/env python3
"""
Base Publisher Interface
Abstract base for all social media platform publishers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

class ContentType(Enum):
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"
    CAROUSEL = "carousel"
    STORY = "story"

class PublishStatus(Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    SCHEDULED = "scheduled"

@dataclass
class PublishResult:
    """Result of publishing operation"""
    success: bool
    platform: str
    post_id: Optional[str] = None
    url: Optional[str] = None
    status: PublishStatus = PublishStatus.PENDING
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ContentPayload:
    """Content to be published"""
    content_type: ContentType
    file_paths: List[str]  # Main content files
    caption: str = ""
    title: str = ""
    description: str = ""
    tags: List[str] = None
    thumbnail_path: Optional[str] = None
    scheduled_time: Optional[str] = None  # ISO format
    privacy: str = "public"  # public, private, unlisted
    location: Optional[str] = None
    mentions: List[str] = None
    hashtags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.mentions is None:
            self.mentions = []
        if self.hashtags is None:
            self.hashtags = []
        if self.metadata is None:
            self.metadata = {}

@dataclass 
class PlatformCredentials:
    """Platform API credentials"""
    platform: str
    credentials: Dict[str, str]
    user_id: Optional[str] = None
    expires_at: Optional[str] = None
    refresh_token: Optional[str] = None

class BasePublisher(ABC):
    """Abstract base publisher for social media platforms"""
    
    def __init__(self, credentials: PlatformCredentials):
        self.credentials = credentials
        self.platform = credentials.platform
        self._session = None
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with platform API"""
        pass
    
    @abstractmethod
    async def publish_content(self, payload: ContentPayload) -> PublishResult:
        """Publish content to platform"""
        pass
    
    @abstractmethod
    async def schedule_content(self, payload: ContentPayload, publish_time: str) -> PublishResult:
        """Schedule content for future publishing"""
        pass
    
    @abstractmethod
    async def get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get metrics for published post"""
        pass
    
    @abstractmethod
    async def delete_post(self, post_id: str) -> bool:
        """Delete published post"""
        pass
    
    @abstractmethod
    def validate_payload(self, payload: ContentPayload) -> List[str]:
        """Validate content payload for platform requirements"""
        pass
    
    @abstractmethod
    def get_platform_limits(self) -> Dict[str, Any]:
        """Get platform-specific limits and constraints"""
        pass
    
    async def test_connection(self) -> bool:
        """Test platform API connection"""
        try:
            return await self.authenticate()
        except Exception as e:
            logger.error(f"Connection test failed for {self.platform}: {e}")
            return False
    
    async def upload_media(self, file_path: str, content_type: ContentType) -> str:
        """Upload media file and return media ID"""
        # Default implementation - should be overridden by platforms that need it
        return file_path
    
    def format_caption(self, payload: ContentPayload) -> str:
        """Format caption with hashtags and mentions"""
        caption = payload.caption
        
        # Add hashtags
        if payload.hashtags:
            hashtags = " ".join(f"#{tag}" for tag in payload.hashtags)
            caption = f"{caption}\n\n{hashtags}"
        
        # Add mentions
        if payload.mentions:
            mentions = " ".join(f"@{mention}" for mention in payload.mentions)
            caption = f"{caption}\n{mentions}"
        
        return caption.strip()
    
    def _validate_file_size(self, file_path: str, max_size_mb: int) -> bool:
        """Validate file size against limit"""
        try:
            import os
            file_size = os.path.getsize(file_path)
            return file_size <= max_size_mb * 1024 * 1024
        except:
            return False
    
    def _validate_video_duration(self, file_path: str, max_duration: int) -> bool:
        """Validate video duration against limit"""
        # Would need ffprobe implementation
        return True
    
    def _validate_image_dimensions(self, file_path: str, max_width: int, max_height: int) -> bool:
        """Validate image dimensions"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return img.width <= max_width and img.height <= max_height
        except:
            return False

class PublishManager:
    """Manages publishing across multiple platforms"""
    
    def __init__(self):
        self.publishers: Dict[str, BasePublisher] = {}
    
    def add_publisher(self, publisher: BasePublisher):
        """Add publisher for a platform"""
        self.publishers[publisher.platform] = publisher
    
    def remove_publisher(self, platform: str):
        """Remove publisher for platform"""
        if platform in self.publishers:
            del self.publishers[platform]
    
    async def publish_to_platform(self, platform: str, payload: ContentPayload) -> PublishResult:
        """Publish content to specific platform"""
        
        if platform not in self.publishers:
            return PublishResult(
                success=False,
                platform=platform,
                status=PublishStatus.FAILED,
                error=f"No publisher configured for {platform}"
            )
        
        publisher = self.publishers[platform]
        
        try:
            # Validate payload
            validation_errors = publisher.validate_payload(payload)
            if validation_errors:
                return PublishResult(
                    success=False,
                    platform=platform,
                    status=PublishStatus.FAILED,
                    error=f"Validation errors: {', '.join(validation_errors)}"
                )
            
            # Authenticate if needed
            if not await publisher.authenticate():
                return PublishResult(
                    success=False,
                    platform=platform, 
                    status=PublishStatus.FAILED,
                    error="Authentication failed"
                )
            
            # Publish content
            result = await publisher.publish_content(payload)
            return result
            
        except Exception as e:
            logger.error(f"Publishing to {platform} failed: {e}")
            return PublishResult(
                success=False,
                platform=platform,
                status=PublishStatus.FAILED,
                error=str(e)
            )
    
    async def publish_to_multiple_platforms(self, platforms: List[str], 
                                          payload: ContentPayload) -> List[PublishResult]:
        """Publish content to multiple platforms simultaneously"""
        
        tasks = []
        for platform in platforms:
            task = self.publish_to_platform(platform, payload)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(PublishResult(
                    success=False,
                    platform=platforms[i],
                    status=PublishStatus.FAILED,
                    error=str(result)
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def schedule_to_multiple_platforms(self, platforms: List[str],
                                           payload: ContentPayload,
                                           publish_time: str) -> List[PublishResult]:
        """Schedule content to multiple platforms"""
        
        tasks = []
        for platform in platforms:
            if platform in self.publishers:
                task = self.publishers[platform].schedule_content(payload, publish_time)
                tasks.append(task)
            else:
                # Create failed result for missing publisher
                failed_result = PublishResult(
                    success=False,
                    platform=platform,
                    status=PublishStatus.FAILED,
                    error=f"No publisher configured for {platform}"
                )
                tasks.append(asyncio.create_task(asyncio.coroutine(lambda: failed_result)()))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(PublishResult(
                    success=False,
                    platform=platforms[i],
                    status=PublishStatus.FAILED,
                    error=str(result)
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def get_all_metrics(self, post_mapping: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Get metrics from all platforms for cross-platform posts"""
        
        results = {}
        tasks = []
        platforms = []
        
        for platform, post_id in post_mapping.items():
            if platform in self.publishers:
                task = self.publishers[platform].get_post_metrics(post_id)
                tasks.append(task)
                platforms.append(platform)
        
        if tasks:
            metrics_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, metrics in enumerate(metrics_results):
                platform = platforms[i]
                if isinstance(metrics, Exception):
                    results[platform] = {"error": str(metrics)}
                else:
                    results[platform] = metrics
        
        return results
    
    def get_available_platforms(self) -> List[str]:
        """Get list of configured platforms"""
        return list(self.publishers.keys())
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all configured platforms"""
        
        results = {}
        tasks = []
        platforms = []
        
        for platform, publisher in self.publishers.items():
            task = publisher.test_connection()
            tasks.append(task)
            platforms.append(platform)
        
        if tasks:
            test_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(test_results):
                platform = platforms[i]
                if isinstance(result, Exception):
                    results[platform] = False
                else:
                    results[platform] = result
        
        return results

# Utility functions
def create_video_payload(video_path: str, caption: str = "", title: str = "",
                        hashtags: List[str] = None, thumbnail_path: str = None) -> ContentPayload:
    """Helper to create video content payload"""
    return ContentPayload(
        content_type=ContentType.VIDEO,
        file_paths=[video_path],
        caption=caption,
        title=title,
        hashtags=hashtags or [],
        thumbnail_path=thumbnail_path
    )

def create_image_payload(image_paths: Union[str, List[str]], caption: str = "",
                        hashtags: List[str] = None) -> ContentPayload:
    """Helper to create image/carousel content payload"""
    
    if isinstance(image_paths, str):
        paths = [image_paths]
        content_type = ContentType.IMAGE
    else:
        paths = image_paths
        content_type = ContentType.CAROUSEL if len(paths) > 1 else ContentType.IMAGE
    
    return ContentPayload(
        content_type=content_type,
        file_paths=paths,
        caption=caption,
        hashtags=hashtags or []
    )

def create_text_payload(text: str, hashtags: List[str] = None) -> ContentPayload:
    """Helper to create text-only content payload"""
    return ContentPayload(
        content_type=ContentType.TEXT,
        file_paths=[],
        caption=text,
        hashtags=hashtags or []
    )

# Example usage
async def main():
    manager = PublishManager()
    
    # Would add real publishers here
    # manager.add_publisher(YouTubePublisher(credentials))
    # manager.add_publisher(InstagramPublisher(credentials))
    
    # Create content payload
    payload = create_video_payload(
        video_path="video.mp4",
        caption="Check out this amazing content!",
        hashtags=["viral", "content", "amazing"],
        title="Amazing Video"
    )
    
    # Publish to multiple platforms
    platforms = ["youtube", "instagram", "tiktok"]
    results = await manager.publish_to_multiple_platforms(platforms, payload)
    
    for result in results:
        if result.success:
            print(f"✅ {result.platform}: {result.url}")
        else:
            print(f"❌ {result.platform}: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())