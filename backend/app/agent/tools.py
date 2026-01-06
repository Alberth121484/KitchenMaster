from google import genai
from google.genai import types
import base64
import io
from typing import Optional, Dict, Any
from PIL import Image

from app.config import get_settings

settings = get_settings()

# Initialize Gemini client
client = genai.Client(api_key=settings.google_api_key)


class GeminiImageGenerator:
    """Wrapper for Gemini image generation capabilities."""
    
    def __init__(self):
        self.imagen_model = "imagen-3.0-generate-002"
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = None,
        aspect_ratio: str = "16:9",
        num_images: int = 1
    ) -> Dict[str, Any]:
        """
        Generate kitchen design image using Gemini Imagen 3.
        
        Returns dict with:
        - success: bool
        - images: list of base64 encoded images
        - error: error message if failed
        """
        try:
            # Enhance prompt for kitchen design
            enhanced_prompt = f"""Professional architectural interior photography of: {prompt}

Style: Ultra-realistic, 8K resolution, professional interior design magazine quality
Lighting: Natural daylight with subtle artificial accent lighting
Camera: Wide-angle lens, eye-level perspective
Details: Sharp focus on materials and textures, realistic reflections on surfaces"""

            config = types.GenerateImagesConfig(
                number_of_images=num_images,
                aspect_ratio=aspect_ratio,
                safety_filter_level="block_only_high",
                person_generation="dont_allow",
                output_mime_type="image/png"
            )
            
            if negative_prompt:
                config.negative_prompt = negative_prompt

            response = client.models.generate_images(
                model=self.imagen_model,
                prompt=enhanced_prompt,
                config=config
            )
            
            images = []
            for gen_image in response.generated_images:
                # Convert to base64
                buffered = io.BytesIO()
                gen_image.image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                images.append(img_base64)
            
            return {
                "success": True,
                "images": images,
                "prompt_used": enhanced_prompt
            }
            
        except Exception as e:
            return {
                "success": False,
                "images": [],
                "error": str(e)
            }
    
    async def edit_image(
        self,
        base_image: str,  # base64 encoded
        edit_prompt: str,
        mask_image: str = None  # optional base64 mask
    ) -> Dict[str, Any]:
        """
        Edit existing kitchen design image.
        
        For now, we'll regenerate with modified prompt since Imagen 3
        edit capabilities require specific setup. In production, you'd
        use the actual edit endpoint.
        """
        try:
            # Decode base image
            img_data = base64.b64decode(base_image)
            img = Image.open(io.BytesIO(img_data))
            
            # For actual editing, we'll use Gemini's multimodal capabilities
            # to understand the image and generate a new one based on edits
            analysis_response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    "Describe this kitchen design in detail, including layout, materials, colors, and style. Be specific about dimensions and features visible.",
                    img
                ]
            )
            
            current_description = analysis_response.text
            
            # Generate new image with modifications
            enhanced_edit_prompt = f"""Based on this kitchen design: {current_description}

Apply these modifications: {edit_prompt}

Create an updated version maintaining the same overall layout and dimensions."""

            # Generate new image
            result = await self.generate_image(enhanced_edit_prompt)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "images": [],
                "error": str(e)
            }


class GeminiReasoner:
    """Wrapper for Gemini reasoning/chat capabilities."""
    
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.model_name = settings.gemini_model
        self.chat = None
    
    def start_chat(self, history: list = None):
        """Initialize or reset chat with history."""
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=0.7
        )
        
        self.chat = client.chats.create(
            model=self.model_name,
            config=config
        )
        
        # Replay history if provided
        if history:
            for msg in history:
                if msg["role"] == "user":
                    self.chat.send_message(msg["content"])
    
    async def send_message(self, message: str) -> str:
        """Send message and get response."""
        if not self.chat:
            self.start_chat()
        
        response = self.chat.send_message(message)
        return response.text
    
    async def analyze_request(self, user_message: str, context: dict = None) -> Dict[str, Any]:
        """
        Analyze user request to extract kitchen design parameters.
        
        Returns structured data about:
        - linear_meters
        - shape
        - style
        - materials
        - colors
        - action (generate, edit, question)
        """
        analysis_prompt = f"""Analiza el siguiente mensaje del usuario y extrae los parámetros de diseño de cocina.
Si algún parámetro no se menciona, devuelve null para ese campo.

Mensaje del usuario: "{user_message}"

Contexto previo: {context or 'Ninguno'}

Responde SOLO con un JSON válido con esta estructura:
{{
    "action": "generate" | "edit" | "question" | "clarification",
    "linear_meters": number | null,
    "shape": "I" | "L" | "U" | "G" | "parallel" | null,
    "style": "modern" | "classic" | "rustic" | "minimalist" | "industrial" | "scandinavian" | "contemporary" | null,
    "materials": {{
        "cabinets": string | null,
        "countertop": string | null,
        "backsplash": string | null
    }},
    "colors": [string] | null,
    "budget": "low" | "medium" | "high" | "premium" | null,
    "edit_instructions": string | null,
    "questions_to_ask": [string] | null,
    "special_requirements": string | null
}}"""
        
        response = await self.send_message(analysis_prompt)
        
        # Parse JSON from response
        import json
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Default if parsing fails
        return {
            "action": "question",
            "questions_to_ask": ["¿Podrías proporcionar más detalles sobre tu cocina ideal?"]
        }


# Utility functions for the agent
async def generate_kitchen_image(
    linear_meters: float,
    shape: str = "L",
    style: str = "modern",
    materials: dict = None,
    colors: list = None,
    additional_details: str = ""
) -> Dict[str, Any]:
    """Generate a kitchen design image with specified parameters."""
    
    materials = materials or {
        "cabinets": "white lacquered MDF",
        "countertop": "quartz",
        "backsplash": "subway tiles"
    }
    colors = colors or ["white", "gray", "wood tones"]
    
    shape_descriptions = {
        "I": "single wall linear",
        "L": "L-shaped corner",
        "U": "U-shaped three-wall",
        "G": "G-shaped with peninsula",
        "parallel": "galley parallel walls"
    }
    
    style_atmospheres = {
        "modern": "clean lines, minimalist hardware, integrated appliances",
        "classic": "ornate moldings, traditional hardware, warm wood tones",
        "rustic": "natural wood, farmhouse sink, open shelving, vintage elements",
        "minimalist": "handleless cabinets, hidden appliances, monochromatic palette",
        "industrial": "exposed brick, metal accents, concrete elements, pendant lights",
        "scandinavian": "light wood, white walls, natural light, simple forms",
        "contemporary": "mixed materials, statement lighting, current trends"
    }
    
    prompt = f"""{shape_descriptions.get(shape, 'L-shaped')} kitchen design, {linear_meters} linear meters total

Style: {style} kitchen with {style_atmospheres.get(style, 'modern aesthetics')}
Cabinets: {materials['cabinets']}
Countertops: {materials['countertop']}
Backsplash: {materials['backsplash']}
Color scheme: {', '.join(colors)}
{additional_details}

Features: functional layout, proper work triangle, adequate storage, integrated lighting"""

    generator = GeminiImageGenerator()
    result = await generator.generate_image(prompt)
    
    return result


async def edit_kitchen_image(
    base_image: str,
    edit_instructions: str,
    current_params: dict = None
) -> Dict[str, Any]:
    """Edit an existing kitchen design image."""
    
    generator = GeminiImageGenerator()
    result = await generator.edit_image(base_image, edit_instructions)
    
    return result
