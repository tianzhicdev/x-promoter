#!/usr/bin/env python3

import tweepy
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
consumer_key = os.environ.get("X_API_KEY")
consumer_secret = os.environ.get("X_API_KEY_SECRETS")
access_token = os.environ.get("X_ACCESS_TOKEN")
access_token_secret = os.environ.get("X_ACCESS_TOKEN_SECRETS")

# Check if all credentials are present
if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
    print("❌ Missing credentials. Please check your .env file")
    exit(1)

# Create Twitter API v2 client
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

def load_ready_tweets():
    """Load tweets ready to send"""
    try:
        with open('/app/data/ready_to_send.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No tweets ready to send. Run prepare first.")
        return []

def load_sent_tweets():
    """Load sent tweets history"""
    try:
        with open('/app/data/sent_tweets.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_sent_tweets(sent_tweets):
    """Save sent tweets history"""
    with open('/app/data/sent_tweets.json', 'w', encoding='utf-8') as f:
        json.dump(sent_tweets, f, indent=2, ensure_ascii=False)

def send_tweets():
    """Send all prepared tweets"""
    # Load ready tweets
    ready_tweets = load_ready_tweets()
    
    if not ready_tweets:
        print("❌ No tweets to send")
        return
    
    # Load sent history
    sent_tweets = load_sent_tweets()
    
    print(f"📤 Sending {len(ready_tweets)} prepared tweets...")
    
    successfully_sent = []
    failed_tweets = []
    
    for i, tweet_data in enumerate(ready_tweets):
        print(f"\n🔄 Sending tweet {i+1}/{len(ready_tweets)}")
        print(f"   Target: {tweet_data['target_tweet']['text'][:50]}...")
        print(f"   Reply: {tweet_data['reply_text'][:100]}...")
        
        try:
            # Send the reply
            response = client.create_tweet(
                text=tweet_data['reply_text'],
                in_reply_to_tweet_id=tweet_data['target_tweet']['tweet_id']
            )
            
            # Record successful send
            sent_record = {
                "tweet_id": tweet_data['target_tweet']['tweet_id'],
                "reply_id": response.data['id'],
                "sent_at": datetime.utcnow().isoformat(),
                "reply_text": tweet_data['reply_text'],
                "target_author": tweet_data['target_tweet']['author_id'],
                "keyword": tweet_data['keyword_triggered']
            }
            
            sent_tweets.append(sent_record)
            successfully_sent.append(tweet_data)
            
            print(f"   ✅ Sent successfully! Reply ID: {response.data['id']}")
            
        except tweepy.TweepyException as e:
            print(f"   ❌ Failed to send: {e}")
            failed_tweets.append(tweet_data)
    
    # Save updated sent tweets
    save_sent_tweets(sent_tweets)
    
    # Handle failed tweets (keep them in ready_to_send for retry)
    if failed_tweets:
        with open('/app/data/ready_to_send.json', 'w', encoding='utf-8') as f:
            json.dump(failed_tweets, f, indent=2, ensure_ascii=False)
        print(f"\n⚠️  {len(failed_tweets)} tweets failed and kept for retry")
    else:
        # Clear ready_to_send if all successful
        with open('/app/data/ready_to_send.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Successfully sent: {len(successfully_sent)}")
    print(f"   ❌ Failed: {len(failed_tweets)}")
    print(f"   📈 Total sent all-time: {len(sent_tweets)}")

if __name__ == "__main__":
    send_tweets()