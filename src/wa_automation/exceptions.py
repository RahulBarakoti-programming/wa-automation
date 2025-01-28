class WhatsAppAutomationError(Exception):
    """Base exception for WhatsApp automation errors"""
    pass

class WhatsAppAuthenticationError(WhatsAppAutomationError):
    """Raised when authentication with WhatsApp Web fails"""
    pass

class WhatsAppLoadError(WhatsAppAutomationError):
    """Raised when WhatsApp Web fails to load properly"""
    pass

class MessageSendError(WhatsAppAutomationError):
    """Raised when a message fails to send"""
    pass