#!/usr/bin/env python3

import tweepy
import os
import json
from datetime import datetime, timedelta
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
    exit(1)

# Create Twitter API v2 client
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    bearer_token=bearer_token
)

def load_keywords():
    """Load keywords and current index"""
    with open('/app/config/keywords.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_keyword_state(index):
    """Save current keyword index"""
    state = {
        "current_index": index,
        "last_used": datetime.utcnow().isoformat()
    }
    with open('/app/config/keyword_state.json', 'w') as f:
        json.dump(state, f, indent=2)

def load_search_results():
    """Load existing search results"""
    try:
        with open('/app/data/search_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_search_results(results):
    """Save search results"""
    with open('/app/data/search_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def search_tweets():
    """Main search function"""
    # Load keywords
    keywords_data = load_keywords()
    keywords = keywords_data['keywords']
    current_index = keywords_data['current_index']
    
    # Get current keyword
    keyword = keywords[current_index]
    print(f"🔍 Searching for: {keyword}")
    
    # Calculate time range (last 24 hours)
    # End time must be at least 10 seconds before now
    end_time = datetime.utcnow() - timedelta(seconds=30)
    start_time = end_time - timedelta(hours=24)
    
    try:
        # Search tweets
        tweets = client.search_recent_tweets(
            query=f"{keyword} -is:retweet",
            max_results=100,
            tweet_fields=['author_id', 'created_at', 'public_metrics'],
            start_time=start_time.isoformat() + "Z",
            end_time=end_time.isoformat() + "Z"
        )
        
        if not tweets.data:
            print(f"No tweets found for keyword: {keyword}")
            results = []
        else:
            # Process results
            results = []
            for tweet in tweets.data:
                result = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "keyword": keyword,
                    "tweet_id": tweet.id,
                    "author_id": tweet.author_id,
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat() if hasattr(tweet.created_at, 'isoformat') else str(tweet.created_at),
                    "likes": tweet.public_metrics.get('like_count', 0) if tweet.public_metrics else 0,
                    "retweets": tweet.public_metrics.get('retweet_count', 0) if tweet.public_metrics else 0,
                    "replies": tweet.public_metrics.get('reply_count', 0) if tweet.public_metrics else 0
                }
                results.append(result)
            
            print(f"✅ Found {len(results)} tweets")
        
        # Load existing results and append new ones
        all_results = load_search_results()
        all_results.extend(results)
        
        # Save updated results
        save_search_results(all_results)
        
        # Update keyword index
        next_index = (current_index + 1) % len(keywords)
        save_keyword_state(next_index)
        
        print(f"📊 Total results in database: {len(all_results)}")
        print(f"🔄 Next keyword will be: {keywords[next_index]}")
        
    except tweepy.TweepyException as e:
        print(f"❌ Error searching tweets: {e}")
        # Still update index even on error
        next_index = (current_index + 1) % len(keywords)
        save_keyword_state(next_index)

if __name__ == "__main__":
    search_tweets()