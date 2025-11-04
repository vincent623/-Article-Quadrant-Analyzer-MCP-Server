"""Content extraction utilities for articles, documents, and images."""

import asyncio
import logging
import os
import re
import tempfile
import time
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from urllib.parse import urlparse, urljoin

import aiofiles
from bs4 import BeautifulSoup

try:
    import newspaper
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

try:
    from readability import Document as ReadabilityDocument
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from mcp_server_article_quadrant.utils.error_handling import (
    ContentExtractionError, NetworkError, ValidationError,
    ErrorContext, handle_error
)
from mcp_server_article_quadrant.utils.http_client import get_http_client
from mcp_server_article_quadrant.utils.image_processor import OCRContentExtractor, ImageProcessor


class WebContentExtractor:
    """Extract content from web URLs with support for various site types."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ocr_extractor = OCRContentExtractor()

    def _is_news_url(self, url: str) -> bool:
        """Check if URL is from a known news site."""
        news_domains = [
            'cnn.com', 'bbc.com', 'reuters.com', 'ap.org', 'npr.org',
            'wsj.com', 'nytimes.com', 'washingtonpost.com', 'theguardian.com',
            'xinhuanet.com', 'people.com.cn', 'cctv.com', 'chinadaily.com.cn',
            'sina.com.cn', 'qq.com', '163.com', 'sohu.com', 'ifeng.com'
        ]
        try:
            domain = urlparse(url).netloc.lower()
            return any(news_domain in domain for news_domain in news_domains)
        except Exception:
            return False

    def _is_wechat_url(self, url: str) -> bool:
        """Check if URL is from WeChat public account."""
        try:
            domain = urlparse(url).netloc.lower()
            return 'mp.weixin.qq.com' in domain
        except Exception:
            return False

    async def extract_with_newspaper3k(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """Extract content using newspaper3k library."""
        try:
            # Create newspaper article
            article = newspaper.Article(url, language='auto')

            # Set timeout and download
            article.config.timeout = timeout
            article.download()

            if article.download_state == 0:  # Download failed
                raise ContentExtractionError(
                    "Failed to download article",
                    source_type="url",
                    source_info=url
                )

            # Parse article
            article.parse()

            # Extract additional metadata
            article.nlp() if hasattr(article, 'nlp') else None

            # Clean HTML content
            text = article.text
            if not text or len(text.strip()) < 50:
                # Fallback to basic HTML extraction
                html_content = article.html
                text = self._extract_text_from_html(html_content)

            metadata = {
                "title": article.title,
                "authors": article.authors,
                "publish_date": article.publish_date.isoformat() if article.publish_date else None,
                "source_url": url,
                "top_image": article.top_image,
                "images": article.images,
                "movies": article.movies,
                "keywords": getattr(article, 'keywords', []),
                "summary": getattr(article, 'summary', ''),
                "extraction_method": "newspaper3k"
            }

            return {
                "success": True,
                "content": {
                    "title": article.title,
                    "text": text,
                    "metadata": metadata
                }
            }

        except Exception as e:
            self.logger.warning(f"Newspaper3k extraction failed for {url}: {e}")
            raise ContentExtractionError(
                f"Newspaper3k extraction failed: {e}",
                source_type="url",
                source_info=url,
                details={"url": url, "error": str(e)}
            )

    async def extract_with_readability(self, url: str) -> Dict[str, Any]:
        """Extract content using readability-lxml."""
        try:
            async with get_http_client() as client:
                response = await client.get(url)
                html_content = response.text

            # Use readability to extract main content
            doc = ReadabilityDocument(html_content)
            title = doc.title()
            text = doc.summary()

            # Extract metadata
            soup = BeautifulSoup(html_content, 'html.parser')

            # Try to extract author
            author = None
            author_meta = soup.find('meta', {'name': 'author'})
            if author_meta:
                author = author_meta.get('content')

            # Try to extract publication date
            pub_date = None
            date_meta = soup.find('meta', {'property': 'article:published_time'})
            if date_meta:
                pub_date = date_meta.get('content')

            metadata = {
                "title": title,
                "author": author,
                "publication_date": pub_date,
                "source_url": url,
                "extraction_method": "readability",
                "readability_score": getattr(doc, 'score', None)
            }

            return {
                "success": True,
                "content": {
                    "title": title,
                    "text": BeautifulSoup(text, 'html.parser').get_text(),
                    "metadata": metadata
                }
            }

        except Exception as e:
            self.logger.warning(f"Readability extraction failed for {url}: {e}")
            raise ContentExtractionError(
                f"Readability extraction failed: {e}",
                source_type="url",
                source_info=url
            )

    async def extract_wechat_content(self, url: str) -> Dict[str, Any]:
        """Extract content from WeChat public account articles."""
        try:
            async with get_http_client() as client:
                response = await client.get(url)
                html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')

            # WeChat specific selectors
            title_elem = soup.find('h1', {'class': 'rich_media_title'}) or soup.find('h2', {'class': 'rich_media_title'})
            title = title_elem.get_text().strip() if title_elem else ""

            # Extract main content
            content_elem = soup.find('div', {'class': 'rich_media_content'}) or soup.find('div', {'id': 'js_content'})
            if content_elem:
                text = content_elem.get_text(separator='\n', strip=True)
            else:
                # Fallback to general extraction
                text = self._extract_text_from_html(html_content)

            # Extract WeChat-specific metadata
            account_name_elem = soup.find('span', {'class': 'rich_media_meta rich_media_meta_nickname'})
            account_name = account_name_elem.get_text().strip() if account_name_elem else None

            publish_time_elem = soup.find('em', {'class': 'rich_media_meta_text'})
            publish_time = publish_time_elem.get_text().strip() if publish_time_elem else None

            metadata = {
                "title": title,
                "author": account_name,
                "publication_date": publish_time,
                "source_url": url,
                "account_name": account_name,
                "extraction_method": "wechat_specific"
            }

            return {
                "success": True,
                "content": {
                    "title": title,
                    "text": text,
                    "metadata": metadata
                }
            }

        except Exception as e:
            self.logger.warning(f"WeChat extraction failed for {url}: {e}")
            # Fallback to general extraction
            return await self.extract_with_readability(url)

    def _extract_text_from_html(self, html_content: str) -> str:
        """Basic text extraction from HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator='\n')

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            self.logger.error(f"HTML text extraction failed: {e}")
            return ""

    async def extract_from_url(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from URL with automatic method selection."""
        timeout = options.get('timeout', 30)
        clean_html = options.get('clean_html', True)
        min_length = options.get('min_length', 100)
        max_content_length = options.get('max_content_length', 50000)

        try:
            with ErrorContext("url_content_extraction", context={"url": url}):
                self.logger.info(f"Extracting content from URL: {url}")

                # Validate URL
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValidationError(f"Invalid URL: {url}", field_name="url", field_value=url)

                # Choose extraction method based on URL type
                if self._is_wechat_url(url):
                    self.logger.info("Using WeChat-specific extraction")
                    result = await self.extract_wechat_content(url)
                elif self._is_news_url(url):
                    self.logger.info("Using newspaper3k for news site")
                    try:
                        result = await self.extract_with_newspaper3k(url, timeout)
                    except Exception:
                        self.logger.info("Falling back to readability extraction")
                        result = await self.extract_with_readability(url)
                else:
                    # Try newspaper3k first, then readability
                    try:
                        result = await self.extract_with_newspaper3k(url, timeout)
                    except Exception:
                        result = await self.extract_with_readability(url)

                if not result["success"]:
                    return result

                content = result["content"]
                text = content["text"]

                # Validate extracted content
                if not text or len(text.strip()) < min_length:
                    raise ContentExtractionError(
                        f"Extracted content too short: {len(text) if text else 0} characters (minimum: {min_length})",
                        source_type="url",
                        source_info=url
                    )

                # Truncate if too long
                if max_content_length and len(text) > max_content_length:
                    text = text[:max_content_length] + "\n\n[Content truncated due to length limit]"
                    content["text"] = text

                # Add additional metadata
                if "metadata" not in content:
                    content["metadata"] = {}

                content["metadata"].update({
                    "word_count": len(text.split()),
                    "language": self._detect_language(text),
                    "extraction_timestamp": time.time()
                })

                # Update result
                result["content"] = content
                result["warnings"] = []

                if max_content_length and len(content["text"]) > max_content_length * 0.9:
                    result["warnings"].append("Content was truncated due to length limit")

                return result

        except Exception as e:
            self.logger.error(f"URL content extraction failed: {e}")
            return handle_error(e, context={"url": url, "options": options})


class FileContentExtractor:
    """Extract content from local files."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ocr_extractor = OCRContentExtractor()
        self.supported_text_formats = {'.txt', '.md', '.html', '.htm'}
        self.supported_pdf_formats = {'.pdf'}
        self.supported_image_formats = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}

    async def extract_from_file(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from local file."""
        try:
            with ErrorContext("file_content_extraction", context={"file_path": file_path}):
                # Validate file path
                path = Path(file_path)
                if not path.exists():
                    raise ContentExtractionError(
                        f"File not found: {file_path}",
                        source_type="file_path",
                        source_info=file_path
                    )

                if not path.is_file():
                    raise ContentExtractionError(
                        f"Path is not a file: {file_path}",
                        source_type="file_path",
                        source_info=file_path
                    )

                # Check file size
                file_size = path.stat().st_size
                max_size = options.get('max_file_size_mb', 50) * 1024 * 1024
                if file_size > max_size:
                    raise ContentExtractionError(
                        f"File too large: {file_size} bytes (maximum: {max_size} bytes)",
                        source_type="file_path",
                        source_info=file_path
                    )

                file_ext = path.suffix.lower()
                encoding = options.get('encoding', 'utf-8')

                # Extract content based on file type
                if file_ext in self.supported_text_formats:
                    return await self._extract_text_file(file_path, encoding)
                elif file_ext in self.supported_pdf_formats:
                    return await self._extract_pdf_file(file_path, options)
                elif file_ext in self.supported_image_formats:
                    return await self._extract_image_file(file_path, options)
                else:
                    raise ContentExtractionError(
                        f"Unsupported file format: {file_ext}",
                        source_type="file_path",
                        source_info=file_path,
                        details={"supported_formats": list(
                            self.supported_text_formats | self.supported_pdf_formats | self.supported_image_formats
                        )}
                    )

        except Exception as e:
            self.logger.error(f"File content extraction failed: {e}")
            return handle_error(e, context={"file_path": file_path, "options": options})

    async def _extract_text_file(self, file_path: str, encoding: str) -> Dict[str, Any]:
        """Extract content from text files."""
        try:
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                content_text = await f.read()

            if not content_text.strip():
                raise ContentExtractionError(
                    "File is empty or contains no readable text",
                    source_type="file_path",
                    source_info=file_path
                )

            # Extract title from filename or first line
            path = Path(file_path)
            title = path.stem.replace('_', ' ').replace('-', ' ').title()

            # Try to get a better title from first line if it looks like a title
            first_line = content_text.split('\n')[0].strip()
            if len(first_line) < 100 and not first_line.endswith('.'):
                title = first_line

            metadata = {
                "title": title,
                "source_url": f"file://{file_path}",
                "file_name": path.name,
                "file_size": path.stat().st_size,
                "word_count": len(content_text.split()),
                "language": self._detect_language(content_text),
                "extraction_method": "text_file"
            }

            return {
                "success": True,
                "content": {
                    "title": title,
                    "text": content_text,
                    "metadata": metadata
                }
            }

        except UnicodeDecodeError as e:
            raise ContentExtractionError(
                f"Text encoding error: {e}",
                source_type="file_path",
                source_info=file_path,
                details={"encoding": encoding}
            )
        except Exception as e:
            raise ContentExtractionError(
                f"Failed to read text file: {e}",
                source_type="file_path",
                source_info=file_path
            )

    async def _extract_pdf_file(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from PDF files."""
        try:
            import pypdf

            content_text = ""
            metadata = {}

            async with aiofiles.open(file_path, 'rb') as f:
                pdf_content = await f.read()

            # Extract text from PDF
            pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_content))

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        content_text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
                except Exception as e:
                    self.logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")

            # Extract PDF metadata
            if pdf_reader.metadata:
                metadata.update({
                    "title": pdf_reader.metadata.get('/Title', ''),
                    "author": pdf_reader.metadata.get('/Author', ''),
                    "subject": pdf_reader.metadata.get('/Subject', ''),
                    "creator": pdf_reader.metadata.get('/Creator', ''),
                    "producer": pdf_reader.metadata.get('/Producer', ''),
                    "creation_date": str(pdf_reader.metadata.get('/CreationDate', '')),
                    "modification_date": str(pdf_reader.metadata.get('/ModDate', '')),
                })

            if not content_text.strip():
                # Try OCR fallback if available
                self.logger.info("PDF text extraction failed, trying OCR fallback")
                return await self._extract_pdf_with_ocr(file_path, options)

            path = Path(file_path)
            metadata.update({
                "source_url": f"file://{file_path}",
                "file_name": path.name,
                "file_size": path.stat().st_size,
                "page_count": len(pdf_reader.pages),
                "word_count": len(content_text.split()),
                "language": self._detect_language(content_text),
                "extraction_method": "pypdf"
            })

            # Use PDF title or filename as title
            title = metadata.get("title") or path.stem.replace('_', ' ').replace('-', ' ').title()

            return {
                "success": True,
                "content": {
                    "title": title,
                    "text": content_text.strip(),
                    "metadata": metadata
                }
            }

        except ImportError:
            # pypdf not available, try OCR
            self.logger.warning("pypdf not available, falling back to OCR")
            return await self._extract_pdf_with_ocr(file_path, options)
        except Exception as e:
            raise ContentExtractionError(
                f"PDF extraction failed: {e}",
                source_type="file_path",
                source_info=file_path
            )

    async def _extract_pdf_with_ocr(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from PDF using OCR."""
        try:
            # Convert PDF to images and run OCR
            # This is a simplified implementation - in practice you'd want more sophisticated PDF-to-image conversion
            import fitz  # PyMuPDF

            path = Path(file_path)
            all_text = ""

            pdf_document = fitz.open(file_path)

            for page_num in range(len(pdf_document)):
                # Convert page to image
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR

                # Convert to PIL Image
                img_data = pix.tobytes("png")

                # Run OCR
                ocr_result = await self.ocr_extractor.extract_text(
                    img_data,
                    language=options.get('language', 'auto')
                )

                if ocr_result["success"]:
                    all_text += f"\n\n--- Page {page_num + 1} ---\n\n{ocr_result['text']}"

            pdf_document.close()

            if not all_text.strip():
                raise ContentExtractionError(
                    "OCR extraction failed for PDF",
                    source_type="file_path",
                    source_info=file_path
                )

            metadata = {
                "title": path.stem.replace('_', ' ').replace('-', ' ').title(),
                "source_url": f"file://{file_path}",
                "file_name": path.name,
                "file_size": path.stat().st_size,
                "word_count": len(all_text.split()),
                "language": self._detect_language(all_text),
                "extraction_method": "pdf_ocr"
            }

            return {
                "success": True,
                "content": {
                    "title": metadata["title"],
                    "text": all_text.strip(),
                    "metadata": metadata
                }
            }

        except ImportError:
            raise ContentExtractionError(
                "PDF OCR requires PyMuPDF (fitz) package",
                source_type="file_path",
                source_info=file_path
            )
        except Exception as e:
            raise ContentExtractionError(
                f"PDF OCR extraction failed: {e}",
                source_type="file_path",
                source_info=file_path
            )

    async def _extract_image_file(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from image files using OCR."""
        try:
            ocr_result = await self.ocr_extractor.extract_text(
                file_path,
                language=options.get('language', 'auto')
            )

            if not ocr_result["success"] or not ocr_result.get("text", "").strip():
                raise ContentExtractionError(
                    "No text could be extracted from image",
                    source_type="file_path",
                    source_info=file_path,
                    details={"ocr_error": ocr_result.get("error")}
                )

            path = Path(file_path)
            text = ocr_result["text"]

            metadata = {
                "title": f"Text from {path.name}",
                "source_url": f"file://{file_path}",
                "file_name": path.name,
                "file_size": path.stat().st_size,
                "word_count": len(text.split()),
                "language": ocr_result.get("language") or self._detect_language(text),
                "extraction_method": "image_ocr",
                "ocr_engine": ocr_result.get("engine"),
                "ocr_confidence": ocr_result.get("confidence", 0.0)
            }

            return {
                "success": True,
                "content": {
                    "title": metadata["title"],
                    "text": text,
                    "metadata": metadata
                },
                "warnings": ["Text extracted from image using OCR - may contain errors"]
            }

        except Exception as e:
            raise ContentExtractionError(
                f"Image OCR extraction failed: {e}",
                source_type="file_path",
                source_info=file_path
            )

    def _detect_language(self, text: str) -> str:
        """Simple language detection."""
        try:
            from langdetect import detect
            return detect(text)
        except Exception:
            # Fallback: simple heuristics
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            total_chars = len(re.sub(r'\s', '', text))

            if total_chars > 0 and chinese_chars / total_chars > 0.3:
                return 'zh'
            else:
                return 'en'


class ContentExtractor:
    """Main content extractor that coordinates different extraction methods."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.web_extractor = WebContentExtractor()
        self.file_extractor = FileContentExtractor()

    async def extract_content(
        self,
        source: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract content from various sources."""
        start_time = time.time()
        options = options or {}

        try:
            source_type = source.get('type')
            content = source.get('content')

            if not source_type or not content:
                raise ValidationError(
                    "Source must have both 'type' and 'content'",
                    field_name="source"
                )

            # Route to appropriate extractor
            if source_type == 'url':
                result = await self.web_extractor.extract_from_url(content, options)
            elif source_type == 'file_path':
                result = await self.file_extractor.extract_from_file(content, options)
            elif source_type == 'direct_text':
                result = self._process_direct_text(content, options)
            else:
                raise ValidationError(
                    f"Unsupported source type: {source_type}",
                    field_name="type",
                    field_value=source_type
                )

            # Add processing time
            processing_time = time.time() - start_time
            if isinstance(result, dict):
                result["processing_time"] = processing_time

            return result

        except Exception as e:
            self.logger.error(f"Content extraction failed: {e}")
            return handle_error(
                e,
                context={"source": source, "options": options},
                logger=self.logger
            )

    def _process_direct_text(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process direct text input."""
        try:
            if not text or not text.strip():
                raise ContentExtractionError(
                    "Direct text content is empty",
                    source_type="direct_text"
                )

            # Clean up text
            clean_text = text.strip()

            # Try to extract title from first line if it looks like a title
            lines = clean_text.split('\n')
            title = "Direct Text Input"
            if len(lines) > 1 and len(lines[0]) < 100 and not lines[0].endswith('.'):
                title = lines[0].strip()
                # Remove title from main text
                clean_text = '\n'.join(lines[1:]).strip()

            metadata = {
                "title": title,
                "source_url": None,
                "word_count": len(clean_text.split()),
                "language": self._detect_language(clean_text),
                "extraction_method": "direct_text"
            }

            return {
                "success": True,
                "content": {
                    "title": title,
                    "text": clean_text,
                    "metadata": metadata
                },
                "processing_time": 0.0
            }

        except Exception as e:
            raise ContentExtractionError(
                f"Direct text processing failed: {e}",
                source_type="direct_text"
            )

    def _detect_language(self, text: str) -> str:
        """Simple language detection."""
        try:
            from langdetect import detect
            return detect(text)
        except Exception:
            # Fallback: simple heuristics
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            total_chars = len(re.sub(r'\s', '', text))

            if total_chars > 0 and chinese_chars / total_chars > 0.3:
                return 'zh'
            else:
                return 'en'