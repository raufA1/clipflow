#!/usr/bin/env python3
"""
Instagram Publisher  
Publishes content to Instagram using Instagram Basic Display API and Graph API
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import httpx
import json
from pathlib import Path

from .base_publisher import BasePublisher, ContentPayload, PublishResult, ContentType, PublishStatus, PlatformCredentials

logger = logging.getLogger(__name__)

class InstagramPublisher(BasePublisher):
    """Instagram API publisher for posts, reels, and stories"""
    
    def __init__(self, credentials: PlatformCredentials):
        super().__init__(credentials)
        self.graph_api_base = "https://graph.facebook.com/v18.0"
        self.access_token = credentials.credentials.get("access_token")
        self.user_id = credentials.user_id or credentials.credentials.get("user_id")
        self.page_id = credentials.credentials.get("page_id")  # For business accounts
        self.app_id = credentials.credentials.get("app_id")
        self.app_secret = credentials.credentials.get("app_secret")
    
    async def authenticate(self) -> bool:
        """Authenticate with Instagram API"""
        
        if not self.access_token:
            logger.error("No access token available")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                # Test token with basic user info request
                response = await client.get(
                    f"{self.graph_api_base}/me",
                    params={
                        "fields": "id,username",
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.user_id = user_data.get("id")
                    logger.info(f"Instagram authentication successful for user: {user_data.get('username')}")
                    return True
                else:
                    logger.error(f"Instagram authentication failed: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Instagram authentication error: {e}")
            return False
    
    async def publish_content(self, payload: ContentPayload) -> PublishResult:
        """Publish content to Instagram"""
        
        try:
            if payload.content_type == ContentType.VIDEO:
                return await self._publish_reel(payload)
            elif payload.content_type in [ContentType.IMAGE, ContentType.CAROUSEL]:
                return await self._publish_image_post(payload)
            elif payload.content_type == ContentType.STORY:
                return await self._publish_story(payload)
            else:
                return PublishResult(
                    success=False,
                    platform="instagram",
                    status=PublishStatus.FAILED,
                    error=f"Unsupported content type: {payload.content_type}"
                )
                
        except Exception as e:
            logger.error(f"Instagram publishing failed: {e}")
            return PublishResult(
                success=False,
                platform="instagram",
                status=PublishStatus.FAILED,
                error=str(e)
            )
    
    async def _publish_reel(self, payload: ContentPayload) -> PublishResult:
        """Publish video as Instagram Reel"""
        
        video_path = payload.file_paths[0]
        
        try:
            # Step 1: Upload video and get media container ID
            container_result = await self._create_video_container(video_path, payload)
            if not container_result["success"]:
                return PublishResult(
                    success=False,
                    platform="instagram",
                    status=PublishStatus.FAILED,
                    error=container_result["error"]
                )
            
            container_id = container_result["container_id"]
            
            # Step 2: Wait for video processing
            await self._wait_for_video_processing(container_id)
            
            # Step 3: Publish the container
            publish_result = await self._publish_container(container_id)
            
            if publish_result["success"]:
                media_id = publish_result["media_id"]
                media_url = f"https://www.instagram.com/reel/{media_id}"
                
                return PublishResult(
                    success=True,
                    platform="instagram",
                    post_id=media_id,
                    url=media_url,
                    status=PublishStatus.PUBLISHED,
                    metadata={
                        "media_id": media_id,
                        "media_url": media_url,
                        "content_type": "reel"
                    }
                )
            else:
                return PublishResult(
                    success=False,
                    platform="instagram", 
                    status=PublishStatus.FAILED,
                    error=publish_result["error"]
                )
                
        except Exception as e:
            return PublishResult(
                success=False,
                platform="instagram",
                status=PublishStatus.FAILED,
                error=str(e)
            )
    
    async def _create_video_container(self, video_path: str, payload: ContentPayload) -> Dict[str, Any]:
        """Create video media container"""
        
        try:
            async with httpx.AsyncClient() as client:
                
                # Upload video file first (this is simplified - real implementation would use resumable upload)
                with open(video_path, "rb") as video_file:
                    files = {"file": video_file}
                    
                    # Create container with video
                    response = await client.post(
                        f"{self.graph_api_base}/{self.user_id}/media",
                        data={
                            "media_type": "REELS",
                            "video_url": video_path,  # In real implementation, this would be a public URL
                            "caption": self.format_caption(payload),
                            "access_token": self.access_token
                        }
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "container_id": result["id"]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Container creation failed: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Video upload failed: {str(e)}"
            }
    
    async def _wait_for_video_processing(self, container_id: str, timeout: int = 300):
        """Wait for video processing to complete"""
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.graph_api_base}/{container_id}",
                        params={
                            "fields": "status_code",
                            "access_token": self.access_token
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get("status_code")
                        
                        if status == "FINISHED":
                            logger.info("Video processing completed")
                            return
                        elif status == "ERROR":
                            raise Exception("Video processing failed")
                    
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise Exception("Video processing timeout")
                
                # Wait before checking again
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error checking video processing status: {e}")
                raise
    
    async def _publish_container(self, container_id: str) -> Dict[str, Any]:
        """Publish the media container"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.graph_api_base}/{self.user_id}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "media_id": result["id"]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Publishing failed: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Publish request failed: {str(e)}"
            }
    
    async def _publish_image_post(self, payload: ContentPayload) -> PublishResult:
        """Publish image or carousel post"""
        
        try:
            if payload.content_type == ContentType.CAROUSEL and len(payload.file_paths) > 1:
                return await self._publish_carousel(payload)
            else:
                return await self._publish_single_image(payload)
                
        except Exception as e:
            return PublishResult(
                success=False,
                platform="instagram",
                status=PublishStatus.FAILED,
                error=str(e)
            )
    
    async def _publish_single_image(self, payload: ContentPayload) -> PublishResult:
        """Publish single image post"""
        
        image_path = payload.file_paths[0]
        
        try:
            async with httpx.AsyncClient() as client:
                
                # Create image container
                with open(image_path, "rb") as image_file:
                    files = {"file": image_file}
                    
                    response = await client.post(
                        f"{self.graph_api_base}/{self.user_id}/media",
                        data={
                            "image_url": image_path,  # In real implementation, this would be a public URL
                            "caption": self.format_caption(payload),
                            "access_token": self.access_token
                        }
                    )
                
                if response.status_code != 200:
                    return PublishResult(
                        success=False,
                        platform="instagram",
                        status=PublishStatus.FAILED,
                        error=f"Image upload failed: {response.text}"
                    )
                
                container_data = response.json()
                container_id = container_data["id"]
                
                # Publish the container
                publish_result = await self._publish_container(container_id)
                
                if publish_result["success"]:
                    media_id = publish_result["media_id"]
                    media_url = f"https://www.instagram.com/p/{media_id}"
                    
                    return PublishResult(
                        success=True,
                        platform="instagram",
                        post_id=media_id,
                        url=media_url,
                        status=PublishStatus.PUBLISHED,
                        metadata={
                            "media_id": media_id,
                            "media_url": media_url,
                            "content_type": "image"
                        }
                    )
                else:
                    return PublishResult(
                        success=False,
                        platform="instagram",
                        status=PublishStatus.FAILED,
                        error=publish_result["error"]
                    )
                    
        except Exception as e:
            return PublishResult(
                success=False,
                platform="instagram",
                status=PublishStatus.FAILED,
                error=str(e)
            )
    
    async def _publish_carousel(self, payload: ContentPayload) -> PublishResult:
        """Publish carousel post with multiple images"""
        
        try:
            # Create containers for each image
            child_containers = []
            
            async with httpx.AsyncClient() as client:
                for image_path in payload.file_paths[:10]:  # Instagram max 10 images
                    
                    with open(image_path, "rb") as image_file:
                        response = await client.post(
                            f"{self.graph_api_base}/{self.user_id}/media",
                            data={
                                "image_url": image_path,
                                "is_carousel_item": "true",
                                "access_token": self.access_token
                            }
                        )
                    
                    if response.status_code == 200:
                        container_data = response.json()
                        child_containers.append(container_data["id"])
                    else:
                        logger.error(f"Failed to create container for {image_path}: {response.text}")
                
                if not child_containers:
                    return PublishResult(
                        success=False,
                        platform="instagram",
                        status=PublishStatus.FAILED,
                        error="No image containers created"
                    )
                
                # Create carousel container
                carousel_response = await client.post(
                    f"{self.graph_api_base}/{self.user_id}/media",
                    data={
                        "media_type": "CAROUSEL",
                        "children": ",".join(child_containers),
                        "caption": self.format_caption(payload),
                        "access_token": self.access_token
                    }
                )
                
                if carousel_response.status_code != 200:
                    return PublishResult(
                        success=False,
                        platform="instagram",
                        status=PublishStatus.FAILED,
                        error=f"Carousel creation failed: {carousel_response.text}"
                    )
                
                carousel_data = carousel_response.json()
                carousel_id = carousel_data["id"]
                
                # Publish carousel
                publish_result = await self._publish_container(carousel_id)
                
                if publish_result["success"]:
                    media_id = publish_result["media_id"]
                    media_url = f"https://www.instagram.com/p/{media_id}"
                    
                    return PublishResult(
                        success=True,
                        platform="instagram",
                        post_id=media_id,
                        url=media_url,
                        status=PublishStatus.PUBLISHED,
                        metadata={
                            "media_id": media_id,
                            "media_url": media_url,
                            "content_type": "carousel",
                            "item_count": len(child_containers)
                        }
                    )
                else:
                    return PublishResult(
                        success=False,
                        platform="instagram",
                        status=PublishStatus.FAILED,
                        error=publish_result["error"]
                    )
                    
        except Exception as e:
            return PublishResult(
                success=False,
                platform="instagram",
                status=PublishStatus.FAILED,
                error=str(e)
            )
    
    async def _publish_story(self, payload: ContentPayload) -> PublishResult:
        """Publish Instagram Story"""
        
        # Stories require different endpoint and have different limitations
        return PublishResult(
            success=False,
            platform="instagram",
            status=PublishStatus.FAILED,
            error="Story publishing not yet implemented"
        )
    
    async def schedule_content(self, payload: ContentPayload, publish_time: str) -> PublishResult:
        """Schedule content for future publishing"""
        
        # Instagram Graph API supports scheduling for business accounts
        try:
            # Convert to Unix timestamp
            from datetime import datetime
            import calendar
            
            dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
            scheduled_timestamp = calendar.timegm(dt.timetuple())
            
            # For now, just store the schedule info
            # Real implementation would create container with scheduled_publish_time
            
            return PublishResult(
                success=False,
                platform="instagram",
                status=PublishStatus.FAILED,
                error="Instagram scheduling requires business account setup"
            )
            
        except Exception as e:
            return PublishResult(
                success=False,
                platform="instagram",
                status=PublishStatus.FAILED,
                error=str(e)
            )
    
    async def get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get Instagram post metrics"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.graph_api_base}/{post_id}/insights",
                    params={
                        "metric": "impressions,reach,likes,comments,saves,shares,video_views",
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"Failed to get metrics: {response.text}"}
                
                data = response.json()
                metrics = {}
                
                for item in data.get("data", []):
                    metric_name = item.get("name")
                    metric_values = item.get("values", [])
                    if metric_values:
                        metrics[metric_name] = metric_values[0].get("value", 0)
                
                # Get basic post info
                post_response = await client.get(
                    f"{self.graph_api_base}/{post_id}",
                    params={
                        "fields": "id,media_type,media_url,permalink,timestamp,caption",
                        "access_token": self.access_token
                    }
                )
                
                if post_response.status_code == 200:
                    post_data = post_response.json()
                    metrics.update({
                        "media_type": post_data.get("media_type"),
                        "media_url": post_data.get("media_url"),
                        "permalink": post_data.get("permalink"),
                        "timestamp": post_data.get("timestamp"),
                        "caption": post_data.get("caption", ""),
                        "platform": "instagram"
                    })
                
                return metrics
                
        except Exception as e:
            logger.error(f"Error getting Instagram metrics: {e}")
            return {"error": str(e)}
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete Instagram post"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.graph_api_base}/{post_id}",
                    params={"access_token": self.access_token}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error deleting Instagram post: {e}")
            return False
    
    def validate_payload(self, payload: ContentPayload) -> List[str]:
        """Validate content for Instagram requirements"""
        
        errors = []
        
        # File existence check
        for file_path in payload.file_paths:
            if not os.path.exists(file_path):
                errors.append(f"File does not exist: {file_path}")
        
        # Content type specific validation
        if payload.content_type == ContentType.VIDEO:
            errors.extend(self._validate_video(payload))
        elif payload.content_type in [ContentType.IMAGE, ContentType.CAROUSEL]:
            errors.extend(self._validate_image(payload))
        
        # Caption length check
        if len(payload.caption) > 2200:
            errors.append("Caption exceeds 2200 character limit")
        
        # Hashtag check
        if payload.hashtags and len(payload.hashtags) > 30:
            errors.append("Maximum 30 hashtags allowed")
        
        return errors
    
    def _validate_video(self, payload: ContentPayload) -> List[str]:
        """Validate video content"""
        
        errors = []
        video_path = payload.file_paths[0]
        
        # File size check (4GB limit)
        if not self._validate_file_size(video_path, 4 * 1024):  # 4GB
            errors.append("Video file exceeds 4GB limit")
        
        # Format check
        if not video_path.lower().endswith(('.mp4', '.mov')):
            errors.append("Video must be MP4 or MOV format")
        
        return errors
    
    def _validate_image(self, payload: ContentPayload) -> List[str]:
        """Validate image content"""
        
        errors = []
        
        # Carousel limit
        if payload.content_type == ContentType.CAROUSEL and len(payload.file_paths) > 10:
            errors.append("Carousel can have maximum 10 images")
        
        for image_path in payload.file_paths:
            # File size check (30MB limit)
            if not self._validate_file_size(image_path, 30):
                errors.append(f"Image file exceeds 30MB limit: {os.path.basename(image_path)}")
            
            # Format check
            if not image_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                errors.append(f"Image must be JPG or PNG format: {os.path.basename(image_path)}")
        
        return errors
    
    def get_platform_limits(self) -> Dict[str, Any]:
        """Get Instagram platform limits"""
        
        return {
            "max_video_size_gb": 4,
            "max_video_duration": 90,  # seconds for Reels
            "max_image_size_mb": 30,
            "max_caption_length": 2200,
            "max_hashtags": 30,
            "max_carousel_items": 10,
            "supported_video_formats": ["mp4", "mov"],
            "supported_image_formats": ["jpg", "jpeg", "png"],
            "reel_max_duration": 90,
            "story_max_duration": 15,
            "aspect_ratios": {
                "feed": "1:1 to 4:5",
                "story": "9:16",
                "reel": "9:16"
            }
        }

