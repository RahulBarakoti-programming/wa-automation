class WhatsAppAutomationError(Exception):
    """Base exception for WhatsApp automation errors"""
    pass

class WhatsAppAuthenticationError(WhatsAppAutomationError):
    """Raised when authentication with WhatsApp Web fails"""
    pass

class WhatsAppLoadError(WhatsAppAutomationError):
    """Raised when WhatsApp Web fails to load."""
    pass

class MessageSendError(WhatsAppAutomationError):
    """Raised when failing to send a message."""
    pass

class InstagramAutomationError(Exception):
    """Base exception for all Instagram related errors."""
    pass

class InstagramAuthenticationError(InstagramAutomationError):
    """Raised when failing to authenticate or login to Instagram."""
    pass

class InstagramLoadError(InstagramAutomationError):
    """Raised when Instagram fails to load."""
    pass

class InstagramActionError(InstagramAutomationError):
    """Raised when failing to perform a direct action (like, follow)."""
    pass

class InstagramPostError(InstagramAutomationError):
    """Raised when failing to upload a post."""
    pass

class InstagramDMError(InstagramAutomationError):
    """Raised when failing to send a DM."""
    pass