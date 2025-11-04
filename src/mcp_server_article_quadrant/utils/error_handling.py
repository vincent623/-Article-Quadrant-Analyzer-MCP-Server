"""Error handling utilities for the Article Quadrant Analyzer MCP Server."""

import logging
import traceback
from typing import Dict, Any, Optional, List
from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for better classification."""
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    CONTENT = "content"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    API = "api"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    RATE_LIMITING = "rate_limiting"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class AnalysisError(Exception):
    """Base exception for all analysis errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        suggested_actions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.suggested_actions = suggested_actions or []
        self.traceback_str = traceback.format_exc()


class ContentExtractionError(AnalysisError):
    """Content extraction specific errors."""

    def __init__(
        self,
        message: str,
        source_type: Optional[str] = None,
        source_info: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, category=ErrorCategory.CONTENT, **kwargs)
        self.source_type = source_type
        self.source_info = source_info


class InsightAnalysisError(AnalysisError):
    """Insight analysis specific errors."""

    def __init__(
        self,
        message: str,
        analysis_type: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, category=ErrorCategory.ANALYSIS, **kwargs)
        self.analysis_type = analysis_type
        self.language = language


class QuadrantGenerationError(AnalysisError):
    """Quadrant visualization errors."""

    def __init__(
        self,
        message: str,
        visualization_type: Optional[str] = None,
        config_issue: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, category=ErrorCategory.VISUALIZATION, **kwargs)
        self.visualization_type = visualization_type
        self.config_issue = config_issue


