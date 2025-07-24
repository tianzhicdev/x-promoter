#!/usr/bin/env python3

import tweepy
import os
import sys
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
bearer_token = os.environ.get("X_BEARER_TOKEN")

# Check if all credentials are present
if not all([consumer_key, consumer_secret, access_token, access_token_secret, bearer_token]):
    print("❌ Missing credentials. Please check your .env file")
    sys.exit(1)

# Create Twitter API v2 client
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    bearer_token=bearer_token
)

def test_tweet():
    print("Sending test message to X/Twitter...")
    
    # Test message
    tweet_text = f"Test tweet from x-promoter at {datetime.now().isoformat()}"
    
    try:
        # Create tweet
        response = client.create_tweet(text=tweet_text)
        print("✅ Test tweet sent successfully!")
        print(f"Tweet ID: {response.data['id']}")
        print(f"Tweet text: {response.data['text']}")
    except tweepy.TweepyException as e:
        print("❌ Failed to send tweet")
        print(f"Error: {e}")
        sys.exit(1)

def promote():
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found")
        sys.exit(1)
    
    keywords = config.get('keywords', [])
    reply_message = config.get('reply_message', '')
    max_replies = config.get('max_replies_per_run', 5)
    
    print(f"🔍 Searching for tweets with keywords: {', '.join(keywords)}")
    
    replied_count = 0
    
    for keyword in keywords:
        if replied_count >= max_replies:
            break
            
        try:
            # Search for recent tweets with the keyword
            # Exclude retweets and replies for better targeting
            query = f"{keyword} -is:retweet -is:reply lang:en"
            tweets = client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=['author_id', 'created_at', 'id']
            )
            
            if not tweets.data:
                print(f"No tweets found for keyword: {keyword}")
                continue
            
            for tweet in tweets.data:
                if replied_count >= max_replies:
                    break
                
                try:
                    # Reply to the tweet
                    reply_text = f"@{tweet.author_id} {reply_message}"
                    response = client.create_tweet(
                        text=reply_text,
                        in_reply_to_tweet_id=tweet.id
                    )
                    
                    replied_count += 1
                    print(f"✅ Replied to tweet {tweet.id} about '{keyword}'")
                    print(f"   Reply: {reply_text}")
                    
                except tweepy.TweepyException as e:
                    print(f"❌ Failed to reply to tweet {tweet.id}: {e}")
                    continue
                    
        except tweepy.TweepyException as e:
            print(f"❌ Error searching for keyword '{keyword}': {e}")
            continue
    
    print(f"\n📊 Summary: Replied to {replied_count} tweets")

# Main execution
if len(sys.argv) > 1:
    if sys.argv[1] == "test":
        test_tweet()
    elif sys.argv[1] == "promote":
        promote()
    else:
        print(f"Unknown command: {sys.argv[1]}")
        print("Usage: python tweet.py [test|promote]")
        sys.exit(1)
else:
    print("Usage: python tweet.py [test|promote]")
    print("  test    - Send a test tweet")
    print("  promote - Search and reply to tweets based on config.json")