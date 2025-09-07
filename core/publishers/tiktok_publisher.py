#!/usr/bin/env python3
"""
TikTok Publisher
Publishes videos to TikTok using TikTok API for Business
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

class TikTokPublisher(BasePublisher):
    """TikTok API publisher for videos"""
    
    def __init__(self, credentials: PlatformCredentials):
        super().__init__(credentials)
        self.api_base = "https://open-api.tiktok.com"
        self.access_token = credentials.credentials.get("access_token")
        self.client_key = credentials.credentials.get("client_key")
        self.client_secret = credentials.credentials.get("client_secret")
        self.open_id = credentials.credentials.get("open_id")  # TikTok user ID
        self.refresh_token = credentials.refresh_token
    
    async def authenticate(self) -> bool:
        """Authenticate with TikTok API"""
        
        if not self.access_token:
            if self.refresh_token:
                return await self._refresh_access_token()
            else:
                logger.error("No access token or refresh token available")
                return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/oauth/token/info/",
                    json={
                        "client_key": self.client_key,
                        "access_token": self.access_token
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("error_code") == 0:
                        logger.info("TikTok authentication successful")
                        return True
                
                # Token might be expired
                if self.refresh_token:
                    return await self._refresh_access_token()
                    
                logger.error(f"TikTok authentication failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"TikTok authentication error: {e}")
            return False
    
    async def _refresh_access_token(self) -> bool:
        """Refresh the access token"""
        
        if not self.refresh_token:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/oauth/refresh_token/",
                    json={
                        "client_key": self.client_key,
                        "client_secret": self.client_secret,
                        "refresh_token": self.refresh_token,
                        "grant_type": "refresh_token"
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("error_code") == 0:
                        token_info = data["data"]
                        self.access_token = token_info["access_token"]
                        self.refresh_token = token_info.get("refresh_token", self.refresh_token)
                        
                        # Update credentials
                        self.credentials.credentials["access_token"] = self.access_token
                        self.credentials.refresh_token = self.refresh_token
                        
                        logger.info("TikTok access token refreshed successfully")
                        return True
                
                logger.error(f"TikTok token refresh failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"TikTok token refresh error: {e}")
            return False
    
    async def publish_content(self, payload: ContentPayload) -> PublishResult:
        """Publish video to TikTok"""
        
        if payload.content_type != ContentType.VIDEO:
            return PublishResult(
                success=False,
                platform="tiktok",
                status=PublishStatus.FAILED,
                error="TikTok only supports video content"
            )
        
        if not payload.file_paths:
            return PublishResult(
                success=False,
                platform="tiktok",
                status=PublishStatus.FAILED,
                error="No video file provided"
            )
        
        video_path = payload.file_paths[0]
        
        try:
            # Step 1: Initialize video upload
            init_result = await self._initialize_upload(payload)
            if not init_result["success"]:
                return PublishResult(
                    success=False,
                    platform="tiktok",
                    status=PublishStatus.FAILED,
                    error=init_result["error"]
                )
            
            upload_url = init_result["upload_url"]
            video_id = init_result["video_id"]
            
            # Step 2: Upload video file
            upload_result = await self._upload_video_file(video_path, upload_url)
            if not upload_result["success"]:
                return PublishResult(
                    success=False,
                    platform="tiktok",
                    status=PublishStatus.FAILED,
                    error=upload_result["error"]
                )
            
            # Step 3: Create video post
            post_result = await self._create_video_post(video_id, payload)
            
            if post_result["success"]:
                share_id = post_result["share_id"]
                video_url = f"https://www.tiktok.com/@{self.open_id}/video/{share_id}"
                
                return PublishResult(
                    success=True,
                    platform="tiktok",
                    post_id=share_id,
                    url=video_url,
                    status=PublishStatus.PUBLISHED,
                    metadata={
                        "share_id": share_id,
                        "video_id": video_id,
                        "video_url": video_url
                    }
                )
            else:
                return PublishResult(
                    success=False,
                    platform="tiktok",
                    status=PublishStatus.FAILED,
                    error=post_result["error"]
                )
                
        except Exception as e:
            logger.error(f"TikTok publishing failed: {e}")
            return PublishResult(
                success=False,
                platform="tiktok",
                status=PublishStatus.FAILED,
                error=str(e)
            )
    
    async def _initialize_upload(self, payload: ContentPayload) -> Dict[str, Any]:
        """Initialize video upload and get upload URL"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/share/video/init/",
                    json={
                        "access_token": self.access_token,
                        "open_id": self.open_id,
                        "body": {
                            "source_info": {
                                "source": "FILE_UPLOAD",
                                "video_size": os.path.getsize(payload.file_paths[0]),
                                "chunk_size": 10485760,  # 10MB chunks
                                "total_chunk_count": 1
                            }
                        }
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("error_code") == 0:
                        share_info = data["data"]["share_info"]
                        return {
                            "success": True,
                            "upload_url": share_info["upload_url"],
                            "video_id": share_info["video_id"]
                        }
                
                return {
                    "success": False,
                    "error": f"Upload initialization failed: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Initialize upload error: {str(e)}"
            }
    
    async def _upload_video_file(self, video_path: str, upload_url: str) -> Dict[str, Any]:
        """Upload video file to TikTok"""
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
                
                with open(video_path, "rb") as video_file:
                    files = {"video": ("video.mp4", video_file, "video/mp4")}
                    
                    response = await client.put(
                        upload_url,
                        files=files
                    )
                
                if response.status_code in [200, 201]:
                    return {"success": True}
                else:
                    return {
                        "success": False,
                        "error": f"File upload failed: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"File upload error: {str(e)}"
            }
    
    async def _create_video_post(self, video_id: str, payload: ContentPayload) -> Dict[str, Any]:
        """Create the video post with metadata"""
        
        try:
            # Prepare post data
            post_data = {
                "access_token": self.access_token,
                "open_id": self.open_id,
                "body": {
                    "video_info": {
                        "video_id": video_id
                    },
                    "post_info": {
                        "title": self._format_title(payload),
                        "privacy_level": "EVERYONE" if payload.privacy == "public" else "PRIVATE",
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False,
                        "video_cover_timestamp_ms": 1000
                    },
                    "source_info": {
                        "source": "FILE_UPLOAD"
                    }
                }
            }
            
            # Add location if provided
            if payload.location:
                post_data["body"]["post_info"]["geofencing_regions"] = [payload.location]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/share/video/publish/",
                    json=post_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("error_code") == 0:
                        return {
                            "success": True,
                            "share_id": data["data"]["share_id"]
                        }
                
                return {
                    "success": False,
                    "error": f"Post creation failed: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Post creation error: {str(e)}"
            }
    
    def _format_title(self, payload: ContentPayload) -> str:
        """Format TikTok video title"""
        
        title_parts = []
        
        # Use title if provided, otherwise use caption
        if payload.title:
            title_parts.append(payload.title)
        elif payload.caption:
            title_parts.append(payload.caption)
        
        # Add hashtags (TikTok loves hashtags)
        if payload.hashtags:
            hashtags = " ".join(f"#{tag}" for tag in payload.hashtags[:10])  # Max 10 hashtags
            title_parts.append(hashtags)
        
        # Add ClipFlow credit
        title_parts.append("🤖 #ClipFlow")
        
        title = " ".join(title_parts)
        
        # TikTok title limit
        if len(title) > 150:
            title = title[:147] + "..."
        
        return title
    
    async def schedule_content(self, payload: ContentPayload, publish_time: str) -> PublishResult:
        """Schedule content for future publishing"""
        
        # TikTok API doesn't currently support direct scheduling
        # This would need to be handled by a job scheduler
        
        return PublishResult(
            success=False,
            platform="tiktok",
            status=PublishStatus.FAILED,
            error="TikTok API doesn't support direct scheduling"
        )
    
    async def get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get TikTok video metrics"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/video/query/",
                    params={
                        "access_token": self.access_token,
                        "open_id": self.open_id,
                        "filters": json.dumps({
                            "video_ids": [post_id]
                        })
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"Failed to get metrics: {response.text}"}
                
                data = response.json()
                if data.get("data", {}).get("error_code") != 0:
                    return {"error": data.get("data", {}).get("description", "Unknown error")}
                
                videos = data.get("data", {}).get("videos", [])
                if not videos:
                    return {"error": "Video not found"}
                
                video = videos[0]
                
                return {
                    "views": video.get("view_count", 0),
                    "likes": video.get("like_count", 0),
                    "comments": video.get("comment_count", 0),
                    "shares": video.get("share_count", 0),
                    "title": video.get("title", ""),
                    "create_time": video.get("create_time", ""),
                    "video_description": video.get("video_description", ""),
                    "duration": video.get("duration", 0),
                    "video_url": f"https://www.tiktok.com/@{self.open_id}/video/{post_id}",
                    "platform": "tiktok"
                }
                
        except Exception as e:
            logger.error(f"Error getting TikTok metrics: {e}")
            return {"error": str(e)}
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete TikTok video"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/video/delete/",
                    json={
                        "access_token": self.access_token,
                        "open_id": self.open_id,
                        "video_id": post_id
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("error_code") == 0
                
                return False
                
        except Exception as e:
            logger.error(f"Error deleting TikTok video: {e}")
            return False
    
    def validate_payload(self, payload: ContentPayload) -> List[str]:
        """Validate content for TikTok requirements"""
        
        errors = []
        
        # Content type check
        if payload.content_type != ContentType.VIDEO:
            errors.append("TikTok only accepts video content")
        
        # File check
        if not payload.file_paths:
            errors.append("No video file provided")
        elif not os.path.exists(payload.file_paths[0]):
            errors.append("Video file does not exist")
        
        video_path = payload.file_paths[0]
        
        # File size check (2GB limit)
        if not self._validate_file_size(video_path, 2 * 1024):  # 2GB
            errors.append("Video file exceeds 2GB limit")
        
        # Format check
        if not video_path.lower().endswith(('.mp4', '.mov', '.avi')):
            errors.append("Video must be MP4, MOV, or AVI format")
        
        # Title/caption length check
        title = self._format_title(payload)
        if len(title) > 150:
            errors.append("Title/caption exceeds 150 character limit")
        
        # Hashtag check
        if payload.hashtags and len(payload.hashtags) > 10:
            errors.append("Maximum 10 hashtags recommended")
        
        return errors
    
    def get_platform_limits(self) -> Dict[str, Any]:
        """Get TikTok platform limits"""
        
        return {
            "max_file_size_gb": 2,
            "max_duration_seconds": 600,  # 10 minutes
            "min_duration_seconds": 1,
            "max_title_length": 150,
            "max_hashtags": 10,
            "supported_formats": ["mp4", "mov", "avi"],
            "recommended_aspect_ratio": "9:16",
            "recommended_resolution": "1080x1920",
            "recommended_fps": 30,
            "max_bitrate": "10Mbps",
            "upload_quota": "No official limit specified"
        }

# OAuth helper functions
class TikTokOAuth:
    """Helper for TikTok OAuth2 flow"""
    
    @staticmethod
    def get_auth_url(client_key: str, redirect_uri: str, state: str = None) -> str:
        """Generate TikTok OAuth2 authorization URL"""
        
        scopes = ["user.info.basic", "video.list", "video.upload"]
        scope_string = ",".join(scopes)
        
        url = (
            f"https://www.tiktok.com/auth/authorize/?"
            f"client_key={client_key}&"
            f"scope={scope_string}&"
            f"response_type=code&"
            f"redirect_uri={redirect_uri}"
        )
        
        if state:
            url += f"&state={state}"
        
        return url
    
    @staticmethod
    async def exchange_code_for_tokens(client_key: str, client_secret: str,
                                     code: str, redirect_uri: str) -> Dict[str, str]:
        """Exchange authorization code for access tokens"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://open-api.tiktok.com/oauth/access_token/",
                    json={
                        "client_key": client_key,
                        "client_secret": client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("error_code") == 0:
                        return data["data"]
                    else:
                        raise Exception(f"Token exchange failed: {data}")
                else:
                    raise Exception(f"Token exchange request failed: {response.text}")
                    
        except Exception as e:
            raise Exception(f"TikTok OAuth2 exchange error: {e}")

# Example usage
async def main():
    credentials = PlatformCredentials(
        platform="tiktok",
        credentials={
            "client_key": "your_client_key",
            "client_secret": "your_client_secret",
            "access_token": "your_access_token",
            "open_id": "your_open_id"
        },
        refresh_token="your_refresh_token"
    )
    
    publisher = TikTokPublisher(credentials)
    
    if await publisher.authenticate():
        print("✅ TikTok authentication successful")
        
        # Create video payload
        payload = ContentPayload(
            content_type=ContentType.VIDEO,
            file_paths=["tiktok_video.mp4"],
            title="Amazing content! 🔥",
            caption="Check out this cool video",
            hashtags=["fyp", "viral", "amazing", "content"],
            privacy="public"
        )
        
        # Publish video
        result = await publisher.publish_content(payload)
        
        if result.success:
            print(f"✅ Video published: {result.url}")
            
            # Get metrics after some time
            await asyncio.sleep(120)  # Wait 2 minutes
            metrics = await publisher.get_post_metrics(result.post_id)
            print(f"📊 Metrics: {metrics}")
        else:
            print(f"❌ Publishing failed: {result.error}")
    else:
        print("❌ TikTok authentication failed")

if __name__ == "__main__":
    asyncio.run(main())