class MistralAPIError(AnalysisError):
    """Mistral Document AI API specific errors."""

    def __init__(
        self,
        message: str,
        api_endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(message, category=ErrorCategory.API, **kwargs)
        self.api_endpoint = api_endpoint
        self.status_code = status_code
        self.response_data = response_data


class OCRError(AnalysisError):
    """OCR processing errors."""

    def __init__(
        self,
        message: str,
        ocr_engine: Optional[str] = None,
        image_info: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, category=ErrorCategory.ANALYSIS, **kwargs)
        self.ocr_engine = ocr_engine
        self.image_info = image_info


class NetworkError(AnalysisError):
    """Network-related errors."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)
        self.url = url
        self.timeout = timeout


class ValidationError(AnalysisError):
    """Input validation errors."""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)
        self.field_name = field_name
        self.field_value = field_value


def get_error_guidance(error: Exception) -> List[str]:
    """Provide suggested actions for common error types."""
    suggestions = []

    if isinstance(error, NetworkError):
        suggestions.extend([
            "Check your internet connection",
            "Verify the URL is accessible",
            "Try again with a different source",
            "Check if the website blocks automated requests"
        ])
    elif isinstance(error, ContentExtractionError):
        if error.source_type == "url":
            suggestions.extend([
                "Check if the URL is valid and accessible",
                "Verify the website allows content extraction",
                "Try a different article from the same site",
                "Check for paywall restrictions"
            ])
        elif error.source_type == "file_path":
            suggestions.extend([
                "Verify the file path is correct",
                "Check file permissions",
                "Ensure the file format is supported",
                "Try with a smaller file"
            ])
        elif error.source_type == "direct_text":
            suggestions.extend([
                "Check text encoding",
                "Ensure text is not empty",
                "Try with shorter text content"
            ])
    elif isinstance(error, OCRError):
        suggestions.extend([
            "Check image quality and resolution",
            "Ensure text is clearly visible",
            "Try with a different image format",
            "Check if OCR service is available"
        ])
    elif isinstance(error, MistralAPIError):
        if error.status_code == 401:
            suggestions.extend([
                "Check your Mistral API key",
                "Verify API key permissions",
                "Ensure API key is valid and not expired"
            ])
        elif error.status_code == 429:
            suggestions.extend([
                "Wait and try again later",
                "Check API rate limits",
                "Consider using fallback OCR"
            ])
        else:
            suggestions.extend([
                "Check Mistral API service status",
                "Verify API endpoint is correct",
                "Try with fallback OCR option"
            ])
    elif isinstance(error, ValidationError):
        suggestions.extend([
            "Check input parameter formats",
            "Verify required fields are provided",
            "Ensure values are within allowed ranges"
        ])
    elif isinstance(error, QuadrantGenerationError):
        suggestions.extend([
            "Check quadrant configuration parameters",
            "Verify insight data format",
            "Ensure coordinates are within valid ranges (-1 to 1)",
            "Try with fewer insights for better visualization"
        ])
    else:
        suggestions.extend([
            "Try again with different content",
            "Check system resources",
            "Contact support if the issue persists"
        ])

    return suggestions


def format_error_response(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """Format a standardized error response."""
    context = context or {}

    # Determine error details based on error type
    error_details = {}

    if isinstance(error, (NetworkError, ContentExtractionError)):
        error_details.update({
            "source_type": getattr(error, 'source_type', None),
            "source_info": getattr(error, 'source_info', None),
            "url": getattr(error, 'url', None)
        })
    elif isinstance(error, (MistralAPIError, OCRError)):
        error_details.update({
            "api_endpoint": getattr(error, 'api_endpoint', None),
            "status_code": getattr(error, 'status_code', None),
            "ocr_engine": getattr(error, 'ocr_engine', None),
            "image_info": getattr(error, 'image_info', None)
        })
    elif isinstance(error, ValidationError):
        error_details.update({
            "field_name": getattr(error, 'field_name', None),
            "field_value": getattr(error, 'field_value', None)
        })
    elif isinstance(error, QuadrantGenerationError):
        error_details.update({
            "visualization_type": getattr(error, 'visualization_type', None),
            "config_issue": getattr(error, 'config_issue', None)
        })

    # Build error response
    response = {
        "success": False,
        "error": {
            "type": error.__class__.__name__,
            "message": str(error),
            "category": getattr(error, 'category', ErrorCategory.UNKNOWN),
            "severity": getattr(error, 'severity', ErrorSeverity.MEDIUM),
            "details": error_details,
            "context": context,
            "suggested_actions": getattr(error, 'suggested_actions', []) or get_error_guidance(error)
        }
    }

    # Include traceback in debug mode
    if include_traceback and hasattr(error, 'traceback_str'):
        response["error"]["traceback"] = error.traceback_str

    return response


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """Handle an error and return a formatted response."""

    # Log the error
    if logger:
        logger.error(f"Error occurred: {error.__class__.__name__}: {error}")
        if context:
            logger.error(f"Error context: {context}")

        # Log traceback for higher severity errors
        if hasattr(error, 'severity') and error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(f"Traceback: {traceback.format_exc()}")

    # Format and return error response
    return format_error_response(error, context, include_traceback)


def create_success_response(
    data: Any,
    processing_time: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = {
        "success": True,
        "data": data
    }

    # Add optional fields
    if processing_time is not None:
        response["processing_time"] = processing_time

    if metadata:
        response["metadata"] = metadata

    if warnings:
        response["warnings"] = warnings

    return response


class ErrorContext:
    """Context manager for error handling with automatic context capture."""

    def __init__(
        self,
        operation: str,
        logger: Optional[logging.Logger] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.logger = logger or logging.getLogger(__name__)
        self.context = context or {}
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.info(f"Starting operation: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        processing_time = time.time() - self.start_time if self.start_time else 0

        if exc_type is None:
            # Operation completed successfully
            self.logger.info(f"Operation completed: {self.operation} in {processing_time:.2f}s")
            return False
        else:
            # Operation failed
            self.logger.error(f"Operation failed: {self.operation} in {processing_time:.2f}s")
            self.context["processing_time"] = processing_time
            self.context["operation"] = self.operation

            # Convert exception to appropriate error type if needed
            if not isinstance(exc_val, AnalysisError):
                # Wrap generic exceptions
                error = AnalysisError(
                    message=str(exc_val),
                    details={"original_exception": exc_type.__name__},
                    context=self.context
                )
                # Replace the original exception with our wrapped version
                raise error from exc_val

            # Add context to existing analysis error
            exc_val.details.update(self.context)

            return False  # Don't suppress the exception