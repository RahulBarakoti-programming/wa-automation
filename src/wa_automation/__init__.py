from .core import WhatsAppAutomation
from .exceptions import (
    WhatsAppAutomationError,
    WhatsAppAuthenticationError,
    WhatsAppLoadError,
    MessageSendError
)

__version__ = '0.1.2'
__author__ = 'Rahul Barakoti'
__email__ = 'rahulbarakoti5@gmail.com'

__all__ = [
    'WhatsAppAutomation',
    'WhatsAppAutomationError',
    'WhatsAppAuthenticationError',
    'WhatsAppLoadError',
    'MessageSendError'
]