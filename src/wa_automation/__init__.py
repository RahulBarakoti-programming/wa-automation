from .core import WhatsAppAutomation
from .instagram import InstagramAutomation
from .exceptions import (
    WhatsAppAutomationError,
    WhatsAppAuthenticationError,
    WhatsAppLoadError,
    MessageSendError,
    InstagramAutomationError,
    InstagramAuthenticationError,
    InstagramLoadError,
    InstagramActionError,
    InstagramPostError,
    InstagramDMError
)

__version__ = '0.1.5'
__author__ = 'Rahul Barakoti'
__email__ = 'rahulbarakoti5@gmail.com'

__all__ = [
    'WhatsAppAutomation',
    'WhatsAppAutomationError',
    'WhatsAppAuthenticationError',
    'WhatsAppLoadError',
    'MessageSendError',
    'InstagramAutomation',
    'InstagramAutomationError',
    'InstagramAuthenticationError',
    'InstagramLoadError',
    'InstagramActionError',
    'InstagramPostError',
    'InstagramDMError'
]