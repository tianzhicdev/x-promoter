#!/bin/bash

case "$1" in
    build)
        echo "🔨 Building Docker container..."
        docker-compose build
        ;;
    
    up)
        echo "🚀 Starting X-Promoter bot..."
        docker-compose up -d
        echo "✅ Bot started. Check logs with: ./exec.sh logs"
        ;;
    
    down)
        echo "🛑 Stopping X-Promoter bot..."
        docker-compose down
        ;;
    
    search)
        echo "🔍 Running search manually..."
        docker-compose exec x-promoter python /app/src/search.py
        ;;
    
    prepare)
        echo "📝 Preparing tweets for review..."
        docker-compose exec x-promoter python /app/src/prepare.py
        echo "✅ Check data/ready_to_send.json for review"
        ;;
    
    send)
        echo "📤 Sending prepared tweets..."
        docker-compose exec x-promoter python /app/src/send.py
        ;;
    
    logs)
        echo "📋 Showing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    
    status)
        echo "📊 Bot Status:"
        echo ""
        echo "🔄 Keyword Rotation:"
        docker-compose exec x-promoter cat /app/config/keyword_state.json
        echo ""
        echo "📥 Ready to Send:"
        docker-compose exec x-promoter sh -c "cat /app/data/ready_to_send.json 2>/dev/null | python -m json.tool | grep -c 'id' || echo '0 tweets ready'"
        echo ""
        echo "📤 Sent Tweets:"
        docker-compose exec x-promoter sh -c "cat /app/data/sent_tweets.json 2>/dev/null | python -m json.tool | grep -c 'tweet_id' || echo '0 tweets sent'"
        ;;
    
    shell)
        echo "🐚 Opening shell in container..."
        docker-compose exec x-promoter /bin/bash
        ;;
    
    test)
        echo "🧪 Running old test tweet script..."
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi
        python tweet.py test
        ;;
    
    *)
        echo "X-Promoter Bot Commands:"
        echo ""
        echo "  ./exec.sh build    - Build Docker container"
        echo "  ./exec.sh up       - Start the bot with cron"
        echo "  ./exec.sh down     - Stop the bot"
        echo "  ./exec.sh search   - Run search manually"
        echo "  ./exec.sh prepare  - Prepare tweets for review"
        echo "  ./exec.sh send     - Send prepared tweets"
        echo "  ./exec.sh logs     - View bot logs"
        echo "  ./exec.sh status   - Check bot status"
        echo "  ./exec.sh shell    - Open shell in container"
        echo "  ./exec.sh test     - Send test tweet (old method)"
        echo ""
        echo "Workflow:"
        echo "1. ./exec.sh build   (first time only)"
        echo "2. ./exec.sh up      (starts auto-search every 15 min)"
        echo "3. ./exec.sh prepare (when you want to prepare replies)"
        echo "4. Review data/ready_to_send.json"
        echo "5. ./exec.sh send    (to send approved tweets)"
        ;;
esac