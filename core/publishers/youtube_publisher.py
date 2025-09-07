#!/usr/bin/env python3
"""
YouTube Publisher
Publishes videos to YouTube using the YouTube Data API v3
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

class YouTubePublisher(BasePublisher):
    """YouTube API publisher for Shorts and regular videos"""
    
    def __init__(self, credentials: PlatformCredentials):
        super().__init__(credentials)
        self.api_base = "https://www.googleapis.com/youtube/v3"
        self.upload_base = "https://www.googleapis.com/upload/youtube/v3"
        self.access_token = credentials.credentials.get("access_token")
        self.client_id = credentials.credentials.get("client_id")
        self.client_secret = credentials.credentials.get("client_secret")
        self.refresh_token = credentials.refresh_token
    
    async def authenticate(self) -> bool:
        """Authenticate with YouTube API"""
        
        if not self.access_token:
            if self.refresh_token:
                return await self._refresh_access_token()
            else:
                logger.error("No access token or refresh token available")
                return False
        
        # Test the token
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/channels",
                    params={"part": "id", "mine": "true"},
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                
                if response.status_code == 401:
                    # Token expired, try to refresh
                    return await self._refresh_access_token()
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"YouTube authentication failed: {e}")
            return False
    
    async def _refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        
        if not self.refresh_token:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": self.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data["access_token"]
                    
                    # Update credentials
                    self.credentials.credentials["access_token"] = self.access_token
                    
                    logger.info("YouTube access token refreshed successfully")
                    return True
                else:
                    logger.error(f"Token refresh failed: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False
    
    async def publish_content(self, payload: ContentPayload) -> PublishResult:
        """Publish video to YouTube"""
        
        if payload.content_type != ContentType.VIDEO:
            return PublishResult(
                success=False,
                platform="youtube",
                status=PublishStatus.FAILED,
                error="YouTube only supports video content"
            )
        
        if not payload.file_paths:
            return PublishResult(
                success=False,
                platform="youtube",
                status=PublishStatus.FAILED,
                error="No video file provided"
            )
        
        video_path = payload.file_paths[0]
        
        try:
            # Step 1: Upload video
            upload_result = await self._upload_video(video_path, payload)
            
            if not upload_result["success"]:
                return PublishResult(
                    success=False,
                    platform="youtube",
                    status=PublishStatus.FAILED,
                    error=upload_result["error"]
                )
            
            video_id = upload_result["video_id"]
            
            # Step 2: Set as YouTube Short if applicable
            await self._configure_as_short(video_id, payload)
            
            # Generate YouTube URL
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            return PublishResult(
                success=True,
                platform="youtube",
                post_id=video_id,
                url=video_url,
                status=PublishStatus.PUBLISHED,
                metadata={
                    "video_id": video_id,
                    "video_url": video_url,
                    "upload_time": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"YouTube publishing failed: {e}")
            return PublishResult(
                success=False,
                platform="youtube",
                status=PublishStatus.FAILED,
                error=str(e)
            )
    
    async def _upload_video(self, video_path: str, payload: ContentPayload) -> Dict[str, Any]:
        """Upload video file to YouTube"""
        
        # Prepare video metadata
        video_metadata = {
            "snippet": {
                "title": payload.title or "Untitled Video",
                "description": self._format_description(payload),
                "tags": payload.tags[:10] if payload.tags else [],  # Max 10 tags
                "categoryId": "22",  # People & Blogs
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en"
            },
            "status": {
                "privacyStatus": payload.privacy,
                "selfDeclaredMadeForKids": False
            }
        }
        
        # Add thumbnail if provided
        if payload.thumbnail_path and os.path.exists(payload.thumbnail_path):
            video_metadata["snippet"]["thumbnails"] = {
                "default": {"url": payload.thumbnail_path}
            }
        
        try:
            # Upload using resumable upload
            async with httpx.AsyncClient(timeout=300.0) as client:
                
                # Step 1: Initiate resumable upload
                init_response = await client.post(
                    f"{self.upload_base}/videos",
                    params={
                        "uploadType": "resumable",
                        "part": "snippet,status"
                    },
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                        "X-Upload-Content-Type": "video/*"
                    },
                    json=video_metadata
                )
                
                if init_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Upload initiation failed: {init_response.text}"
                    }
                
                upload_url = init_response.headers.get("Location")
                if not upload_url:
                    return {
                        "success": False,
                        "error": "No upload URL received"
                    }
                
                # Step 2: Upload video file
                with open(video_path, "rb") as video_file:
                    video_data = video_file.read()
                
                upload_response = await client.put(
                    upload_url,
                    content=video_data,
                    headers={
                        "Content-Type": "video/*",
                        "Content-Length": str(len(video_data))
                    }
                )
                
                if upload_response.status_code not in [200, 201]:
                    return {
                        "success": False,
                        "error": f"Video upload failed: {upload_response.text}"
                    }
                
                # Parse response
                upload_data = upload_response.json()
                video_id = upload_data.get("id")
                
                if not video_id:
                    return {
                        "success": False,
                        "error": "No video ID returned from upload"
                    }
                
                return {
                    "success": True,
                    "video_id": video_id,
                    "response": upload_data
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }
    
    async def _configure_as_short(self, video_id: str, payload: ContentPayload):
        """Configure video as YouTube Short if applicable"""
        
        # Check if video should be a Short (vertical, under 60 seconds)
        video_info = payload.metadata.get("video_info", {})
        duration = video_info.get("duration", 0)
        is_vertical = video_info.get("aspect_ratio", 1) < 1
        
        if is_vertical and duration <= 60:
            try:
                # Add #Shorts to description if not already there
                async with httpx.AsyncClient() as client:
                    # Get current video details
                    response = await client.get(
                        f"{self.api_base}/videos",
                        params={
                            "part": "snippet",
                            "id": video_id
                        },
                        headers={"Authorization": f"Bearer {self.access_token}"}
                    )
                    
                    if response.status_code == 200:
                        video_data = response.json()
                        if video_data.get("items"):
                            current_description = video_data["items"][0]["snippet"]["description"]
                            
                            if "#Shorts" not in current_description:
                                updated_description = f"{current_description}\n\n#Shorts"
                                
                                # Update video with #Shorts tag
                                await client.put(
                                    f"{self.api_base}/videos",
                                    params={"part": "snippet"},
                                    headers={
                                        "Authorization": f"Bearer {self.access_token}",
                                        "Content-Type": "application/json"
                                    },
                                    json={
                                        "id": video_id,
                                        "snippet": {
                                            **video_data["items"][0]["snippet"],
                                            "description": updated_description
                                        }
                                    }
                                )
                                
                                logger.info(f"Configured video {video_id} as YouTube Short")
            
            except Exception as e:
                logger.warning(f"Could not configure as Short: {e}")
    
    def _format_description(self, payload: ContentPayload) -> str:
        """Format video description"""
        
        description_parts = []
        
        if payload.description:
            description_parts.append(payload.description)
        elif payload.caption:
            description_parts.append(payload.caption)
        
        # Add hashtags
        if payload.hashtags:
            hashtags = " ".join(f"#{tag}" for tag in payload.hashtags)
            description_parts.append(hashtags)
        
        # Add ClipFlow credit
        description_parts.append("\n🤖 Generated with ClipFlow")
        
        return "\n\n".join(description_parts)
    
    async def schedule_content(self, payload: ContentPayload, publish_time: str) -> PublishResult:
        """Schedule content for future publishing"""
        
        # YouTube doesn't support direct scheduling via API for regular users
        # This would require YouTube Studio API or manual scheduling
        
        return PublishResult(
            success=False,
            platform="youtube",
            status=PublishStatus.FAILED,
            error="YouTube API doesn't support scheduling for regular users"
        )
    
    async def get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get video metrics from YouTube Analytics"""
        
        try:
            async with httpx.AsyncClient() as client:
                # Get basic video statistics
                response = await client.get(
                    f"{self.api_base}/videos",
                    params={
                        "part": "statistics,snippet",
                        "id": post_id
                    },
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                
                if response.status_code != 200:
                    return {"error": f"Failed to get metrics: {response.text}"}
                
                data = response.json()
                if not data.get("items"):
                    return {"error": "Video not found"}
                
                video_data = data["items"][0]
                stats = video_data.get("statistics", {})
                snippet = video_data.get("snippet", {})
                
                return {
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "shares": int(stats.get("favoriteCount", 0)),
                    "title": snippet.get("title", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "duration": snippet.get("duration", ""),
                    "video_url": f"https://www.youtube.com/watch?v={post_id}",
                    "platform": "youtube"
                }
                
        except Exception as e:
            logger.error(f"Error getting YouTube metrics: {e}")
            return {"error": str(e)}
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete YouTube video"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.api_base}/videos",
                    params={"id": post_id},
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                
                return response.status_code == 204
                
        except Exception as e:
            logger.error(f"Error deleting YouTube video: {e}")
            return False
    
    def validate_payload(self, payload: ContentPayload) -> List[str]:
        """Validate content for YouTube requirements"""
        
        errors = []
        
        # Content type check
        if payload.content_type != ContentType.VIDEO:
            errors.append("YouTube only accepts video content")
        
        # File check
        if not payload.file_paths:
            errors.append("No video file provided")
        elif not os.path.exists(payload.file_paths[0]):
            errors.append("Video file does not exist")
        
        # File size check (128GB limit)
        if payload.file_paths and os.path.exists(payload.file_paths[0]):
            if not self._validate_file_size(payload.file_paths[0], 128 * 1024):  # 128GB
                errors.append("Video file exceeds 128GB limit")
        
        # Title check
        if len(payload.title) > 100:
            errors.append("Title exceeds 100 character limit")
        
        # Description check
        description = self._format_description(payload)
        if len(description) > 5000:
            errors.append("Description exceeds 5000 character limit")
        
        # Tags check
        if payload.tags and len(payload.tags) > 10:
            errors.append("Maximum 10 tags allowed")
        
        for tag in payload.tags:
            if len(tag) > 30:
                errors.append(f"Tag '{tag}' exceeds 30 character limit")
        
        return errors
    
    def get_platform_limits(self) -> Dict[str, Any]:
        """Get YouTube platform limits"""
        
        return {
            "max_file_size_gb": 128,
            "max_duration_hours": 12,
            "max_title_length": 100,
            "max_description_length": 5000,
            "max_tags": 10,
            "max_tag_length": 30,
            "supported_formats": ["mp4", "mov", "avi", "wmv", "mpg", "flv", "webm"],
            "shorts_max_duration": 60,
            "shorts_aspect_ratio": "vertical",
            "upload_quota": "6 hours per 24 hours for verified accounts"
        }

# OAuth2 helper functions
class YouTubeOAuth:
    """Helper class for YouTube OAuth2 flow"""
    
    @staticmethod
    def get_auth_url(client_id: str, redirect_uri: str) -> str:
        """Generate YouTube OAuth2 authorization URL"""
        
        scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.readonly"
        ]
        
        scope_string = " ".join(scopes)
        
        return (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope_string}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"prompt=consent"
        )
    
    @staticmethod
    async def exchange_code_for_tokens(client_id: str, client_secret: str,
                                     code: str, redirect_uri: str) -> Dict[str, str]:
        """Exchange authorization code for access tokens"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Token exchange failed: {response.text}")
                    
        except Exception as e:
            raise Exception(f"OAuth2 exchange error: {e}")

# Example usage
async def main():
    # Setup credentials (in real app, these would come from secure storage)
    credentials = PlatformCredentials(
        platform="youtube",
        credentials={
            "client_id": "your_client_id",
            "client_secret": "your_client_secret", 
            "access_token": "your_access_token"
        },
        refresh_token="your_refresh_token"
    )
    
    publisher = YouTubePublisher(credentials)
    
    # Test authentication
    if await publisher.authenticate():
        print("✅ YouTube authentication successful")
        
        # Create video payload
        payload = ContentPayload(
            content_type=ContentType.VIDEO,
            file_paths=["video.mp4"],
            title="Amazing Short Video",
            description="Check out this awesome content!",
            tags=["shorts", "viral", "amazing"],
            privacy="public",
            metadata={
                "video_info": {
                    "duration": 45,
                    "aspect_ratio": 0.56  # Vertical
                }
            }
        )
        
        # Publish video
        result = await publisher.publish_content(payload)
        
        if result.success:
            print(f"✅ Video published: {result.url}")
            
            # Get metrics after some time
            await asyncio.sleep(60)  # Wait a minute
            metrics = await publisher.get_post_metrics(result.post_id)
            print(f"📊 Metrics: {metrics}")
        else:
            print(f"❌ Publishing failed: {result.error}")
    else:
        print("❌ YouTube authentication failed")

if __name__ == "__main__":
    asyncio.run(main())