# Example usage
async def main():
    credentials = PlatformCredentials(
        platform="instagram",
        credentials={
            "access_token": "your_access_token",
            "app_id": "your_app_id",
            "app_secret": "your_app_secret"
        },
        user_id="your_user_id"
    )
    
    publisher = InstagramPublisher(credentials)
    
    if await publisher.authenticate():
        print("✅ Instagram authentication successful")
        
        # Publish single image
        image_payload = ContentPayload(
            content_type=ContentType.IMAGE,
            file_paths=["image.jpg"],
            caption="Amazing content! 🔥",
            hashtags=["content", "amazing", "instagram"]
        )
        
        result = await publisher.publish_content(image_payload)
        if result.success:
            print(f"✅ Image published: {result.url}")
        else:
            print(f"❌ Publishing failed: {result.error}")
        
        # Publish Reel
        video_payload = ContentPayload(
            content_type=ContentType.VIDEO,
            file_paths=["reel.mp4"],
            caption="Check out this cool reel! 🎬",
            hashtags=["reel", "viral", "content"]
        )
        
        result = await publisher.publish_content(video_payload)
        if result.success:
            print(f"✅ Reel published: {result.url}")
        else:
            print(f"❌ Reel publishing failed: {result.error}")
    else:
        print("❌ Instagram authentication failed")

if __name__ == "__main__":
    asyncio.run(main())