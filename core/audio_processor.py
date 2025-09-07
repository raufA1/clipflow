#!/usr/bin/env python3
"""
Audio Processing and Audiogram Generation
Converts audio to visual waveforms, podcasts to video clips, voice to text
"""

import os
import asyncio
import subprocess
import json
import wave
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

@dataclass
class AudioInfo:
    """Audio metadata information"""
    duration: float
    sample_rate: int
    channels: int
    bitrate: int
    format: str
    file_size: int

@dataclass
class AudiogramConfig:
    """Audiogram visual configuration"""
    width: int = 1080
    height: int = 1920
    background_color: str = "#1DA1F2"
    waveform_color: str = "#FFFFFF"
    text_color: str = "#FFFFFF"
    accent_color: str = "#FFD700"
    fps: int = 30
    waveform_style: str = "bars"  # bars, line, circle
    show_progress: bool = True
    show_title: bool = True

class AudioProcessor:
    """Advanced audio processing with visualization"""
    
    def __init__(self, temp_dir: str = "temp", output_dir: str = "data/content"):
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)
        
        for dir_path in [self.temp_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def get_audio_info(self, audio_path: str) -> AudioInfo:
        """Extract audio metadata using ffprobe"""
        
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json", 
            "-show_format",
            "-show_streams",
            audio_path
        ]
        
        try:
            result = await self._run_command(cmd)
            data = json.loads(result.stdout)
            
            # Find audio stream
            audio_stream = next(
                (s for s in data["streams"] if s["codec_type"] == "audio"),
                None
            )
            
            if not audio_stream:
                raise ValueError("No audio stream found")
            
            format_info = data["format"]
            
            return AudioInfo(
                duration=float(format_info.get("duration", 0)),
                sample_rate=int(audio_stream.get("sample_rate", 44100)),
                channels=int(audio_stream.get("channels", 2)),
                bitrate=int(format_info.get("bit_rate", 0)),
                format=format_info.get("format_name", "unknown"),
                file_size=int(format_info.get("size", 0))
            )
            
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            raise
    
    async def create_audiogram(self, audio_path: str, platform: str = "instagram",
                             user_id: int = 0, content_id: str = "",
                             title: str = "", config: Optional[AudiogramConfig] = None,
                             brand_config: Optional[Dict] = None) -> str:
        """Create audiogram video from audio file"""
        
        if config is None:
            config = self._get_platform_audiogram_config(platform)
        
        # Apply brand customization
        if brand_config:
            config = self._customize_audiogram_config(config, brand_config)
        
        audio_info = await self.get_audio_info(audio_path)
        
        # Extract audio waveform data
        waveform_data = await self._extract_waveform_data(audio_path, config.fps)
        
        # Generate video frames
        frames_dir = self.temp_dir / f"frames_{content_id}"
        frames_dir.mkdir(exist_ok=True)
        
        await self._generate_audiogram_frames(
            waveform_data, frames_dir, config, title, audio_info
        )
        
        # Create video from frames and audio
        output_name = f"{content_id}_audiogram_{platform}.mp4"
        output_path = self.output_dir / str(user_id) / "audiograms" / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        await self._create_video_from_frames(
            str(frames_dir), audio_path, str(output_path), config.fps
        )
        
        # Cleanup frames
        await self._cleanup_frames(frames_dir)
        
        return str(output_path)
    
    async def extract_audio_highlights(self, audio_path: str, segment_length: int = 30,
                                     num_segments: int = 3) -> List[str]:
        """Extract highlight segments from audio"""
        
        audio_info = await self.get_audio_info(audio_path)
        
        if audio_info.duration <= segment_length:
            return [audio_path]  # Audio is already short enough
        
        # Calculate segment positions
        segments = []
        segment_duration = min(segment_length, audio_info.duration / num_segments)
        
        for i in range(num_segments):
            start_time = i * (audio_info.duration / num_segments)
            end_time = start_time + segment_duration
            
            segment_path = self.temp_dir / f"segment_{i}_{os.path.basename(audio_path)}"
            
            # Extract segment
            cmd = [
                "ffmpeg", "-i", audio_path, "-y",
                "-ss", str(start_time),
                "-t", str(segment_duration),
                "-c", "copy",
                str(segment_path)
            ]
            
            await self._run_command(cmd)
            segments.append(str(segment_path))
        
        return segments
    
    async def transcribe_audio(self, audio_path: str, language: str = "auto") -> str:
        """Transcribe audio to text using Whisper or similar"""
        
        # For now, return a placeholder
        # In real implementation, would use OpenAI Whisper or similar
        
        logger.info(f"Transcribing audio: {audio_path}")
        
        # Placeholder transcription
        return "This is a placeholder transcription. In a real implementation, this would use Whisper or another STT service to transcribe the audio content."
    
    async def create_podcast_clip(self, audio_path: str, start_time: float,
                                duration: float, title: str, 
                                speaker_names: List[str] = None,
                                user_id: int = 0, content_id: str = "") -> str:
        """Create podcast clip with speaker identification"""
        
        # Extract audio segment
        segment_path = self.temp_dir / f"podcast_segment_{content_id}.wav"
        
        cmd = [
            "ffmpeg", "-i", audio_path, "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-ac", "2",  # Stereo
            "-ar", "44100",  # Sample rate
            str(segment_path)
        ]
        
        await self._run_command(cmd)
        
        # Create audiogram for the segment
        config = AudiogramConfig(
            width=1080, height=1920,
            background_color="#2C3E50",
            waveform_color="#3498DB",
            text_color="#FFFFFF",
            show_title=True,
            waveform_style="bars"
        )
        
        # Add speaker info to title if available
        if speaker_names:
            title = f"{title}\n🎙️ {', '.join(speaker_names)}"
        
        return await self.create_audiogram(
            str(segment_path), "podcast", user_id, content_id, title, config
        )
    
    async def create_music_visualization(self, audio_path: str, style: str = "spectrum",
                                       user_id: int = 0, content_id: str = "") -> str:
        """Create music visualization video"""
        
        config = AudiogramConfig(
            width=1920, height=1080,  # Landscape for music
            background_color="#000000",
            waveform_color="#FF6B6B", 
            accent_color="#4ECDC4",
            waveform_style=style,
            show_progress=True,
            show_title=False
        )
        
        return await self.create_audiogram(
            audio_path, "music", user_id, content_id, "", config
        )
    
    def _get_platform_audiogram_config(self, platform: str) -> AudiogramConfig:
        """Get platform-specific audiogram configuration"""
        
        configs = {
            "instagram": AudiogramConfig(
                width=1080, height=1920,
                background_color="#E1306C",
                waveform_color="#FFFFFF"
            ),
            "instagram_post": AudiogramConfig(
                width=1080, height=1080,
                background_color="#E1306C", 
                waveform_color="#FFFFFF"
            ),
            "twitter": AudiogramConfig(
                width=1200, height=675,
                background_color="#1DA1F2",
                waveform_color="#FFFFFF"
            ),
            "linkedin": AudiogramConfig(
                width=1200, height=628,
                background_color="#0077B5",
                waveform_color="#FFFFFF"
            ),
            "podcast": AudiogramConfig(
                width=1080, height=1920,
                background_color="#2C3E50",
                waveform_color="#3498DB",
                show_title=True
            ),
            "music": AudiogramConfig(
                width=1920, height=1080,
                background_color="#000000",
                waveform_color="#FF6B6B",
                waveform_style="spectrum"
            )
        }
        
        return configs.get(platform, configs["instagram"])
    
    def _customize_audiogram_config(self, config: AudiogramConfig, brand_config: Dict) -> AudiogramConfig:
        """Customize audiogram with brand colors"""
        
        if "primary_color" in brand_config:
            config.background_color = brand_config["primary_color"]
        
        if "secondary_color" in brand_config:
            config.waveform_color = brand_config["secondary_color"]
        
        if "accent_color" in brand_config:
            config.accent_color = brand_config["accent_color"]
        
        return config
    
    async def _extract_waveform_data(self, audio_path: str, fps: int) -> np.ndarray:
        """Extract waveform data for visualization"""
        
        # Convert audio to raw format for processing
        raw_path = self.temp_dir / "temp_audio.wav"
        
        cmd = [
            "ffmpeg", "-i", audio_path, "-y",
            "-ac", "1",  # Mono
            "-ar", "22050",  # Lower sample rate for processing
            "-f", "wav",
            str(raw_path)
        ]
        
        await self._run_command(cmd)
        
        # Read WAV data
        try:
            with wave.open(str(raw_path), 'rb') as wav_file:
                frames = wav_file.readframes(-1)
                sample_rate = wav_file.getframerate()
                audio_data = np.frombuffer(frames, dtype=np.int16)
        except Exception as e:
            logger.error(f"Error reading WAV data: {e}")
            # Generate dummy data
            duration = 30  # seconds
            sample_rate = 22050
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        # Downsample for visualization frames
        samples_per_frame = len(audio_data) // (fps * len(audio_data) // sample_rate)
        if samples_per_frame == 0:
            samples_per_frame = 1
        
        # Calculate RMS values for each frame
        num_frames = len(audio_data) // samples_per_frame
        waveform_data = []
        
        for i in range(num_frames):
            start_idx = i * samples_per_frame
            end_idx = start_idx + samples_per_frame
            frame_data = audio_data[start_idx:end_idx]
            
            # Calculate RMS (Root Mean Square) for amplitude
            rms = np.sqrt(np.mean(frame_data.astype(np.float64) ** 2))
            waveform_data.append(rms)
        
        return np.array(waveform_data)
    
    async def _generate_audiogram_frames(self, waveform_data: np.ndarray, 
                                       frames_dir: Path, config: AudiogramConfig,
                                       title: str, audio_info: AudioInfo):
        """Generate individual frames for audiogram video"""
        
        total_frames = len(waveform_data)
        max_amplitude = np.max(waveform_data) if len(waveform_data) > 0 else 1
        
        for frame_idx in range(total_frames):
            img = Image.new("RGB", (config.width, config.height), config.background_color)
            draw = ImageDraw.Draw(img)
            
            # Draw title
            if config.show_title and title:
                await self._draw_title(draw, title, config)
            
            # Draw waveform
            await self._draw_waveform(
                draw, waveform_data[:frame_idx + 1], config, max_amplitude
            )
            
            # Draw progress bar
            if config.show_progress:
                progress = (frame_idx + 1) / total_frames
                await self._draw_progress_bar(draw, progress, config)
            
            # Draw timestamp
            current_time = (frame_idx + 1) / config.fps
            await self._draw_timestamp(draw, current_time, audio_info.duration, config)
            
            # Save frame
            frame_path = frames_dir / f"frame_{frame_idx:06d}.png"
            img.save(str(frame_path), "PNG")
        
        logger.info(f"Generated {total_frames} frames for audiogram")
    
    async def _draw_title(self, draw: ImageDraw.Draw, title: str, config: AudiogramConfig):
        """Draw title text on frame"""
        
        # Calculate title area
        title_area_height = config.height // 4
        margin = 40
        
        try:
            font_size = 48 if config.width >= 1080 else 36
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Word wrap title
        lines = self._wrap_text(title, font, config.width - 2 * margin, draw)
        
        # Center text vertically in title area
        line_height = font_size + 10
        total_text_height = len(lines) * line_height
        start_y = (title_area_height - total_text_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (config.width - text_width) // 2
            y = start_y + i * line_height
            
            draw.text((x, y), line, font=font, fill=config.text_color)
    
    async def _draw_waveform(self, draw: ImageDraw.Draw, waveform_data: np.ndarray,
                           config: AudiogramConfig, max_amplitude: float):
        """Draw waveform visualization"""
        
        if len(waveform_data) == 0:
            return
        
        # Calculate waveform area
        waveform_top = config.height // 3
        waveform_height = config.height // 3
        waveform_center = waveform_top + waveform_height // 2
        
        if config.waveform_style == "bars":
            await self._draw_bars_waveform(
                draw, waveform_data, config, max_amplitude, 
                waveform_top, waveform_height, waveform_center
            )
        elif config.waveform_style == "line":
            await self._draw_line_waveform(
                draw, waveform_data, config, max_amplitude,
                waveform_top, waveform_height, waveform_center
            )
        elif config.waveform_style == "circle":
            await self._draw_circle_waveform(
                draw, waveform_data, config, max_amplitude
            )
    
    async def _draw_bars_waveform(self, draw: ImageDraw.Draw, waveform_data: np.ndarray,
                                config: AudiogramConfig, max_amplitude: float,
                                waveform_top: int, waveform_height: int, waveform_center: int):
        """Draw bars-style waveform"""
        
        num_bars = min(len(waveform_data), 60)  # Max 60 bars
        bar_width = (config.width - 100) // num_bars
        bar_spacing = 2
        
        # Show recent data (sliding window)
        start_idx = max(0, len(waveform_data) - num_bars)
        recent_data = waveform_data[start_idx:]
        
        for i, amplitude in enumerate(recent_data):
            if max_amplitude > 0:
                normalized_amp = amplitude / max_amplitude
            else:
                normalized_amp = 0
            
            bar_height = int(normalized_amp * waveform_height * 0.8)  # 80% max height
            
            x = 50 + i * (bar_width + bar_spacing)
            y_top = waveform_center - bar_height // 2
            y_bottom = waveform_center + bar_height // 2
            
            # Color based on amplitude
            if normalized_amp > 0.7:
                color = config.accent_color
            else:
                color = config.waveform_color
            
            draw.rectangle([x, y_top, x + bar_width, y_bottom], fill=color)
    
    async def _draw_line_waveform(self, draw: ImageDraw.Draw, waveform_data: np.ndarray,
                                config: AudiogramConfig, max_amplitude: float,
                                waveform_top: int, waveform_height: int, waveform_center: int):
        """Draw line-style waveform"""
        
        if len(waveform_data) < 2:
            return
        
        points = []
        width_per_point = config.width / len(waveform_data)
        
        for i, amplitude in enumerate(waveform_data):
            if max_amplitude > 0:
                normalized_amp = amplitude / max_amplitude
            else:
                normalized_amp = 0
            
            x = int(i * width_per_point)
            y = waveform_center - int(normalized_amp * waveform_height * 0.4)
            points.append((x, y))
        
        # Draw connected line
        if len(points) > 1:
            for i in range(len(points) - 1):
                draw.line([points[i], points[i + 1]], fill=config.waveform_color, width=3)
    
    async def _draw_circle_waveform(self, draw: ImageDraw.Draw, waveform_data: np.ndarray,
                                  config: AudiogramConfig, max_amplitude: float):
        """Draw circular waveform visualization"""
        
        if len(waveform_data) == 0:
            return
        
        center_x = config.width // 2
        center_y = config.height // 2
        base_radius = min(config.width, config.height) // 6
        
        # Current amplitude
        current_amplitude = waveform_data[-1] if len(waveform_data) > 0 else 0
        if max_amplitude > 0:
            normalized_amp = current_amplitude / max_amplitude
        else:
            normalized_amp = 0
        
        # Draw pulsing circle
        radius = base_radius + int(normalized_amp * base_radius * 0.5)
        
        # Outer circle (pulse)
        draw.ellipse([
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        ], outline=config.waveform_color, width=4)
        
        # Inner circle (base)
        inner_radius = base_radius // 2
        draw.ellipse([
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius
        ], fill=config.waveform_color)
    
    async def _draw_progress_bar(self, draw: ImageDraw.Draw, progress: float, 
                               config: AudiogramConfig):
        """Draw progress bar"""
        
        bar_height = 6
        bar_y = config.height - 80
        bar_margin = 50
        bar_width = config.width - 2 * bar_margin
        
        # Background bar
        draw.rectangle([
            bar_margin, bar_y,
            bar_margin + bar_width, bar_y + bar_height
        ], fill="#333333")
        
        # Progress bar
        progress_width = int(bar_width * progress)
        draw.rectangle([
            bar_margin, bar_y,
            bar_margin + progress_width, bar_y + bar_height
        ], fill=config.accent_color)
    
    async def _draw_timestamp(self, draw: ImageDraw.Draw, current_time: float,
                            total_duration: float, config: AudiogramConfig):
        """Draw timestamp"""
        
        def format_time(seconds):
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"
        
        timestamp_text = f"{format_time(current_time)} / {format_time(total_duration)}"
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), timestamp_text, font=font)
        text_width = bbox[2] - bbox[0]
        
        x = (config.width - text_width) // 2
        y = config.height - 40
        
        draw.text((x, y), timestamp_text, font=font, fill=config.text_color)
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont,
                   max_width: int, draw: ImageDraw.Draw) -> List[str]:
        """Wrap text to fit within specified width"""
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    async def _create_video_from_frames(self, frames_dir: str, audio_path: str,
                                      output_path: str, fps: int):
        """Create video from frames and audio"""
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", f"{frames_dir}/frame_%06d.png",
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",  # Match shortest stream
            "-movflags", "+faststart",
            output_path
        ]
        
        await self._run_command(cmd, timeout=300)
    
    async def _cleanup_frames(self, frames_dir: Path):
        """Clean up temporary frame files"""
        try:
            for frame_file in frames_dir.glob("*.png"):
                frame_file.unlink()
            frames_dir.rmdir()
        except Exception as e:
            logger.warning(f"Could not cleanup frames: {e}")
    
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

# Example usage
async def main():
    processor = AudioProcessor()
    
    # Create basic audiogram
    audiogram_path = await processor.create_audiogram(
        "input_audio.mp3", "instagram",
        user_id=12345, content_id="audio123",
        title="Amazing Podcast Episode 🎙️",
        brand_config={"primary_color": "#E1306C", "secondary_color": "#FFFFFF"}
    )
    
    print(f"✅ Audiogram created: {audiogram_path}")
    
    # Create podcast clip
    podcast_clip = await processor.create_podcast_clip(
        "podcast.mp3", start_time=120, duration=30,
        title="Key Insight from Today's Episode",
        speaker_names=["John Doe", "Jane Smith"],
        user_id=12345, content_id="podcast123"
    )
    
    print(f"✅ Podcast clip: {podcast_clip}")
    
    # Extract highlights
    highlights = await processor.extract_audio_highlights(
        "long_audio.mp3", segment_length=30, num_segments=3
    )
    
    print(f"✅ Extracted {len(highlights)} highlight segments")

if __name__ == "__main__":
    asyncio.run(main())