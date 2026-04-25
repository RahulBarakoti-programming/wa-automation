import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import json
from wa_automation import InstagramAutomation

def main():
    print("Initializing Instagram Automation...")
    ig = InstagramAutomation()

    # 1. Check if logged in. If not, log in.
    if not ig.is_authenticated:
        print("Not logged in. Starting login flow...")
        # Note: You can replace these with environment variables or inputs
        ig.login("rahulgayathri12@gmail.com", "rahulgayathri2118")
    else:
        print("Already logged in via session. Skipping login.")

    target_account = "scedexa_"

    # 2. Extract Data from Target Account
    print(f"\\n--- Scraping Data for {target_account} ---")
    try:
        profile_data = ig.get_profile_info(target_account)
        print(f"Stats: {profile_data['posts_count']} posts, {profile_data['followers']} followers, {profile_data['following']} following")
        print(f"Bio: {profile_data['bio']}")
        
        # 3. Go deep into their most recent post
        if profile_data["recent_posts"]:
            latest_post_url = profile_data["recent_posts"][0]
            print(f"\\nFetching latest post: {latest_post_url}")
            
            post_data = ig.get_post_details(latest_post_url)
            print(f"Caption: {post_data['caption'][:50]}...")
            
            print(f"\\nTop Commenters:")
            for comment in post_data["comments"][:3]: # Limit to top 3 for the test
                print(f"- {comment['username']} said: '{comment['text']}'")
                
                # Optional: You can uncomment below to go down the rabbit hole and scrape the commenter's bio too!
                # commenter_info = ig.get_profile_info(comment['username'])
                # print(f"  -> Bio: {commenter_info['bio']}")
        else:
            print("No recent posts found.")
            
    except Exception as e:
        print(f"Error scraping data: {str(e)}")

    # 4. Action: Send DM
    print(f"\\n--- Sending DM to {target_account} ---")
    try:
        message = "Hey! I loved your recent post. I'm building an automation tool and just wanted to test this!"
        success = ig.send_dm(target_account, message)
        if success:
            print(f"✅ Successfully sent DM to {target_account}!")
    except Exception as e:
        print(f"❌ Failed to send DM: {str(e)}")

    print("\\nDone! Cleaning up...")
    ig.cleanup()

if __name__ == "__main__":
    main()
