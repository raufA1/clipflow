#!/usr/bin/env python3
"""
Text-to-Visual Generator
Creates engaging visual content from text for social media platforms
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import colorsys
import random
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class TextStyle:
    """Text styling configuration"""
    font_family: str = "arial"
    font_size: int = 48
    font_color: str = "#000000"
    background_color: str = "#FFFFFF"
    accent_color: str = "#1DA1F2"
    alignment: str = "center"  # left, center, right
    line_spacing: float = 1.2
    max_chars_per_line: int = 40
    
@dataclass 
class VisualTemplate:
    """Visual template configuration"""
    name: str
    width: int
    height: int
    background_type: str  # solid, gradient, image
    background_config: Dict[str, Any]
    text_areas: List[Dict[str, Any]]
    decorative_elements: List[Dict[str, Any]]

class TextToVisualGenerator:
    """Generate visual content from text"""
    
    def __init__(self, temp_dir: str = "temp", output_dir: str = "data/content"):
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)
        self.assets_dir = Path("assets/fonts")
        
        for dir_path in [self.temp_dir, self.output_dir, self.assets_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, VisualTemplate]:
        """Load predefined visual templates"""
        
        templates = {
            "quote": VisualTemplate(
                name="quote",
                width=1080, height=1080,
                background_type="gradient",
                background_config={
                    "start_color": "#667eea",
                    "end_color": "#764ba2",
                    "direction": "diagonal"
                },
                text_areas=[
                    {
                        "type": "main_text",
                        "area": (100, 300, 980, 700),
                        "font_size": 52,
                        "color": "#FFFFFF",
                        "alignment": "center",
                        "weight": "bold"
                    },
                    {
                        "type": "author",
                        "area": (100, 750, 980, 800),
                        "font_size": 28,
                        "color": "#E0E0E0",
                        "alignment": "center",
                        "weight": "normal"
                    }
                ],
                decorative_elements=[
                    {
                        "type": "quotation_marks",
                        "position": (100, 250),
                        "size": 80,
                        "color": "#FFFFFF"
                    }
                ]
            ),
            
            "tip": VisualTemplate(
                name="tip",
                width=1080, height=1920,  # Story format
                background_type="solid",
                background_config={"color": "#F8F9FA"},
                text_areas=[
                    {
                        "type": "title",
                        "area": (80, 200, 1000, 300),
                        "font_size": 48,
                        "color": "#1D3557",
                        "alignment": "left",
                        "weight": "bold"
                    },
                    {
                        "type": "content",
                        "area": (80, 350, 1000, 1500),
                        "font_size": 36,
                        "color": "#495057",
                        "alignment": "left",
                        "weight": "normal"
                    }
                ],
                decorative_elements=[
                    {
                        "type": "accent_bar",
                        "area": (80, 150, 200, 180),
                        "color": "#E63946"
                    },
                    {
                        "type": "icon",
                        "position": (80, 80),
                        "icon": "💡",
                        "size": 48
                    }
                ]
            ),
            
            "announcement": VisualTemplate(
                name="announcement",
                width=1200, height=675,  # Twitter format
                background_type="gradient",
                background_config={
                    "start_color": "#FF6B6B",
                    "end_color": "#4ECDC4",
                    "direction": "horizontal"
                },
                text_areas=[
                    {
                        "type": "main_text",
                        "area": (100, 200, 1100, 475),
                        "font_size": 56,
                        "color": "#FFFFFF",
                        "alignment": "center",
                        "weight": "bold"
                    }
                ],
                decorative_elements=[
                    {
                        "type": "border",
                        "width": 8,
                        "color": "#FFFFFF",
                        "opacity": 0.8
                    }
                ]
            ),
            
            "professional": VisualTemplate(
                name="professional", 
                width=1200, height=628,  # LinkedIn format
                background_type="solid",
                background_config={"color": "#FFFFFF"},
                text_areas=[
                    {
                        "type": "title",
                        "area": (80, 120, 1120, 220),
                        "font_size": 42,
                        "color": "#2D3748",
                        "alignment": "left",
                        "weight": "bold"
                    },
                    {
                        "type": "content",
                        "area": (80, 260, 1120, 480),
                        "font_size": 28,
                        "color": "#4A5568", 
                        "alignment": "left",
                        "weight": "normal"
                    },
                    {
                        "type": "cta",
                        "area": (80, 520, 400, 560),
                        "font_size": 24,
                        "color": "#0077B5",
                        "alignment": "left",
                        "weight": "bold"
                    }
                ],
                decorative_elements=[
                    {
                        "type": "accent_line",
                        "area": (80, 80, 200, 88),
                        "color": "#0077B5"
                    }
                ]
            )
        }
        
        return templates
    
    async def create_visual_from_text(self, text: str, template_name: str = "auto",
                                    platform: str = "instagram", 
                                    user_id: int = 0, content_id: str = "",
                                    brand_config: Optional[Dict] = None,
                                    custom_style: Optional[Dict] = None) -> str:
        """Create visual from text content"""
        
        # Auto-select template if needed
        if template_name == "auto":
            template_name = self._auto_select_template(text, platform)
        
        template = self.templates.get(template_name, self.templates["quote"])
        
        # Apply brand customization
        if brand_config:
            template = self._customize_template_with_brand(template, brand_config)
        
        # Apply custom styling
        if custom_style:
            template = self._apply_custom_style(template, custom_style)
        
        # Generate image
        img = await self._generate_image(text, template, platform)
        
        # Save image
        output_name = f"{content_id}_text_visual_{platform}.jpg"
        output_path = self.output_dir / str(user_id) / "visuals" / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        img.save(str(output_path), "JPEG", quality=95, optimize=True)
        
        return str(output_path)
    
    def _auto_select_template(self, text: str, platform: str) -> str:
        """Auto-select appropriate template based on text and platform"""
        
        text_length = len(text)
        word_count = len(text.split())
        
        # Check for quote indicators
        if any(indicator in text.lower() for indicator in ['"', "'", "said", "quote"]):
            return "quote"
        
        # Check for tip/tutorial content
        if any(word in text.lower() for word in ["tip", "how to", "tutorial", "guide", "steps"]):
            return "tip"
        
        # Check for announcements
        if any(word in text.lower() for word in ["announcement", "news", "update", "breaking"]):
            return "announcement"
        
        # Professional content for LinkedIn
        if platform == "linkedin" or any(word in text.lower() for word in ["business", "professional", "career"]):
            return "professional"
        
        # Default based on text length
        if text_length > 200:
            return "tip"  # Long content
        else:
            return "quote"  # Short content
    
    def _customize_template_with_brand(self, template: VisualTemplate, brand_config: Dict) -> VisualTemplate:
        """Customize template with brand colors and fonts"""
        
        # Create a copy to modify
        import copy
        template = copy.deepcopy(template)
        
        # Apply brand colors
        if "primary_color" in brand_config:
            primary = brand_config["primary_color"]
            
            # Update background if gradient
            if template.background_type == "gradient":
                template.background_config["start_color"] = primary
            
            # Update accent elements
            for element in template.decorative_elements:
                if element.get("type") in ["accent_bar", "accent_line"]:
                    element["color"] = primary
        
        if "secondary_color" in brand_config:
            secondary = brand_config["secondary_color"]
            
            # Update gradient end color
            if template.background_type == "gradient":
                template.background_config["end_color"] = secondary
        
        # Apply brand fonts
        if "font_family" in brand_config:
            font_family = brand_config["font_family"]
            # This would be applied during font loading
        
        return template
    
    def _apply_custom_style(self, template: VisualTemplate, style: Dict) -> VisualTemplate:
        """Apply custom styling overrides"""
        
        import copy
        template = copy.deepcopy(template)
        
        # Override background
        if "background_color" in style:
            template.background_type = "solid"
            template.background_config = {"color": style["background_color"]}
        
        # Override text colors
        if "text_color" in style:
            for area in template.text_areas:
                area["color"] = style["text_color"]
        
        return template
    
    async def _generate_image(self, text: str, template: VisualTemplate, platform: str) -> Image.Image:
        """Generate image from text and template"""
        
        # Create base image
        img = Image.new("RGB", (template.width, template.height), "#FFFFFF")
        
        # Apply background
        img = await self._apply_background(img, template.background_type, template.background_config)
        
        # Add decorative elements
        img = await self._add_decorative_elements(img, template.decorative_elements)
        
        # Add text content
        img = await self._add_text_content(img, text, template.text_areas)
        
        return img
    
    async def _apply_background(self, img: Image.Image, bg_type: str, config: Dict) -> Image.Image:
        """Apply background to image"""
        
        if bg_type == "solid":
            # Solid color background
            color = self._parse_color(config.get("color", "#FFFFFF"))
            img.paste(color, (0, 0, img.width, img.height))
        
        elif bg_type == "gradient":
            # Gradient background
            img = self._create_gradient_background(
                img, 
                config.get("start_color", "#667eea"),
                config.get("end_color", "#764ba2"),
                config.get("direction", "vertical")
            )
        
        elif bg_type == "image":
            # Image background
            bg_path = config.get("image_path")
            if bg_path and os.path.exists(bg_path):
                bg_img = Image.open(bg_path)
                bg_img = bg_img.resize((img.width, img.height), Image.Resampling.LANCZOS)
                img.paste(bg_img, (0, 0))
        
        return img
    
    def _create_gradient_background(self, img: Image.Image, start_color: str, 
                                   end_color: str, direction: str) -> Image.Image:
        """Create gradient background"""
        
        start_rgb = self._parse_color(start_color)
        end_rgb = self._parse_color(end_color)
        
        # Create gradient
        gradient = Image.new("RGB", (img.width, img.height))
        
        if direction == "vertical":
            for y in range(img.height):
                ratio = y / img.height
                color = tuple(int(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * ratio) for i in range(3))
                gradient.paste(color, (0, y, img.width, y + 1))
        
        elif direction == "horizontal":
            for x in range(img.width):
                ratio = x / img.width
                color = tuple(int(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * ratio) for i in range(3))
                gradient.paste(color, (x, 0, x + 1, img.height))
        
        elif direction == "diagonal":
            for y in range(img.height):
                for x in range(img.width):
                    ratio = (x + y) / (img.width + img.height)
                    color = tuple(int(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * ratio) for i in range(3))
                    gradient.putpixel((x, y), color)
        
        return gradient
    
    async def _add_decorative_elements(self, img: Image.Image, elements: List[Dict]) -> Image.Image:
        """Add decorative elements to image"""
        
        draw = ImageDraw.Draw(img)
        
        for element in elements:
            element_type = element.get("type")
            
            if element_type == "quotation_marks":
                self._draw_quotation_marks(draw, element)
            
            elif element_type == "accent_bar":
                self._draw_accent_bar(draw, element)
            
            elif element_type == "accent_line":
                self._draw_accent_line(draw, element)
            
            elif element_type == "border":
                self._draw_border(draw, img.size, element)
            
            elif element_type == "icon":
                await self._draw_icon(img, element)
        
        return img
    
    def _draw_quotation_marks(self, draw: ImageDraw.Draw, config: Dict):
        """Draw stylized quotation marks"""
        position = config.get("position", (100, 100))
        size = config.get("size", 60)
        color = self._parse_color(config.get("color", "#FFFFFF"))
        
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()
        
        draw.text(position, """, font=font, fill=color)
    
    def _draw_accent_bar(self, draw: ImageDraw.Draw, config: Dict):
        """Draw accent bar"""
        area = config.get("area", (80, 150, 200, 180))
        color = self._parse_color(config.get("color", "#E63946"))
        
        draw.rectangle(area, fill=color)
    
    def _draw_accent_line(self, draw: ImageDraw.Draw, config: Dict):
        """Draw accent line"""
        area = config.get("area", (80, 80, 200, 88))
        color = self._parse_color(config.get("color", "#0077B5"))
        
        draw.rectangle(area, fill=color)
    
    def _draw_border(self, draw: ImageDraw.Draw, img_size: Tuple[int, int], config: Dict):
        """Draw border around image"""
        width = config.get("width", 5)
        color = self._parse_color(config.get("color", "#FFFFFF"))
        opacity = config.get("opacity", 1.0)
        
        # Apply opacity to color
        if opacity < 1.0:
            color = color + (int(255 * opacity),)
        
        # Draw border
        for i in range(width):
            draw.rectangle([i, i, img_size[0] - 1 - i, img_size[1] - 1 - i], 
                          outline=color, width=1)
    
    async def _draw_icon(self, img: Image.Image, config: Dict):
        """Draw icon/emoji"""
        position = config.get("position", (80, 80))
        icon = config.get("icon", "💡")
        size = config.get("size", 48)
        
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use emoji font
            font = ImageFont.truetype("seguiemj.ttf", size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", size)
            except:
                font = ImageFont.load_default()
        
        draw.text(position, icon, font=font, fill="black")
    
    async def _add_text_content(self, img: Image.Image, text: str, text_areas: List[Dict]) -> Image.Image:
        """Add text content to image"""
        
        draw = ImageDraw.Draw(img)
        
        # Parse text into sections for different areas
        text_sections = self._parse_text_sections(text, len(text_areas))
        
        for i, area_config in enumerate(text_areas):
            if i < len(text_sections):
                section_text = text_sections[i]
                await self._draw_text_in_area(draw, section_text, area_config)
        
        return img
    
    def _parse_text_sections(self, text: str, num_sections: int) -> List[str]:
        """Parse text into sections for different text areas"""
        
        if num_sections == 1:
            return [text]
        
        # Check if text has natural sections (quotes, titles, etc.)
        lines = text.split('\n')
        
        if len(lines) >= num_sections:
            return lines[:num_sections]
        
        # Split by sentences for multiple sections
        sentences = text.split('.')
        if len(sentences) >= num_sections:
            sections = []
            per_section = len(sentences) // num_sections
            for i in range(num_sections):
                start_idx = i * per_section
                end_idx = start_idx + per_section if i < num_sections - 1 else len(sentences)
                sections.append('.'.join(sentences[start_idx:end_idx]).strip())
            return sections
        
        # Default: put main text in first area, leave others empty
        result = [text]
        result.extend([''] * (num_sections - 1))
        return result
    
    async def _draw_text_in_area(self, draw: ImageDraw.Draw, text: str, area_config: Dict):
        """Draw text within specified area"""
        
        if not text.strip():
            return
        
        area = area_config.get("area", (0, 0, 1080, 1080))
        font_size = area_config.get("font_size", 36)
        color = self._parse_color(area_config.get("color", "#000000"))
        alignment = area_config.get("alignment", "center")
        weight = area_config.get("weight", "normal")
        
        # Load font
        font = self._load_font(font_size, weight)
        
        # Calculate available dimensions
        max_width = area[2] - area[0]
        max_height = area[3] - area[1]
        
        # Wrap text to fit area
        wrapped_lines = self._wrap_text_to_fit(text, font, max_width, draw)
        
        # Calculate line height
        line_height = int(font_size * 1.2)
        total_height = len(wrapped_lines) * line_height
        
        # Calculate starting position
        if alignment == "center":
            start_y = area[1] + (max_height - total_height) // 2
        elif alignment == "bottom":
            start_y = area[3] - total_height
        else:  # top
            start_y = area[1]
        
        # Draw each line
        for i, line in enumerate(wrapped_lines):
            y = start_y + i * line_height
            
            # Calculate x position based on alignment
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if alignment == "center":
                x = area[0] + (max_width - text_width) // 2
            elif alignment == "right":
                x = area[2] - text_width
            else:  # left
                x = area[0]
            
            draw.text((x, y), line, font=font, fill=color)
    
    def _wrap_text_to_fit(self, text: str, font: ImageFont.FreeTypeFont, 
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
                    # Single word is too long, break it
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _load_font(self, size: int, weight: str = "normal") -> ImageFont.FreeTypeFont:
        """Load font with specified size and weight"""
        
        font_files = {
            "normal": ["arial.ttf", "DejaVuSans.ttf"],
            "bold": ["arialbd.ttf", "DejaVuSans-Bold.ttf"],
            "light": ["ariall.ttf", "DejaVuSans-Light.ttf"]
        }
        
        fonts_to_try = font_files.get(weight, font_files["normal"])
        
        for font_file in fonts_to_try:
            try:
                return ImageFont.truetype(font_file, size)
            except:
                continue
        
        # Fallback to default font
        return ImageFont.load_default()
    
    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        """Parse color string to RGB tuple"""
        
        if color_str.startswith("#"):
            # Hex color
            hex_color = color_str[1:]
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Named colors
        color_map = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "gray": (128, 128, 128),
            "grey": (128, 128, 128)
        }
        
        return color_map.get(color_str.lower(), (0, 0, 0))

class QuoteVisualGenerator:
    """Specialized generator for quote visuals"""
    
    def __init__(self, text_generator: TextToVisualGenerator):
        self.generator = text_generator
    
    async def create_quote_visual(self, quote: str, author: str = "",
                                platform: str = "instagram",
                                user_id: int = 0, content_id: str = "",
                                style: str = "elegant") -> str:
        """Create quote visual with author attribution"""
        
        full_text = f"{quote}\n\n— {author}" if author else quote
        
        # Select style-specific template customization
        style_configs = {
            "elegant": {
                "background_color": "#2C3E50",
                "text_color": "#ECF0F1",
                "accent_color": "#E74C3C"
            },
            "modern": {
                "background_color": "#FFFFFF", 
                "text_color": "#2D3748",
                "accent_color": "#4299E1"
            },
            "vibrant": {
                "background_color": "#FF6B6B",
                "text_color": "#FFFFFF",
                "accent_color": "#4ECDC4"
            }
        }
        
        custom_style = style_configs.get(style, style_configs["elegant"])
        
        return await self.generator.create_visual_from_text(
            full_text, "quote", platform, user_id, content_id,
            custom_style=custom_style
        )

# Example usage
async def main():
    generator = TextToVisualGenerator()
    
    # Create quote visual
    quote_path = await generator.create_visual_from_text(
        "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "quote", "instagram", 12345, "quote123",
        brand_config={"primary_color": "#1DA1F2", "secondary_color": "#14171A"}
    )
    print(f"✅ Quote visual: {quote_path}")
    
    # Create tip visual
    tip_text = "💡 Pro Tip: Use the 80/20 rule for content creation. Spend 80% of your time on high-impact activities and 20% on experimentation."
    tip_path = await generator.create_visual_from_text(
        tip_text, "tip", "instagram_story", 12345, "tip123"
    )
    print(f"✅ Tip visual: {tip_path}")
    
    # Create professional post
    professional_text = "The future of work is remote-first. Companies that adapt now will have a competitive advantage in attracting top talent."
    prof_path = await generator.create_visual_from_text(
        professional_text, "professional", "linkedin", 12345, "prof123"
    )
    print(f"✅ Professional visual: {prof_path}")

if __name__ == "__main__":
    asyncio.run(main())