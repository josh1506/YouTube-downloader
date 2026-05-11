"""Custom exceptions for the ytdl package."""


class YTDLError(Exception):
    """Base exception for all ytdl errors."""


class NoFormatsFoundError(YTDLError):
    """Raised when no downloadable formats are found for a URL."""


class InvalidQualityError(YTDLError):
    """Raised when a requested quality is not available for a video."""


class InvalidLanguageError(YTDLError):
    """Raised when a requested audio language is not available."""
