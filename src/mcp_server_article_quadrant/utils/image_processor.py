"""Image processing utilities for OCR and content extraction."""

import base64
import io
import logging
import os
import tempfile
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

from mcp_server_article_quadrant.utils.error_handling import OCRError, ValidationError, handle_error
from mcp_server_article_quadrant.utils.http_client import HTTPClient


class ImageProcessor:
    """Base image processing utilities."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif'}

    def validate_image(self, image_path: str) -> bool:
        """Validate if file is a supported image format."""
        try:
            path = Path(image_path)
            return path.suffix.lower() in self.supported_formats and path.exists()
        except Exception:
            return False

    def load_image(self, image_source: Union[str, bytes, Image.Image]) -> Image.Image:
        """Load image from various sources."""
        try:
            if isinstance(image_source, Image.Image):
                return image_source
            elif isinstance(image_source, bytes):
                return Image.open(io.BytesIO(image_source))
            elif isinstance(image_source, str):
                if os.path.exists(image_source):
                    return Image.open(image_source)
                else:
                    # Try to decode as base64
                    try:
                        if image_source.startswith('data:image'):
                            # Remove data URL prefix
                            image_data = image_source.split(',')[1]
                        else:
                            image_data = image_source
                        decoded = base64.b64decode(image_data)
                        return Image.open(io.BytesIO(decoded))
                    except Exception:
                        raise ValidationError(f"Invalid image source: {image_source}")
            else:
                raise ValidationError(f"Unsupported image source type: {type(image_source)}")

        except Exception as e:
            if not isinstance(e, ValidationError):
                raise OCRError(f"Failed to load image: {e}", image_info=str(image_source))
            raise

    def preprocess_image(
        self,
        image: Image.Image,
        enhance_contrast: bool = True,
        enhance_sharpness: bool = True,
        denoise: bool = True,
        resize_max_dim: Optional[int] = None,
        target_dpi: Optional[int] = None
    ) -> Image.Image:
        """Preprocess image for better OCR results."""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if too large (for processing efficiency)
            if resize_max_dim:
                max_dim = max(image.size)
                if max_dim > resize_max_dim:
                    ratio = resize_max_dim / max_dim
                    new_size = tuple(int(dim * ratio) for dim in image.size)
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Enhance contrast
            if enhance_contrast:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)

            # Enhance sharpness
            if enhance_sharpness:
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.2)

            # Denoise
            if denoise:
                image = image.filter(ImageFilter.MedianFilter(size=3))

            # Adjust DPI if specified
            if target_dpi:
                # PIL doesn't directly support DPI adjustment for OCR,
                # but we can simulate by resizing
                current_dpi = image.info.get('dpi', (72, 72))[0]
                if current_dpi != target_dpi:
                    ratio = target_dpi / current_dpi
                    new_size = tuple(int(dim * ratio) for dim in image.size)
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            raise OCRError(f"Image preprocessing failed: {e}")

    def image_to_bytes(self, image: Image.Image, format: str = "PNG") -> bytes:
        """Convert PIL Image to bytes."""
        try:
            buffer = io.BytesIO()
            image.save(buffer, format=format)
            return buffer.getvalue()
        except Exception as e:
            raise OCRError(f"Failed to convert image to bytes: {e}")

    def save_temp_image(self, image: Image.Image, suffix: str = ".png") -> str:
        """Save image to temporary file and return path."""
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                image.save(tmp_file.name)
                return tmp_file.name
        except Exception as e:
            raise OCRError(f"Failed to save temporary image: {e}")

    def get_image_info(self, image: Union[str, bytes, Image.Image]) -> Dict[str, Any]:
        """Get information about an image."""
        try:
            pil_image = self.load_image(image)
            return {
                "size": pil_image.size,
                "mode": pil_image.mode,
                "format": pil_image.format,
                "has_transparency": pil_image.mode in ('RGBA', 'LA') or 'transparency' in pil_image.info
            }
        except Exception as e:
            return {"error": str(e)}


class MistralOCRClient:
    """Mistral Document AI OCR client."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.mistral.ai"):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.base_url = base_url.rstrip('/')
        self.logger = logging.getLogger(__name__)

        if not self.api_key:
            self.logger.warning("Mistral API key not provided, OCR will be disabled")

        self.enabled = bool(self.api_key)
        self.timeout = int(os.getenv("MISTRAL_TIMEOUT", "60"))
        self.max_retries = int(os.getenv("MISTRAL_MAX_RETRIES", "3"))

    async def extract_text(
        self,
        image: Union[str, bytes, Image.Image],
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract text from image using Mistral Document AI."""
        if not self.enabled:
            return {
                "success": False,
                "error": "Mistral OCR not available - no API key provided",
                "text": None
            }

        try:
            # Prepare image
            if isinstance(image, str) and os.path.exists(image):
                with open(image, 'rb') as f:
                    image_bytes = f.read()
            elif isinstance(image, Image.Image):
                image_bytes = self.image_to_bytes(image)
            elif isinstance(image, bytes):
                image_bytes = image
            else:
                raise ValidationError("Invalid image format for Mistral OCR")

            # Encode image as base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": os.getenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest"),
                "image": f"data:image/png;base64,{image_b64}"
            }

            if language:
                data["language"] = language

            # Make request
            async with HTTPClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/ocr",
                    json=data,
                    headers=headers
                )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result.get("text", ""),
                    "confidence": result.get("confidence", 0.0),
                    "processing_time": result.get("processing_time"),
                    "language_detected": result.get("language"),
                    "method": "mistral_ocr"
                }
            else:
                error_detail = response.text
                self.logger.error(f"Mistral OCR error: {response.status_code} - {error_detail}")
                return {
                    "success": False,
                    "error": f"Mistral OCR API error: {response.status_code}",
                    "details": error_detail,
                    "text": None
                }

        except Exception as e:
            self.logger.error(f"Mistral OCR failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": None
            }


class FallbackOCRClient:
    """Fallback OCR client using local engines."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tesseract_available = self._check_tesseract()
        self.easyocr_available = self._check_easyocr()
        self.easyocr_reader = None

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available."""
        try:
            import pytesseract
            # Try to get version to verify it's working
            pytesseract.get_tesseract_version()
            return True
        except ImportError:
            self.logger.warning("pytesseract not installed")
            return False
        except Exception as e:
            self.logger.warning(f"Tesseract not available: {e}")
            return False

    def _check_easyocr(self) -> bool:
        """Check if EasyOCR is available."""
        try:
            import easyocr
            return True
        except ImportError:
            self.logger.warning("easyocr not installed")
            return False
        except Exception as e:
            self.logger.warning(f"EasyOCR not available: {e}")
            return False

    def _init_easyocr(self):
        """Initialize EasyOCR reader."""
        if self.easyocr_available and self.easyocr_reader is None:
            try:
                import easyocr
                # Initialize with English and Chinese
                self.easyocr_reader = easyocr.Reader(['en', 'ch_sim'])
            except Exception as e:
                self.logger.error(f"Failed to initialize EasyOCR: {e}")
                self.easyocr_available = False

    async def extract_text_tesseract(
        self,
        image: Union[str, bytes, Image.Image],
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract text using Tesseract OCR."""
        if not self.tesseract_available:
            return {
                "success": False,
                "error": "Tesseract OCR not available",
                "text": None
            }

        try:
            import pytesseract

            # Load and preprocess image
            processor = ImageProcessor()
            pil_image = processor.load_image(image)
            processed_image = processor.preprocess_image(pil_image)

            # Configure Tesseract
            lang_map = {
                'en': 'eng',
                'zh': 'chi_sim',
                'zh-cn': 'chi_sim',
                'zh-tw': 'chi_tra',
                'auto': 'eng+chi_sim'
            }
            tess_lang = lang_map.get(language or 'auto', 'eng+chi_sim')

            # Extract text
            config = '--oem 3 --psm 6'  # Use LSTM and assume uniform block of text
            text = pytesseract.image_to_string(processed_image, lang=tess_lang, config=config)

            # Get confidence data
            data = pytesseract.image_to_data(processed_image, lang=tess_lang, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "success": True,
                "text": text.strip(),
                "confidence": avg_confidence / 100.0,  # Convert to 0-1 range
                "method": "tesseract",
                "language": tess_lang
            }

        except Exception as e:
            self.logger.error(f"Tesseract OCR failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": None
            }

    async def extract_text_easyocr(
        self,
        image: Union[str, bytes, Image.Image],
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract text using EasyOCR."""
        if not self.easyocr_available:
            return {
                "success": False,
                "error": "EasyOCR not available",
                "text": None
            }

        try:
            self._init_easyocr()
            if not self.easyocr_reader:
                return {
                    "success": False,
                    "error": "Failed to initialize EasyOCR",
                    "text": None
                }

            # Load image
            processor = ImageProcessor()
            if isinstance(image, str):
                image_array = cv2.imread(image)
            elif isinstance(image, Image.Image):
                # Convert PIL to OpenCV format
                image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            else:
                # Assume it's already an image array
                image_array = image

            # Extract text
            results = self.easyocr_reader.readtext(image_array)

            # Process results
            text_lines = []
            confidences = []
            for (bbox, text, confidence) in results:
                text_lines.append(text)
                confidences.append(confidence)

            full_text = '\n'.join(text_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "success": True,
                "text": full_text.strip(),
                "confidence": avg_confidence,
                "method": "easyocr",
                "language": language or 'auto'
            }

        except Exception as e:
            self.logger.error(f"EasyOCR failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": None
            }

    async def extract_text(
        self,
        image: Union[str, bytes, Image.Image],
        language: Optional[str] = None,
        preferred_engine: str = "tesseract"
    ) -> Dict[str, Any]:
        """Extract text using available OCR engines."""
        engines = []

        # Determine engine order based on preference and availability
        if preferred_engine == "easyocr" and self.easyocr_available:
            engines = ["easyocr", "tesseract"]
        else:
            engines = ["tesseract", "easyocr"]

        # Try each engine
        for engine in engines:
            if engine == "tesseract" and self.tesseract_available:
                result = await self.extract_text_tesseract(image, language)
            elif engine == "easyocr" and self.easyocr_available:
                result = await self.extract_text_easyocr(image, language)
            else:
                continue

            if result["success"] and result.get("text", "").strip():
                return result

        # All engines failed
        return {
            "success": False,
            "error": "All OCR engines failed or no text detected",
            "text": None
        }


class OCRContentExtractor:
    """Main OCR content extractor with multiple engine support."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mistral_client = MistralOCRClient()
        self.fallback_client = FallbackOCRClient()
        self.enable_mistral = os.getenv("ENABLE_MISTRAL_OCR", "true").lower() == "true"
        self.enable_fallback = os.getenv("ENABLE_FALLBACK_OCR", "true").lower() == "true"

    async def extract_text(
        self,
        image: Union[str, bytes, Image.Image],
        language: Optional[str] = None,
        prefer_mistral: bool = True
    ) -> Dict[str, Any]:
        """Extract text from image using available OCR engines."""
        try:
            # Validate image first
            processor = ImageProcessor()
            try:
                image_info = processor.get_image_info(image)
                if "error" in image_info:
                    raise ValidationError(f"Invalid image: {image_info['error']}")
            except Exception as e:
                raise ValidationError(f"Image validation failed: {e}")

            results = []
            processing_order = []

            # Determine processing order
            if prefer_mistral and self.enable_mistral and self.mistral_client.enabled:
                processing_order = [("mistral", self.mistral_client)]

            if self.enable_fallback:
                processing_order.append(("fallback", self.fallback_client))

            # Try each engine
            for engine_name, client in processing_order:
                try:
                    self.logger.info(f"Trying OCR engine: {engine_name}")
                    result = await client.extract_text(image, language)
                    result["engine"] = engine_name
                    results.append(result)

                    if result["success"] and result.get("text", "").strip():
                        # Successful extraction
                        text = result["text"].strip()
                        if len(text) > 10:  # Minimum meaningful text
                            return {
                                "success": True,
                                "text": text,
                                "confidence": result.get("confidence", 0.0),
                                "engine": engine_name,
                                "language": result.get("language"),
                                "method": result.get("method"),
                                "all_results": results if len(results) > 1 else None
                            }

                except Exception as e:
                    self.logger.warning(f"OCR engine {engine_name} failed: {e}")
                    results.append({
                        "success": False,
                        "error": str(e),
                        "engine": engine_name
                    })

            # All engines failed
            return {
                "success": False,
                "error": "All OCR engines failed to extract text",
                "all_results": results
            }

        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }