#!/usr/bin/env python3
"""
ClipFlow Brand Management System
Handles brand consistency, logo integration, and visual identity
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import logging

logger = logging.getLogger(__name__)

@dataclass
class BrandColors:
    """Brand color palette"""
    primary: str
    secondary: str
    accent: str
    background: str
    dark_background: str
    text: str
    text_secondary: str
    success: str
    warning: str
    error: str

@dataclass
class BrandConfig:
    """Complete brand configuration"""
    name: str
    tagline: str
    colors: BrandColors
    logo_path: Optional[str] = None
    dark_logo_path: Optional[str] = None
    icon_path: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrandConfig':
        """Create BrandConfig from dictionary"""
        colors = BrandColors(**data.get('colors', {}))
        
        logo_config = data.get('logo', {})
        return cls(
            name=data.get('brand_name', 'ClipFlow'),
            tagline=data.get('tagline', 'Universal Content Automation Platform'),
            colors=colors,
            logo_path=logo_config.get('path'),
            dark_logo_path=logo_config.get('dark_mode_path'),
            icon_path=logo_config.get('icon_path')
        )

class BrandManager:
    """Manages brand assets and visual identity"""
    
    def __init__(self, config_path: str = "config/brand_config.json"):
        self.config_path = Path(config_path)
        self.assets_dir = Path("assets")
        self.templates_dir = Path("templates")
        
        # Create directories
        self.assets_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Load brand configuration
        self.brand_config = self._load_brand_config()
        
        # Cache for loaded images
        self._image_cache = {}
    
    def _load_brand_config(self) -> BrandConfig:
        """Load brand configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                return BrandConfig.from_dict(data)
            else:
                logger.warning(f"Brand config not found at {self.config_path}, using defaults")
                return self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading brand config: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> BrandConfig:
        """Create default brand configuration"""
        colors = BrandColors(
            primary="#6366F1",
            secondary="#8B5CF6",
            accent="#F59E0B",
            background="#F8FAFC",
            dark_background="#0F172A",
            text="#1E293B",
            text_secondary="#64748B",
            success="#10B981",
            warning="#F59E0B",
            error="#EF4444"
        )
        
        return BrandConfig(
            name="ClipFlow",
            tagline="Universal Content Automation Platform",
            colors=colors
        )
    
    def get_logo(self, dark_mode: bool = False, size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
        """Get brand logo image"""
        logo_path = self.brand_config.dark_logo_path if dark_mode else self.brand_config.logo_path
        
        if not logo_path or not Path(logo_path).exists():
            # Create default logo if none exists
            return self._create_default_logo(size or (200, 60))
        
        cache_key = f"{logo_path}_{size}"
        if cache_key in self._image_cache:
            return self._image_cache[cache_key].copy()
        
        try:
            logo = Image.open(logo_path)
            if size:
                logo = logo.resize(size, Image.Resampling.LANCZOS)
            
            self._image_cache[cache_key] = logo.copy()
            return logo
        except Exception as e:
            logger.error(f"Error loading logo: {e}")
            return self._create_default_logo(size or (200, 60))
    
    def _create_default_logo(self, size: Tuple[int, int]) -> Image.Image:
        """Create default ClipFlow logo"""
        width, height = size
        
        # Create image with gradient background
        logo = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(logo)
        
        # Draw gradient background
        for i in range(height):
            r = int(99 + (139 - 99) * i / height)  # #6366F1 to #8B5CF6
            g = int(102 + (92 - 102) * i / height)
            b = int(241 + (246 - 241) * i / height)
            draw.line([(0, i), (width, i)], fill=(r, g, b, 200))
        
        # Draw rounded rectangle
        corner_radius = min(width, height) // 8
        self._draw_rounded_rectangle(draw, 0, 0, width, height, corner_radius, 
                                   fill=(99, 102, 241, 230))
        
        # Add ClipFlow text
        try:
            # Try to use a good font
            font_size = max(12, height // 4)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            text = self.brand_config.name
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center text
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw text with shadow
            draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 128))
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
            
        except Exception as e:
            logger.warning(f"Could not add text to logo: {e}")
        
        return logo
    
    def _draw_rounded_rectangle(self, draw: ImageDraw.Draw, x1: int, y1: int, 
                              x2: int, y2: int, radius: int, **kwargs):
        """Draw rounded rectangle"""
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], **kwargs)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], **kwargs)
        
        # Corners
        draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, **kwargs)
        draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, **kwargs)
        draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, **kwargs)
        draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, **kwargs)
    
    def apply_watermark(self, image: Image.Image, position: str = "bottom_right", 
                       opacity: float = 0.7, margin: int = 20) -> Image.Image:
        """Apply brand watermark to image"""
        try:
            # Get logo
            logo_size = (min(image.width, image.height) // 6, min(image.width, image.height) // 10)
            logo = self.get_logo(size=logo_size)
            
            if not logo:
                return image
            
            # Apply opacity
            if opacity < 1.0:
                logo = logo.convert("RGBA")
                alpha = logo.split()[-1]
                alpha = alpha.point(lambda p: int(p * opacity))
                logo.putalpha(alpha)
            
            # Calculate position
            x, y = self._calculate_watermark_position(
                image.size, logo.size, position, margin
            )
            
            # Apply watermark
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            watermarked = Image.new('RGBA', image.size, (0, 0, 0, 0))
            watermarked.paste(image, (0, 0))
            watermarked.paste(logo, (x, y), logo)
            
            return watermarked.convert('RGB')
            
        except Exception as e:
            logger.error(f"Error applying watermark: {e}")
            return image
    
    def _calculate_watermark_position(self, image_size: Tuple[int, int], 
                                    logo_size: Tuple[int, int], 
                                    position: str, margin: int) -> Tuple[int, int]:
        """Calculate watermark position"""
        img_w, img_h = image_size
        logo_w, logo_h = logo_size
        
        positions = {
            "top_left": (margin, margin),
            "top_right": (img_w - logo_w - margin, margin),
            "bottom_left": (margin, img_h - logo_h - margin),
            "bottom_right": (img_w - logo_w - margin, img_h - logo_h - margin),
            "center": ((img_w - logo_w) // 2, (img_h - logo_h) // 2)
        }
        
        return positions.get(position, positions["bottom_right"])
    
    def create_text_card(self, text: str, width: int = 800, height: int = 600,
                        background_color: Optional[str] = None) -> Image.Image:
        """Create branded text card for social media"""
        
        # Use brand colors
        bg_color = background_color or self.brand_config.colors.background
        if bg_color.startswith('#'):
            bg_color = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Create image
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # Add gradient overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Gradient from primary to secondary color
        primary = self.brand_config.colors.primary
        secondary = self.brand_config.colors.secondary
        
        # Simple vertical gradient
        for i in range(height):
            alpha = int(50 * i / height)  # Fade from 0 to 50
            overlay_draw.line([(0, i), (width, i)], fill=(99, 102, 241, alpha))
        
        image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(image)
        
        # Add text
        try:
            font_size = min(width, height) // 15
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Word wrap text
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] - bbox[0] <= width - 100:  # 50px margin on each side
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(current_line)
            
            # Draw text lines
            total_height = len(lines) * (font_size + 10)
            start_y = (height - total_height) // 2
            
            text_color = self.brand_config.colors.text
            if text_color.startswith('#'):
                text_color = tuple(int(text_color[i:i+2], 16) for i in (1, 3, 5))
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x = (width - line_width) // 2
                y = start_y + i * (font_size + 10)
                
                # Text shadow
                draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 128))
                # Main text
                draw.text((x, y), line, font=font, fill=text_color)
        
        except Exception as e:
            logger.error(f"Error adding text to card: {e}")
        
        # Add logo watermark
        return self.apply_watermark(image, position="bottom_right", opacity=0.6)
    
    def get_platform_colors(self, platform: str) -> Dict[str, str]:
        """Get platform-specific colors"""
        platform_themes = {
            "youtube": {"primary": "#FF0000", "background": "#000000", "text": "#FFFFFF"},
            "instagram": {"primary": "#E4405F", "background": "#FFFFFF", "text": "#262626"},
            "tiktok": {"primary": "#000000", "secondary": "#FF0050", "background": "#FFFFFF", "text": "#161823"},
            "twitter": {"primary": "#1DA1F2", "background": "#FFFFFF", "text": "#14171A"},
            "linkedin": {"primary": "#0077B5", "background": "#FFFFFF", "text": "#000000"}
        }
        
        return platform_themes.get(platform.lower(), {
            "primary": self.brand_config.colors.primary,
            "background": self.brand_config.colors.background,
            "text": self.brand_config.colors.text
        })
    
    def save_brand_asset(self, image: Image.Image, filename: str) -> str:
        """Save brand asset to assets directory"""
        asset_path = self.assets_dir / filename
        
        try:
            # Ensure proper format
            if filename.lower().endswith('.png'):
                image.save(asset_path, 'PNG', optimize=True)
            elif filename.lower().endswith(('.jpg', '.jpeg')):
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                image.save(asset_path, 'JPEG', quality=95, optimize=True)
            else:
                # Default to PNG
                asset_path = asset_path.with_suffix('.png')
                image.save(asset_path, 'PNG', optimize=True)
            
            logger.info(f"Saved brand asset: {asset_path}")
            return str(asset_path)
            
        except Exception as e:
            logger.error(f"Error saving brand asset: {e}")
            return ""

# Example usage
async def main():
    """Example usage of brand manager"""
    brand_manager = BrandManager()
    
    # Create default logo
    logo = brand_manager.get_logo(size=(300, 100))
    if logo:
        brand_manager.save_brand_asset(logo, "clipflow_logo.png")
    
    # Create dark mode logo
    dark_logo = brand_manager.get_logo(dark_mode=True, size=(300, 100))
    if dark_logo:
        brand_manager.save_brand_asset(dark_logo, "clipflow_logo_dark.png")
    
    # Create text card
    text_card = brand_manager.create_text_card(
        "🚀 Transform your content workflow with AI-powered multi-platform publishing!",
        width=1080,
        height=1080
    )
    brand_manager.save_brand_asset(text_card, "sample_text_card.jpg")
    
    print("✅ Brand assets created successfully!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())