#!/usr/bin/env python3
"""
Universal Content Processing Pipeline
Handles video, photo, text, audio → Multi-platform optimization
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

class ContentType(Enum):
    VIDEO = "video"
    PHOTO = "photo" 
    TEXT = "text"
    AUDIO = "audio"
    DOCUMENT = "document"

class Platform(Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"

@dataclass
class ContentItem:
    """Base content item"""
    id: str
    user_id: int
    content_type: ContentType
    file_path: Optional[str] = None
    text_content: Optional[str] = None
    caption: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass 
class ProcessingResult:
    """Result of content processing"""
    success: bool
    platform: Platform
    output_path: Optional[str] = None
    caption: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ContentProcessor:
    """Universal content processor"""
    
    def __init__(self, data_dir: str = "data", temp_dir: str = "temp"):
        self.data_dir = Path(data_dir)
        self.temp_dir = Path(temp_dir)
        self.content_dir = self.data_dir / "content"
        
        # Create directories
        for dir_path in [self.data_dir, self.temp_dir, self.content_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def process_content(self, content: ContentItem, target_platforms: List[Platform]) -> List[ProcessingResult]:
        """Process content for multiple platforms"""
        results = []
        
        logger.info(f"Processing {content.content_type.value} for platforms: {[p.value for p in target_platforms]}")
        
        for platform in target_platforms:
            try:
                result = await self._process_for_platform(content, platform)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {content.content_type.value} for {platform.value}: {e}")
                results.append(ProcessingResult(
                    success=False,
                    platform=platform,
                    error=str(e)
                ))
        
        return results
    
    async def _process_for_platform(self, content: ContentItem, platform: Platform) -> ProcessingResult:
        """Process content for specific platform"""
        
        if content.content_type == ContentType.VIDEO:
            return await self._process_video(content, platform)
        elif content.content_type == ContentType.PHOTO:
            return await self._process_photo(content, platform)
        elif content.content_type == ContentType.TEXT:
            return await self._process_text(content, platform)
        elif content.content_type == ContentType.AUDIO:
            return await self._process_audio(content, platform)
        else:
            return ProcessingResult(
                success=False,
                platform=platform,
                error=f"Unsupported content type: {content.content_type.value}"
            )
    
    async def _process_video(self, content: ContentItem, platform: Platform) -> ProcessingResult:
        """Process video for specific platform"""
        
        # Platform-specific video processing rules
        specs = self._get_video_specs(platform)
        
        # Generate unique output filename
        output_name = f"{content.id}_{platform.value}.mp4"
        output_path = self.content_dir / content.user_id / "videos" / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # TODO: Implement actual video processing with ffmpeg
        # For now, create placeholder
        logger.info(f"Processing video for {platform.value} with specs: {specs}")
        
        # Simulate processing
        await asyncio.sleep(1)
        
        # Generate platform-specific caption
        caption = self._generate_caption(content, platform)
        
        return ProcessingResult(
            success=True,
            platform=platform,
            output_path=str(output_path),
            caption=caption,
            metadata={
                "specs": specs,
                "duration": content.metadata.get("duration", 0),
                "aspect_ratio": specs["aspect_ratio"]
            }
        )
    
    async def _process_photo(self, content: ContentItem, platform: Platform) -> ProcessingResult:
        """Process photo for specific platform"""
        
        specs = self._get_photo_specs(platform)
        
        output_name = f"{content.id}_{platform.value}.jpg"
        output_path = self.content_dir / str(content.user_id) / "photos" / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Processing photo for {platform.value} with specs: {specs}")
        
        # TODO: Implement image processing with Pillow
        await asyncio.sleep(0.5)
        
        caption = self._generate_caption(content, platform)
        
        return ProcessingResult(
            success=True,
            platform=platform,
            output_path=str(output_path),
            caption=caption,
            metadata={"specs": specs}
        )
    
    async def _process_text(self, content: ContentItem, platform: Platform) -> ProcessingResult:
        """Process text content for specific platform"""
        
        specs = self._get_text_specs(platform)
        text = content.text_content or content.caption
        
        # Format text according to platform rules
        formatted_text = self._format_text_for_platform(text, platform, specs)
        
        # Generate visual if needed
        visual_path = None
        if specs.get("create_visual", False):
            visual_name = f"{content.id}_{platform.value}_text.jpg"
            visual_path = self.content_dir / str(content.user_id) / "visuals" / visual_name
            visual_path.parent.mkdir(parents=True, exist_ok=True)
            
            # TODO: Create text visual with PIL
            logger.info(f"Creating text visual for {platform.value}")
        
        return ProcessingResult(
            success=True,
            platform=platform,
            output_path=str(visual_path) if visual_path else None,
            caption=formatted_text,
            metadata={"specs": specs, "original_length": len(text)}
        )
    
    async def _process_audio(self, content: ContentItem, platform: Platform) -> ProcessingResult:
        """Process audio for specific platform"""
        
        specs = self._get_audio_specs(platform)
        
        output_name = f"{content.id}_{platform.value}_audiogram.mp4"
        output_path = self.content_dir / str(content.user_id) / "audiograms" / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating audiogram for {platform.value} with specs: {specs}")
        
        # TODO: Create audiogram with waveform visualization
        await asyncio.sleep(2)
        
        caption = self._generate_caption(content, platform)
        
        return ProcessingResult(
            success=True,
            platform=platform,
            output_path=str(output_path),
            caption=caption,
            metadata={"specs": specs}
        )
    
    def _get_video_specs(self, platform: Platform) -> Dict[str, Any]:
        """Get video specifications for platform"""
        specs = {
            Platform.YOUTUBE: {
                "max_duration": 60,
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "fps": 30,
                "format": "mp4",
                "max_size_mb": 256
            },
            Platform.TIKTOK: {
                "max_duration": 180,
                "aspect_ratio": "9:16", 
                "resolution": "1080x1920",
                "fps": 30,
                "format": "mp4",
                "max_size_mb": 287
            },
            Platform.INSTAGRAM: {
                "max_duration": 90,
                "aspect_ratio": "9:16",
                "resolution": "1080x1920", 
                "fps": 30,
                "format": "mp4",
                "max_size_mb": 100
            },
            Platform.TWITTER: {
                "max_duration": 140,
                "aspect_ratio": "16:9",
                "resolution": "1920x1080",
                "fps": 30,
                "format": "mp4",
                "max_size_mb": 512
            },
            Platform.LINKEDIN: {
                "max_duration": 600,
                "aspect_ratio": "16:9",
                "resolution": "1920x1080",
                "fps": 30,
                "format": "mp4",
                "max_size_mb": 200
            }
        }
        
        return specs.get(platform, specs[Platform.YOUTUBE])
    
    def _get_photo_specs(self, platform: Platform) -> Dict[str, Any]:
        """Get photo specifications for platform"""
        specs = {
            Platform.INSTAGRAM: {
                "formats": ["1:1", "4:5", "9:16"],
                "max_resolution": "1080x1080",
                "format": "jpg",
                "quality": 95
            },
            Platform.TWITTER: {
                "formats": ["16:9", "1:1"],
                "max_resolution": "1024x512",
                "format": "jpg", 
                "quality": 85
            },
            Platform.LINKEDIN: {
                "formats": ["1.91:1", "1:1"],
                "max_resolution": "1200x628",
                "format": "jpg",
                "quality": 90
            }
        }
        
        return specs.get(platform, specs[Platform.INSTAGRAM])
    
    def _get_text_specs(self, platform: Platform) -> Dict[str, Any]:
        """Get text specifications for platform"""
        specs = {
            Platform.TWITTER: {
                "max_chars": 280,
                "hashtags": 2,
                "thread_support": True,
                "create_visual": False
            },
            Platform.INSTAGRAM: {
                "max_chars": 2200,
                "hashtags": 30,
                "thread_support": False,
                "create_visual": True
            },
            Platform.LINKEDIN: {
                "max_chars": 3000,
                "hashtags": 5,
                "thread_support": False,
                "create_visual": False
            }
        }
        
        return specs.get(platform, specs[Platform.TWITTER])
    
    def _get_audio_specs(self, platform: Platform) -> Dict[str, Any]:
        """Get audio processing specs for platform"""
        return {
            "waveform_style": "bars",
            "background_color": "#1DA1F2",
            "duration_limit": 60,
            "output_format": "mp4"
        }
    
    def _format_text_for_platform(self, text: str, platform: Platform, specs: Dict[str, Any]) -> str:
        """Format text according to platform requirements"""
        max_chars = specs.get("max_chars", 280)
        
        # Truncate if too long
        if len(text) > max_chars:
            if specs.get("thread_support", False):
                # Create thread format
                return f"{text[:max_chars-5]}... [1/n thread]"
            else:
                return text[:max_chars-3] + "..."
        
        # Add platform-specific formatting
        if platform == Platform.TWITTER:
            # Add relevant hashtags
            if not any(word.startswith("#") for word in text.split()):
                text += " #ClipFlow"
        
        elif platform == Platform.LINKEDIN:
            # Professional formatting
            if not text.endswith("."):
                text += "."
        
        return text
    
    def _generate_caption(self, content: ContentItem, platform: Platform) -> str:
        """Generate platform-specific caption"""
        base_caption = content.caption or ""
        
        # Platform-specific caption enhancement
        if platform == Platform.TIKTOK:
            return f"{base_caption} 🎵 #fyp #viral #ClipFlow"
        elif platform == Platform.INSTAGRAM:
            return f"{base_caption} ✨\n\n#reels #content #ClipFlow"
        elif platform == Platform.YOUTUBE:
            return f"{base_caption}\n\nCreated with #ClipFlow #Shorts"
        elif platform == Platform.TWITTER:
            return f"{base_caption} 🚀 #ClipFlow"
        elif platform == Platform.LINKEDIN:
            return f"{base_caption}\n\n#ContentCreation #Automation"
        
        return base_caption

class ContentManager:
    """Manages content items and processing queue"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.processor = ContentProcessor(data_dir)
        self.queue_file = self.data_dir / "processing_queue.json"
        
    async def add_content(self, user_id: int, content_type: ContentType, 
                         file_path: str = None, text_content: str = None, 
                         caption: str = None, metadata: Dict[str, Any] = None) -> ContentItem:
        """Add new content item"""
        
        # Generate unique content ID
        content_id = self._generate_content_id(user_id, content_type, file_path or text_content)
        
        content = ContentItem(
            id=content_id,
            user_id=user_id,
            content_type=content_type,
            file_path=file_path,
            text_content=text_content,
            caption=caption,
            metadata=metadata or {}
        )
        
        # Save content metadata
        await self._save_content_metadata(content)
        
        return content
    
    async def process_content(self, content: ContentItem, platforms: List[Platform]) -> List[ProcessingResult]:
        """Process content for multiple platforms"""
        return await self.processor.process_content(content, platforms)
    
    def _generate_content_id(self, user_id: int, content_type: ContentType, data: str) -> str:
        """Generate unique content ID"""
        hash_input = f"{user_id}_{content_type.value}_{data}_{os.urandom(8).hex()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    async def _save_content_metadata(self, content: ContentItem):
        """Save content metadata to disk"""
        metadata_dir = self.data_dir / str(content.user_id) / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_dir / f"{content.id}.json"
        
        metadata = {
            "id": content.id,
            "user_id": content.user_id,
            "content_type": content.content_type.value,
            "file_path": content.file_path,
            "text_content": content.text_content,
            "caption": content.caption,
            "metadata": content.metadata,
            "created_at": content.metadata.get("created_at", "")
        }
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

# Example usage
async def main():
    manager = ContentManager()
    
    # Example: Process a video
    video_content = await manager.add_content(
        user_id=12345,
        content_type=ContentType.VIDEO,
        file_path="input_video.mp4",
        caption="Amazing content!",
        metadata={"duration": 30, "width": 1080, "height": 1920}
    )
    
    platforms = [Platform.YOUTUBE, Platform.TIKTOK, Platform.INSTAGRAM]
    results = await manager.process_content(video_content, platforms)
    
    for result in results:
        if result.success:
            print(f"✅ {result.platform.value}: {result.output_path}")
        else:
            print(f"❌ {result.platform.value}: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())