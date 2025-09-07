#!/usr/bin/env python3
"""
Advanced Image Processing with Pillow
Handles resizing, cropping, effects, brand overlays for all platforms
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from PIL.ExifTags import ORIENTATION
import io
import logging
import colorsys
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ImageSpecs:
    """Platform-specific image specifications"""
    width: int
    height: int
    quality: int = 95
    format: str = "JPEG"
    max_file_size: int = 15 * 1024 * 1024  # 15MB default

@dataclass
class ImageInfo:
    """Image metadata information"""
    width: int
    height: int
    format: str
    mode: str
    file_size: int
    has_transparency: bool
    orientation: int = 1
    
    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height if self.height > 0 else 1
    
    @property
    def is_vertical(self) -> bool:
        return self.height > self.width
    
    @property
    def is_square(self) -> bool:
        return abs(self.width - self.height) / max(self.width, self.height) < 0.1
    
    @property
    def is_horizontal(self) -> bool:
        return self.width > self.height

class ImageProcessor:
    """Advanced image processor with platform optimization"""
    
    def __init__(self, temp_dir: str = "temp", output_dir: str = "data/content"):
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)
        
        for dir_path in [self.temp_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_image_info(self, image_path: str) -> ImageInfo:
        """Extract image metadata"""
        try:
            with Image.open(image_path) as img:
                # Handle EXIF orientation
                orientation = 1
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    orientation = exif.get(ORIENTATION, 1)
                
                return ImageInfo(
                    width=img.width,
                    height=img.height,
                    format=img.format or "UNKNOWN",
                    mode=img.mode,
                    file_size=os.path.getsize(image_path),
                    has_transparency=img.mode in ("RGBA", "LA", "P") and "transparency" in img.info,
                    orientation=orientation
                )
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            raise
    
    async def process_for_platform(self, input_path: str, platform: str,
                                  user_id: int, content_id: str,
                                  brand_config: Optional[Dict] = None,
                                  style: str = "default") -> str:
        """Process image for specific platform"""
        
        specs = self._get_platform_specs(platform)
        
        # Generate output path
        output_name = f"{content_id}_{platform}.jpg"
        output_path = self.output_dir / str(user_id) / "images" / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Processing image for {platform}: {specs.width}x{specs.height}")
        
        # Process image
        processed_img = await self._process_image(input_path, specs, brand_config, style)
        
        # Save with optimization
        await self._save_optimized(processed_img, str(output_path), specs)
        
        return str(output_path)
    
    async def _process_image(self, input_path: str, specs: ImageSpecs,
                           brand_config: Optional[Dict] = None, 
                           style: str = "default") -> Image.Image:
        """Process image with all transformations"""
        
        # Open and fix orientation
        img = Image.open(input_path)
        img = self._fix_orientation(img)
        
        # Convert to RGB if needed
        if img.mode in ("RGBA", "LA", "P"):
            # Handle transparency
            if img.mode == "P" and "transparency" in img.info:
                img = img.convert("RGBA")
            
            if img.mode == "RGBA":
                # Create white background for JPEG
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])  # Use alpha as mask
                img = background
            else:
                img = img.convert("RGB")
        
        # Smart crop and resize
        img = await self._smart_crop_and_resize(img, specs.width, specs.height)
        
        # Apply style effects
        if style != "default":
            img = await self._apply_style_effects(img, style)
        
        # Add brand overlay
        if brand_config:
            img = await self._add_brand_overlay(img, brand_config)
        
        return img
    
    def _fix_orientation(self, img: Image.Image) -> Image.Image:
        """Fix image orientation based on EXIF data"""
        try:
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                orientation = exif.get(ORIENTATION, 1)
                
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except Exception:
            pass  # Ignore EXIF errors
        
        return img
    
    async def _smart_crop_and_resize(self, img: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """Smart crop and resize maintaining important content"""
        
        current_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if abs(current_ratio - target_ratio) < 0.01:
            # Same aspect ratio, just resize
            return img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Different aspect ratios - smart crop needed
        if current_ratio > target_ratio:
            # Image is wider - crop width
            new_width = int(img.height * target_ratio)
            # Center crop (could be enhanced with face detection)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Image is taller - crop height
            new_height = int(img.width / target_ratio)
            # Center crop (could be enhanced with important content detection)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
        
        # Resize to target dimensions
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    async def _apply_style_effects(self, img: Image.Image, style: str) -> Image.Image:
        """Apply style effects to image"""
        
        effects = {
            "vintage": self._apply_vintage_effect,
            "modern": self._apply_modern_effect,
            "dramatic": self._apply_dramatic_effect,
            "soft": self._apply_soft_effect,
            "vibrant": self._apply_vibrant_effect,
            "minimal": self._apply_minimal_effect
        }
        
        effect_func = effects.get(style, lambda x: x)
        return effect_func(img)
    
    def _apply_vintage_effect(self, img: Image.Image) -> Image.Image:
        """Apply vintage/retro effect"""
        # Reduce saturation
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.7)
        
        # Add warm tone
        img_array = np.array(img)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.1, 0, 255)  # More red
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.9, 0, 255)  # Less blue
        
        return Image.fromarray(img_array.astype(np.uint8))
    
    def _apply_modern_effect(self, img: Image.Image) -> Image.Image:
        """Apply modern/clean effect"""
        # Increase contrast slightly
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        # Slight sharpening
        return img.filter(ImageFilter.UnsharpMask(radius=1, percent=110, threshold=3))
    
    def _apply_dramatic_effect(self, img: Image.Image) -> Image.Image:
        """Apply dramatic effect"""
        # High contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)
        
        # Reduce brightness slightly
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.9)
        
        return img
    
    def _apply_soft_effect(self, img: Image.Image) -> Image.Image:
        """Apply soft effect"""
        # Slight blur
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Reduce contrast
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(0.9)
    
    def _apply_vibrant_effect(self, img: Image.Image) -> Image.Image:
        """Apply vibrant effect"""
        # Increase saturation
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)
        
        # Slight contrast boost
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(1.1)
    
    def _apply_minimal_effect(self, img: Image.Image) -> Image.Image:
        """Apply minimal effect"""
        # Reduce saturation
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(0.8)
    
    async def _add_brand_overlay(self, img: Image.Image, brand_config: Dict) -> Image.Image:
        """Add brand overlay (logo, watermark, etc.)"""
        
        # Create a copy to work with
        img = img.copy()
        
        # Add logo if specified
        if brand_config.get("logo_path") and os.path.exists(brand_config["logo_path"]):
            img = await self._add_logo_overlay(img, brand_config)
        
        # Add text watermark if specified
        if brand_config.get("watermark_text"):
            img = await self._add_text_watermark(img, brand_config)
        
        # Add color accent if specified
        if brand_config.get("accent_color"):
            img = await self._add_color_accent(img, brand_config)
        
        return img
    
    async def _add_logo_overlay(self, img: Image.Image, brand_config: Dict) -> Image.Image:
        """Add logo overlay to image"""
        
        logo_path = brand_config["logo_path"]
        position = brand_config.get("logo_position", "bottom-right")
        opacity = brand_config.get("logo_opacity", 0.8)
        size_percent = brand_config.get("logo_size_percent", 12)
        
        try:
            # Open and prepare logo
            with Image.open(logo_path) as logo:
                # Calculate logo size
                logo_width = int(img.width * size_percent / 100)
                logo_height = int(logo.height * logo_width / logo.width)
                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                
                # Convert to RGBA for transparency
                if logo.mode != "RGBA":
                    logo = logo.convert("RGBA")
                
                # Apply opacity
                if opacity < 1.0:
                    alpha = logo.split()[-1]
                    alpha = alpha.point(lambda x: int(x * opacity))
                    logo.putalpha(alpha)
                
                # Calculate position
                margin = 20
                positions = {
                    "top-left": (margin, margin),
                    "top-right": (img.width - logo_width - margin, margin),
                    "bottom-left": (margin, img.height - logo_height - margin),
                    "bottom-right": (img.width - logo_width - margin, img.height - logo_height - margin),
                    "center": ((img.width - logo_width) // 2, (img.height - logo_height) // 2)
                }
                
                x, y = positions.get(position, positions["bottom-right"])
                
                # Paste logo onto image
                img.paste(logo, (x, y), logo)
                
        except Exception as e:
            logger.warning(f"Could not add logo overlay: {e}")
        
        return img
    
    async def _add_text_watermark(self, img: Image.Image, brand_config: Dict) -> Image.Image:
        """Add text watermark to image"""
        
        text = brand_config["watermark_text"]
        position = brand_config.get("watermark_position", "bottom-right")
        color = brand_config.get("watermark_color", "white")
        opacity = brand_config.get("watermark_opacity", 0.7)
        
        try:
            # Create drawing context
            draw = ImageDraw.Draw(img)
            
            # Try to load font
            font_size = max(img.width // 50, 12)  # Responsive font size
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position
            margin = 20
            positions = {
                "top-left": (margin, margin),
                "top-right": (img.width - text_width - margin, margin),
                "bottom-left": (margin, img.height - text_height - margin),
                "bottom-right": (img.width - text_width - margin, img.height - text_height - margin),
                "center": ((img.width - text_width) // 2, (img.height - text_height) // 2)
            }
            
            x, y = positions.get(position, positions["bottom-right"])
            
            # Parse color
            if isinstance(color, str):
                if color.startswith("#"):
                    color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                elif color == "white":
                    color = (255, 255, 255)
                elif color == "black":
                    color = (0, 0, 0)
            
            # Apply opacity
            if opacity < 1.0:
                color = color + (int(255 * opacity),)
                # Create temporary image for text
                txt_img = Image.new("RGBA", img.size, (255, 255, 255, 0))
                txt_draw = ImageDraw.Draw(txt_img)
                txt_draw.text((x, y), text, font=font, fill=color)
                
                # Composite with original
                img = Image.alpha_composite(img.convert("RGBA"), txt_img).convert("RGB")
            else:
                draw.text((x, y), text, font=font, fill=color)
                
        except Exception as e:
            logger.warning(f"Could not add text watermark: {e}")
        
        return img
    
    async def _add_color_accent(self, img: Image.Image, brand_config: Dict) -> Image.Image:
        """Add subtle color accent based on brand colors"""
        
        accent_color = brand_config["accent_color"]
        intensity = brand_config.get("accent_intensity", 0.1)
        
        try:
            # Parse color
            if isinstance(accent_color, str) and accent_color.startswith("#"):
                r = int(accent_color[1:3], 16)
                g = int(accent_color[3:5], 16)
                b = int(accent_color[5:7], 16)
            else:
                return img
            
            # Create color overlay
            overlay = Image.new("RGB", img.size, (r, g, b))
            
            # Blend with original
            img = Image.blend(img, overlay, intensity)
            
        except Exception as e:
            logger.warning(f"Could not add color accent: {e}")
        
        return img
    
    async def _save_optimized(self, img: Image.Image, output_path: str, specs: ImageSpecs):
        """Save image with optimization for file size and quality"""
        
        quality = specs.quality
        max_size = specs.max_file_size
        
        # Try saving with initial quality
        while quality >= 60:  # Don't go below 60% quality
            buffer = io.BytesIO()
            img.save(buffer, format=specs.format, quality=quality, optimize=True)
            
            if buffer.tell() <= max_size:
                # File size is acceptable
                with open(output_path, "wb") as f:
                    f.write(buffer.getvalue())
                return
            
            # Reduce quality and try again
            quality -= 10
        
        # If still too large, resize image
        scale_factor = 0.9
        while scale_factor > 0.5:
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            resized_img.save(buffer, format=specs.format, quality=75, optimize=True)
            
            if buffer.tell() <= max_size:
                with open(output_path, "wb") as f:
                    f.write(buffer.getvalue())
                return
            
            scale_factor -= 0.1
        
        # Final fallback - save as is
        img.save(output_path, format=specs.format, quality=60, optimize=True)
    
    def _get_platform_specs(self, platform: str) -> ImageSpecs:
        """Get platform-specific image specifications"""
        
        specs = {
            "instagram_post": ImageSpecs(width=1080, height=1080, quality=95),  # Square
            "instagram_story": ImageSpecs(width=1080, height=1920, quality=90), # 9:16
            "twitter_post": ImageSpecs(width=1200, height=675, quality=85),     # 16:9
            "twitter_header": ImageSpecs(width=1500, height=500, quality=90),
            "linkedin_post": ImageSpecs(width=1200, height=628, quality=90),    # 1.91:1
            "linkedin_banner": ImageSpecs(width=1584, height=396, quality=95),
            "facebook_post": ImageSpecs(width=1200, height=630, quality=85),
            "youtube_thumbnail": ImageSpecs(width=1280, height=720, quality=95),
            "tiktok": ImageSpecs(width=1080, height=1920, quality=90)
        }
        
        return specs.get(platform.lower(), specs["instagram_post"])

class CarouselGenerator:
    """Generate multi-image carousels for platforms like Instagram"""
    
    def __init__(self, image_processor: ImageProcessor):
        self.processor = image_processor
    
    async def create_carousel(self, images: List[str], platform: str,
                            user_id: int, content_id: str,
                            brand_config: Optional[Dict] = None,
                            style: str = "default") -> List[str]:
        """Create carousel from multiple images"""
        
        output_paths = []
        
        for i, img_path in enumerate(images[:10]):  # Max 10 images for IG
            output_path = await self.processor.process_for_platform(
                img_path, f"{platform}_carousel_{i+1}",
                user_id, f"{content_id}_{i+1}",
                brand_config, style
            )
            output_paths.append(output_path)
        
        return output_paths
    
    async def create_before_after(self, before_img: str, after_img: str,
                                platform: str, user_id: int, content_id: str,
                                brand_config: Optional[Dict] = None) -> str:
        """Create before/after comparison image"""
        
        # Load both images
        img1 = Image.open(before_img)
        img2 = Image.open(after_img)
        
        specs = self.processor._get_platform_specs(platform)
        
        # Resize both to half width
        half_width = specs.width // 2
        img1 = img1.resize((half_width, specs.height), Image.Resampling.LANCZOS)
        img2 = img2.resize((half_width, specs.height), Image.Resampling.LANCZOS)
        
        # Create combined image
        combined = Image.new("RGB", (specs.width, specs.height))
        combined.paste(img1, (0, 0))
        combined.paste(img2, (half_width, 0))
        
        # Add "BEFORE" and "AFTER" labels
        draw = ImageDraw.Draw(combined)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 20), "BEFORE", font=font, fill="white")
        draw.text((half_width + 20, 20), "AFTER", font=font, fill="white")
        
        # Save
        output_name = f"{content_id}_before_after_{platform}.jpg"
        output_path = self.processor.output_dir / str(user_id) / "images" / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        await self.processor._save_optimized(combined, str(output_path), specs)
        
        return str(output_path)

# Example usage
async def main():
    processor = ImageProcessor()
    
    # Process single image
    output_path = await processor.process_for_platform(
        "input.jpg", "instagram_post",
        user_id=12345, content_id="test123",
        brand_config={
            "logo_path": "logo.png",
            "logo_position": "bottom-right",
            "logo_opacity": 0.7,
            "watermark_text": "@username",
            "accent_color": "#1DA1F2"
        },
        style="modern"
    )
    
    print(f"✅ Instagram post: {output_path}")
    
    # Create carousel
    carousel_gen = CarouselGenerator(processor)
    carousel_paths = await carousel_gen.create_carousel(
        ["img1.jpg", "img2.jpg", "img3.jpg"],
        "instagram_post", 12345, "carousel123"
    )
    
    print(f"✅ Carousel: {len(carousel_paths)} images created")

if __name__ == "__main__":
    asyncio.run(main())