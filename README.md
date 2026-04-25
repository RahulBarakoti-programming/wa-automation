# WA-Automation 📱✨

A powerful, undetected Python library for automating both **WhatsApp Web** and **Instagram** interactions using Selenium. This library provides a simple and intuitive interface for sending messages, scrapping profile data, posting photos, and dodging platform bot-detection schemas seamlessly.

## 🚀 Features

### Instagram Automation (NEW in v0.2.0)
- 🔐 Auto-login with session caching and 2FA support
- 💬 Send direct messages (DMs) straight to users
- 📊 Deep profile extraction (Followers, Following, Post Count, and Bios)
- 💭 Post scraping (Captions, Commenters, and direct Comment text)
- 📸 Upload and post photos with captions programmatically
- ❤️ Like posts and follow users automatically

### WhatsApp Automation
- 💬 Send text messages individually or in bulk
- 📸 Send images with captions
- 📎 Send documents and PDF files
- 🔄 Automatic QR code handling
- 🌐 Chrome session management to stay logged in

---

## 💻 Installation

Install the package using pip:

```bash
pip install wa-automation
```

---

## 📷 Instagram Quick Start

Here is a quick example of how you can set up a scraping and messaging workflow using the new Instagram engine:

```python
from wa_automation import InstagramAutomation

# Initialize Instagram automation
ig = InstagramAutomation()

# The library caches your session inside User_Data/Instagram!
if not ig.is_authenticated:
    ig.login("your_email@gmail.com", "your_password")

# 1. Scrape Profile Data
target_user = "scedexa_"
profile = ig.get_profile_info(target_user)
print(f"{profile['followers']} Followers | Bio: {profile['bio']}")

# 2. Scrape Recent Post and Comments
if profile['recent_posts']:
    post_data = ig.get_post_details(profile['recent_posts'][0])
    for comment in post_data['comments']:
        print(f"{comment['username']} said: {comment['text']}")

# 3. Send a Direct Message
ig.send_dm(target_user, "Hey! Tested my new automation bot successfully! 🚀")

# 4. Upload a Photo to your Grid
ig.post_photo("path/to/my_image.jpg", "Hello world from the Python API! #coding")

# Clean up
ig.cleanup()
```

---

## 💬 WhatsApp Quick Start

Here's a simple example to get you started with WhatsApp:

```python
from wa_automation import WhatsAppAutomation

# Initialize WhatsApp automation
whatsapp = WhatsAppAutomation()

# Send a message
whatsapp.send_message("1234567890", "Hello from WA-Automation!")

# Send an image with caption
whatsapp.send_image("1234567890", "path/to/image.jpg", "Check out this photo!")

# Clean up when done
whatsapp.cleanup()
```

---

## 🛡️ Anti-Detection Mechanisms

This library goes the extra mile to prevent account suspension:
- Uses `undetected-chromedriver` to mask Selenium hooks globally.
- Persists session storage (`User_Data`) directly to your disk, meaning you only need to sign in / scan QR codes **once**.
- Features simulated, human-like typing delays (`_type_like_human`).
- Safely bypasses virtual keyboard monitoring by invoking direct clipboard pasting (`_insert_text`).

---

## ⚠️ Error Handling

The library provides fine-grained, platform-specific custom exceptions for better error handling:

```python
from wa_automation import InstagramAutomation, InstagramDMError, InstagramAuthenticationError

ig = InstagramAutomation()

try:
    ig.login("email", "bad_pass")
except InstagramAuthenticationError as e:
    print(f"Login failed: {e}")

try:
    ig.send_dm("invalid_user_999", "Hello!")
except InstagramDMError as e:
    print(f"Failed to send DM: {e}")
```

---

## 🛠️ Prerequisites

- Python 3.8 or higher
- Google Chrome browser installed locally
- Stable internet connection

---

## 🤝 Contributing

Contributions are heavily encouraged! Since Social Media DOM structures update frequently, the fallback arrays (`_find_element_with_fallback`) are constantly evolving.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License & Disclaimer

This project is licensed under the MIT License. 

**Disclaimer**: This library is strictly intended for educational and local workflow automation mapping. It is **not** affiliated with Meta, WhatsApp, or Instagram. Please use responsibly and in accordance with the target platform's Terms of Service. Avoid heavy API spam. Always run with sleep delays.
