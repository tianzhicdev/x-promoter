#!/usr/bin/env python3

import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API")

def load_search_results():
    """Load search results"""
    try:
        with open('/app/data/search_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No search results found. Run search first.")
        return []

def load_sent_tweets():
    """Load already sent tweets"""
    try:
        with open('/app/data/sent_tweets.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_promotion_content():
    """Load abitchaotic.md content"""
    with open('/app/content/abitchaotic.md', 'r', encoding='utf-8') as f:
        return f.read()

def calculate_engagement_score(tweet):
    """Calculate engagement score for ranking tweets"""
    likes = tweet.get('likes', 0)
    retweets = tweet.get('retweets', 0)
    replies = tweet.get('replies', 0)
    
    # Weight likes more than retweets, and retweets more than replies
    return (likes * 3) + (retweets * 2) + replies

def filter_and_rank_tweets(tweets, sent_tweet_ids):
    """Filter out sent tweets and rank by engagement"""
    # Filter out already sent tweets
    filtered = [t for t in tweets if t['tweet_id'] not in sent_tweet_ids]
    
    # Filter tweets from last 48 hours for better relevance
    cutoff_time = datetime.utcnow() - timedelta(hours=48)
    recent_tweets = []
    for tweet in filtered:
        try:
            tweet_time = datetime.fromisoformat(tweet['created_at'].replace('Z', ''))
            if tweet_time > cutoff_time:
                recent_tweets.append(tweet)
        except:
            continue
    
    # Sort by engagement score
    recent_tweets.sort(key=calculate_engagement_score, reverse=True)
    
    return recent_tweets

def generate_reply(tweet, promotion_content):
    """Use OpenAI to generate a contextual reply"""
    prompt = f"""You are a helpful social media assistant promoting abitchaotic.com, a platform for selling digital products with crypto payments.

Platform Info:
{promotion_content}

Target Tweet:
Author: @{tweet['author_id']}
Text: {tweet['text']}
Keyword that matched: {tweet['keyword']}

Task: Create a natural, helpful reply that:
1. Addresses their specific need or comment
2. Introduces abitchaotic.com as a solution
3. Mentions ONE key benefit relevant to their tweet
4. Sounds conversational, not promotional
5. Is under 280 characters
6. Includes @{tweet['author_id']} at the start

Do not use hashtags. Do not sound like a bot. Be helpful and genuine.

Reply:"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes natural Twitter replies."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return None

def prepare_tweets(limit=5):
    """Main function to prepare tweets for sending"""
    # Load data
    search_results = load_search_results()
    sent_tweets = load_sent_tweets()
    promotion_content = load_promotion_content()
    
    if not search_results:
        print("❌ No search results available")
        return
    
    # Get sent tweet IDs
    sent_tweet_ids = {t['tweet_id'] for t in sent_tweets}
    
    # Filter and rank tweets
    candidates = filter_and_rank_tweets(search_results, sent_tweet_ids)
    
    if not candidates:
        print("❌ No new tweets to reply to")
        return
    
    print(f"📊 Found {len(candidates)} candidate tweets")
    
    # Prepare replies
    ready_to_send = []
    
    for i, tweet in enumerate(candidates[:limit]):
        print(f"\n🔄 Processing tweet {i+1}/{min(limit, len(candidates))}")
        print(f"   Tweet: {tweet['text'][:100]}...")
        print(f"   Engagement: {calculate_engagement_score(tweet)} (Likes: {tweet['likes']}, RTs: {tweet['retweets']})")
        
        # Generate reply
        reply_text = generate_reply(tweet, promotion_content)
        
        if reply_text:
            prepared_tweet = {
                "id": f"{tweet['tweet_id']}_reply",
                "prepared_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                "target_tweet": tweet,
                "reply_text": reply_text,
                "keyword_triggered": tweet['keyword'],
                "status": "pending"
            }
            
            ready_to_send.append(prepared_tweet)
            print(f"   ✅ Reply prepared: {reply_text[:100]}...")
        else:
            print(f"   ❌ Failed to generate reply")
    
    # Save prepared tweets
    if ready_to_send:
        with open('/app/data/ready_to_send.json', 'w', encoding='utf-8') as f:
            json.dump(ready_to_send, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Prepared {len(ready_to_send)} tweets for review")
        print("📝 Review them in data/ready_to_send.json")
    else:
        print("\n❌ No tweets were prepared")

if __name__ == "__main__":
    prepare_tweets()