"""
Simple test script to send a WhatsApp message using wa-automation
"""
from wa_automation import WhatsAppAutomation

def main():
    # Initialize WhatsApp automation
    print("Initializing WhatsApp automation...")
    wa = WhatsAppAutomation(chrome_version=146)
    
    try:
        # Send test message
        phone_number = "+918864988395"  # Indian number with country code
        message = (
            "Hello! This is a test from *wa-automation*.\n\n"
            "This message should have:\n"
            "1. *Bold text*\n"
            "2. _Italic text_\n"
            "3. Proper newlines."
        )
        
        print(f"Sending message to {phone_number}...")
        wa.send_message(phone_number, message)
        print("Message sent successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        print("Cleaning up...")
        wa.cleanup()
        print("Done!")

if __name__ == "__main__":
    main()
