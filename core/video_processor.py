#!/usr/bin/env python3
"""
Advanced Video Processing with FFmpeg
Handles platform-specific optimization, cropping, effects
"""

import subprocess
import asyncio
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)

@dataclass
class VideoInfo:
    """Video metadata information"""
    duration: float
    width: int
    height: int
    fps: float
    bitrate: int
    codec: str
    aspect_ratio: float
    file_size: int
    
    @property
    def is_vertical(self) -> bool:
        return self.height > self.width
    
    @property
    def is_square(self) -> bool:
        return abs(self.width - self.height) < 50
    
    @property
    def is_horizontal(self) -> bool:
        return self.width > self.height

@dataclass
class VideoSpecs:
    """Platform-specific video specifications"""
    width: int
    height: int
    fps: int
    max_duration: int
    max_bitrate: int
    max_file_size: int  # in bytes
    codec: str = "libx264"
    audio_codec: str = "aac"
    format: str = "mp4"

class VideoProcessor:
    """Advanced video processor using FFmpeg"""
    
    def __init__(self, temp_dir: str = "temp", output_dir: str = "data/content"):
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)
        
        for dir_path in [self.temp_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def get_video_info(self, video_path: str) -> VideoInfo:
        """Extract video metadata using ffprobe"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        try:
            result = await self._run_command(cmd)
            data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = next(
                (s for s in data["streams"] if s["codec_type"] == "video"),
                None
            )
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            format_info = data["format"]
            
            return VideoInfo(
                duration=float(format_info.get("duration", 0)),
                width=int(video_stream["width"]),
                height=int(video_stream["height"]),
                fps=self._parse_fps(video_stream.get("r_frame_rate", "30/1")),
                bitrate=int(format_info.get("bit_rate", 0)),
                codec=video_stream.get("codec_name", "unknown"),
                aspect_ratio=int(video_stream["width"]) / int(video_stream["height"]),
                file_size=int(format_info.get("size", 0))
            )
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise
    
    async def process_for_platform(self, input_path: str, platform: str, 
                                  user_id: int, content_id: str,
                                  brand_config: Optional[Dict] = None) -> str:
        """Process video for specific platform"""
        
        specs = self._get_platform_specs(platform)
        video_info = await self.get_video_info(input_path)
        
        # Generate output path
        output_name = f"{content_id}_{platform}.{specs.format}"
        output_path = self.output_dir / str(user_id) / "videos" / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Processing video for {platform}: {specs.width}x{specs.height}")
        
        # Build FFmpeg command
        cmd = await self._build_ffmpeg_command(
            input_path, str(output_path), specs, video_info, brand_config
        )
        
        # Execute processing
        await self._run_command(cmd, timeout=300)  # 5 minute timeout
        
        # Verify output
        if not output_path.exists():
            raise RuntimeError(f"Video processing failed - no output file")
        
        # Check file size
        output_size = output_path.stat().st_size
        if output_size > specs.max_file_size:
            logger.warning(f"Output file too large: {output_size / 1024 / 1024:.1f}MB")
            # Re-encode with lower bitrate
            await self._compress_video(str(output_path), specs)
        
        return str(output_path)
    
    async def _build_ffmpeg_command(self, input_path: str, output_path: str,
                                   specs: VideoSpecs, video_info: VideoInfo,
                                   brand_config: Optional[Dict] = None) -> List[str]:
        """Build FFmpeg command for platform-specific processing"""
        
        cmd = ["ffmpeg", "-i", input_path, "-y"]  # -y to overwrite
        
        # Video filters
        filters = []
        
        # 1. Crop/Scale to target aspect ratio
        crop_scale_filter = self._get_crop_scale_filter(video_info, specs)
        if crop_scale_filter:
            filters.append(crop_scale_filter)
        
        # 2. Frame rate adjustment
        if video_info.fps > specs.fps:
            filters.append(f"fps={specs.fps}")
        
        # 3. Brand overlay (logo/watermark)
        if brand_config and brand_config.get("logo_path"):
            overlay_filter = self._get_brand_overlay_filter(brand_config, specs)
            if overlay_filter:
                filters.append(overlay_filter)
        
        # 4. Duration limiting
        if video_info.duration > specs.max_duration:
            # Smart trimming - keep middle section
            start_time = (video_info.duration - specs.max_duration) / 2
            cmd.extend(["-ss", str(start_time), "-t", str(specs.max_duration)])
        
        # Apply video filters
        if filters:
            cmd.extend(["-vf", ",".join(filters)])
        
        # Video encoding settings
        cmd.extend([
            "-c:v", specs.codec,
            "-preset", "fast",
            "-crf", "23",  # Good quality/size balance
            "-maxrate", f"{specs.max_bitrate}k",
            "-bufsize", f"{specs.max_bitrate * 2}k"
        ])
        
        # Audio settings
        cmd.extend([
            "-c:a", specs.audio_codec,
            "-b:a", "128k",
            "-ar", "44100"
        ])
        
        # Output format
        cmd.extend(["-f", specs.format, output_path])
        
        return cmd
    
    def _get_crop_scale_filter(self, video_info: VideoInfo, specs: VideoSpecs) -> Optional[str]:
        """Generate crop and scale filter for target aspect ratio"""
        
        target_aspect = specs.width / specs.height
        source_aspect = video_info.aspect_ratio
        
        if abs(target_aspect - source_aspect) < 0.01:
            # Same aspect ratio, just scale
            return f"scale={specs.width}:{specs.height}"
        
        if target_aspect > source_aspect:
            # Target is wider - crop height, pad width
            new_height = int(video_info.width / target_aspect)
            crop_y = (video_info.height - new_height) // 2
            return f"crop={video_info.width}:{new_height}:0:{crop_y},scale={specs.width}:{specs.height}"
        else:
            # Target is taller - crop width, pad height  
            new_width = int(video_info.height * target_aspect)
            crop_x = (video_info.width - new_width) // 2
            return f"crop={new_width}:{video_info.height}:{crop_x}:0,scale={specs.width}:{specs.height}"
    
    def _get_brand_overlay_filter(self, brand_config: Dict, specs: VideoSpecs) -> Optional[str]:
        """Generate brand overlay filter"""
        logo_path = brand_config.get("logo_path")
        if not logo_path or not os.path.exists(logo_path):
            return None
        
        # Logo position and size
        position = brand_config.get("position", "bottom-right")
        opacity = brand_config.get("opacity", 0.8)
        size_percent = brand_config.get("size_percent", 15)  # 15% of video width
        
        logo_width = int(specs.width * size_percent / 100)
        
        # Position coordinates
        positions = {
            "top-left": (10, 10),
            "top-right": (f"W-w-10", 10),
            "bottom-left": (10, f"H-h-10"),
            "bottom-right": (f"W-w-10", f"H-h-10"),
            "center": (f"(W-w)/2", f"(H-h)/2")
        }
        
        x, y = positions.get(position, positions["bottom-right"])
        
        return f"movie={logo_path}:loop=0,setpts=N/(FRAME_RATE*TB),scale={logo_width}:-1,format=rgba,colorchannelmixer=aa={opacity}[logo];[0:v][logo]overlay={x}:{y}"
    
    def _get_platform_specs(self, platform: str) -> VideoSpecs:
        """Get platform-specific video specifications"""
        
        specs = {
            "youtube": VideoSpecs(
                width=1080, height=1920, fps=30, max_duration=60,
                max_bitrate=8000, max_file_size=256 * 1024 * 1024
            ),
            "tiktok": VideoSpecs(
                width=1080, height=1920, fps=30, max_duration=180,
                max_bitrate=6000, max_file_size=287 * 1024 * 1024
            ),
            "instagram": VideoSpecs(
                width=1080, height=1920, fps=30, max_duration=90,
                max_bitrate=5000, max_file_size=100 * 1024 * 1024
            ),
            "twitter": VideoSpecs(
                width=1920, height=1080, fps=30, max_duration=140,
                max_bitrate=6000, max_file_size=512 * 1024 * 1024
            ),
            "linkedin": VideoSpecs(
                width=1920, height=1080, fps=30, max_duration=600,
                max_bitrate=5000, max_file_size=200 * 1024 * 1024
            )
        }
        
        return specs.get(platform.lower(), specs["youtube"])
    
    async def _compress_video(self, video_path: str, specs: VideoSpecs):
        """Compress video to meet file size requirements"""
        temp_path = f"{video_path}.temp"
        
        # Calculate target bitrate to meet file size
        video_info = await self.get_video_info(video_path)
        target_bitrate = int((specs.max_file_size * 8) / video_info.duration / 1024 * 0.9)  # 90% margin
        
        cmd = [
            "ffmpeg", "-i", video_path, "-y",
            "-c:v", specs.codec,
            "-b:v", f"{target_bitrate}k",
            "-maxrate", f"{target_bitrate}k",
            "-bufsize", f"{target_bitrate * 2}k",
            "-c:a", specs.audio_codec,
            "-b:a", "96k",
            temp_path
        ]
        
        await self._run_command(cmd)
        
        # Replace original with compressed
        os.replace(temp_path, video_path)
    
    def _parse_fps(self, fps_string: str) -> float:
        """Parse FPS from ffprobe output (e.g., '30/1' -> 30.0)"""
        try:
            if "/" in fps_string:
                num, den = fps_string.split("/")
                return float(num) / float(den)
            return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 30.0
    
    async def _run_command(self, cmd: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        """Run command asynchronously with timeout"""
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Command failed: {error_msg}")
            
            return type('Result', (), {
                'returncode': process.returncode,
                'stdout': stdout.decode(),
                'stderr': stderr.decode()
            })()
            
        except asyncio.TimeoutError:
            raise RuntimeError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {e}")

class SmartVideoAnalyzer:
    """Analyzes video content for optimal processing"""
    
    def __init__(self):
        self.processor = VideoProcessor()
    
    async def analyze_content(self, video_path: str) -> Dict[str, Any]:
        """Analyze video content and suggest optimal settings"""
        
        video_info = await self.processor.get_video_info(video_path)
        
        # Analyze content type
        content_type = self._detect_content_type(video_info)
        
        # Suggest platforms
        suggested_platforms = self._suggest_platforms(video_info, content_type)
        
        # Optimal cropping analysis
        crop_analysis = await self._analyze_optimal_crop(video_path, video_info)
        
        return {
            "video_info": video_info,
            "content_type": content_type,
            "suggested_platforms": suggested_platforms,
            "crop_analysis": crop_analysis,
            "processing_recommendations": self._get_processing_recommendations(video_info)
        }
    
    def _detect_content_type(self, video_info: VideoInfo) -> str:
        """Detect video content type based on characteristics"""
        
        if video_info.duration <= 15:
            return "story"
        elif video_info.duration <= 60 and video_info.is_vertical:
            return "short_vertical"
        elif video_info.duration <= 180:
            return "short_content"
        elif video_info.duration <= 600:
            return "medium_content"
        else:
            return "long_content"
    
    def _suggest_platforms(self, video_info: VideoInfo, content_type: str) -> List[str]:
        """Suggest optimal platforms for video"""
        
        suggestions = []
        
        # Vertical short videos
        if content_type in ["story", "short_vertical"] and video_info.is_vertical:
            suggestions.extend(["tiktok", "youtube", "instagram"])
        
        # Horizontal videos
        elif video_info.is_horizontal:
            if video_info.duration <= 140:
                suggestions.extend(["twitter", "linkedin"])
            else:
                suggestions.append("linkedin")
        
        # Square videos
        elif video_info.is_square:
            suggestions.extend(["instagram", "twitter"])
        
        return suggestions
    
    async def _analyze_optimal_crop(self, video_path: str, video_info: VideoInfo) -> Dict[str, Any]:
        """Analyze optimal cropping regions for different aspect ratios"""
        
        # For advanced implementation, could use computer vision to detect
        # faces, text, or important regions for optimal cropping
        
        return {
            "has_faces": False,  # TODO: Face detection
            "text_regions": [],  # TODO: Text detection
            "motion_areas": [],  # TODO: Motion analysis
            "recommended_crops": {
                "9:16": {"x": 0, "y": 0, "confidence": 0.8},
                "1:1": {"x": 0, "y": 0, "confidence": 0.7},
                "16:9": {"x": 0, "y": 0, "confidence": 0.9}
            }
        }
    
    def _get_processing_recommendations(self, video_info: VideoInfo) -> Dict[str, Any]:
        """Get processing recommendations based on video analysis"""
        
        recommendations = {
            "quality_preset": "balanced",
            "effects": [],
            "transitions": [],
            "audio_processing": []
        }
        
        # Quality preset based on input quality
        if video_info.bitrate < 2000000:  # Low bitrate
            recommendations["quality_preset"] = "quality"
        elif video_info.bitrate > 8000000:  # High bitrate
            recommendations["quality_preset"] = "fast"
        
        # Suggest effects based on content
        if video_info.fps < 24:
            recommendations["effects"].append("frame_interpolation")
        
        if video_info.duration > 60:
            recommendations["effects"].append("highlight_detection")
        
        return recommendations

# Example usage
async def main():
    processor = VideoProcessor()
    analyzer = SmartVideoAnalyzer()
    
    # Analyze video
    video_path = "input.mp4"
    analysis = await analyzer.analyze_content(video_path)
    
    print(f"Content type: {analysis['content_type']}")
    print(f"Suggested platforms: {analysis['suggested_platforms']}")
    
    # Process for platforms
    brand_config = {
        "logo_path": "logo.png",
        "position": "bottom-right",
        "opacity": 0.7,
        "size_percent": 12
    }
    
    for platform in analysis['suggested_platforms']:
        try:
            output_path = await processor.process_for_platform(
                video_path, platform, user_id=12345, content_id="test123",
                brand_config=brand_config
            )
            print(f"✅ {platform}: {output_path}")
        except Exception as e:
            print(f"❌ {platform}: {e}")

if __name__ == "__main__":
    asyncio.run(main())