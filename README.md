# WA-Automation

A powerful Python library for automating WhatsApp Web interactions using Selenium. This library provides a simple and intuitive interface for sending messages, images, and files through WhatsApp Web.

## Features

- 💬 Send text messages
- 📸 Send images with captions
- 📎 Send files with captions
- 🔄 Automatic QR code handling
- 🌐 Chrome session management
- 🔒 Secure and reliable automation

## Installation

Install the package using pip:

```bash
pip install wa-automation
```

## Quick Start

Here's a simple example to get you started:

```python
from wa_automation import WhatsAppAutomation

# Initialize WhatsApp automation
whatsapp = WhatsAppAutomation()

# Send a message
whatsapp.send_message("1234567890", "Hello from WA-Automation!")

# Send an image with caption
whatsapp.send_image("1234567890", "path/to/image.jpg", "Check out this photo!")

# Send a file with caption
whatsapp.send_file("1234567890", "path/to/document.pdf", "Here's the document you requested")

# Clean up when done
whatsapp.cleanup()
```

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- Stable internet connection
- Active WhatsApp account

## Detailed Usage

### Initialization

```python
from wa_automation import WhatsAppAutomation

# Default initialization
whatsapp = WhatsAppAutomation()

# Custom user data directory
whatsapp = WhatsAppAutomation(user_data_dir="custom/path/to/user_data")
```

### Sending Messages

```python
# Simple text message
whatsapp.send_message("1234567890", "Hello!")

# Send to multiple numbers
numbers = ["1234567890", "0987654321"]
for number in numbers:
    whatsapp.send_message(number, "Bulk message")
```

### Sending Images

```python
# Send image without caption
whatsapp.send_image("1234567890", "path/to/image.jpg")

# Send image with caption
whatsapp.send_image("1234567890", "path/to/image.jpg", "Beautiful sunset!")
```

### Sending Files

```python
# Send file without caption
whatsapp.send_file("1234567890", "path/to/document.pdf")

# Send file with caption
whatsapp.send_file("1234567890", "path/to/document.pdf", "Monthly report")
```

## Error Handling

The library provides custom exceptions for better error handling:

```python
from wa_automation import WhatsAppAutomationError, MessageSendError

try:
    whatsapp.send_message("1234567890", "Hello!")
except MessageSendError as e:
    print(f"Failed to send message: {e}")
except WhatsAppAutomationError as e:
    print(f"General automation error: {e}")
```

## Best Practices

1. Always use the `cleanup()` method when you're done:

   ```python
   try:
       whatsapp.send_message("1234567890", "Hello!")
   finally:
       whatsapp.cleanup()
   ```

2. Use context manager (coming soon):

   ```python
   with WhatsAppAutomation() as whatsapp:
       whatsapp.send_message("1234567890", "Hello!")
   ```

3. Handle rate limiting:

   ```python
   import time

   numbers = ["1234567890", "0987654321"]
   for number in numbers:
       whatsapp.send_message(number, "Hello!")
       time.sleep(2)  # Add delay between messages
   ```

## Known Limitations

- Requires active internet connection
- Chrome browser must be installed
- Phone must be connected to WhatsApp Web
- Message delivery depends on recipient's connectivity

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This library is not affiliated with WhatsApp Inc. Please use responsibly and in accordance with WhatsApp's terms of service.

## Support

For support, please:

1. Check the [documentation](https://github.com/yourusername/wa-automation/wiki)
2. Search [existing issues](https://github.com/yourusername/wa-automation/issues)
3. Create a new issue if needed

## Changelog

### 0.1.0 (2024-01-28)

- Initial release
- Basic messaging functionality
- Image and file sending support
- QR code handling
- Session management
