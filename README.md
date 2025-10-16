# Wardrobe Consulting Telegram Bot 🌸

A Telegram bot that helps women choose outfits based on weather, mood, psychological profile, and wardrobe inventory.

## Features

- **Psychological Profile Survey**: One-time questionnaire to understand personal style preferences
- **Wardrobe Inventory**: Track clothing items by categories (basics, tops, bottoms, shoes, outerwear, accessories)
- **Weather Integration**: Real-time weather data from Open-Meteo API
- **Smart Recommendations**: AI-powered outfit suggestions based on:
  - Current weather conditions
  - Destination (work, date, party, etc.)
  - Mood and psychological profile
  - Available wardrobe items

## Setup for Render.com (Docker)

### 1. Create Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Save the `BOT_TOKEN` you receive

### 2. Deploy to Render with Docker
1. Connect your GitHub repository to Render
2. Create a new "Web Service"
3. Choose **Docker** as the environment
4. Render will automatically detect the Dockerfile
5. No build/start commands needed - Docker handles everything

### 3. Set Environment Variables
In your Render dashboard, go to Environment and add:

```
BOT_TOKEN=your_bot_token_from_botfather
WEBHOOK_URL=https://your-app-name.onrender.com/webhook
```

Replace `your-app-name` with your actual Render app name.

### 4. Docker Configuration
The project includes:
- **Dockerfile**: Optimized for production with security best practices
- **.dockerignore**: Excludes unnecessary files from Docker build
- **Health checks**: Built-in container health monitoring
- **Non-root user**: Runs securely without root privileges

### 4. Test the Bot
1. Find your bot on Telegram using the username you created
2. Send `/start` to begin
3. Follow the setup flow:
   - Complete psychological profile survey
   - Add items to your wardrobe
   - Get outfit recommendations!

## Local Development

### Option 1: Direct Python
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   ```bash
   export BOT_TOKEN="your_bot_token"
   export WEBHOOK_URL="https://your-ngrok-url.ngrok.io/webhook"
   ```
4. Run: `python main.py`

### Option 2: Docker (Recommended)
1. Clone the repository
2. Build Docker image:
   ```bash
   docker build -t wardrobe-bot .
   ```
3. Run container:
   ```bash
   docker run -p 10000:10000 \
     -e BOT_TOKEN="your_bot_token" \
     -e WEBHOOK_URL="https://your-ngrok-url.ngrok.io/webhook" \
     wardrobe-bot
   ```
4. Test: Visit `http://localhost:10000` - should show "Wardrobe Bot is running! 🌸"

## Bot Commands

- `/start` - Begin or restart the bot
- **🧠 Пройти опрос профиля** - Complete psychological profile
- **👗 Заполнить гардероб** - Add items to wardrobe
- **🌤️ Что сегодня надеть?** - Get outfit recommendation

## How It Works

1. **Profile Setup**: Users complete a 3-question psychological survey
2. **Wardrobe Building**: Users add clothing items by category
3. **Daily Recommendations**: 
   - Enter city for weather data
   - Select destination (work, date, party, etc.)
   - Choose mood
   - Receive personalized outfit suggestions

## API Dependencies

- **Open-Meteo**: Free weather API for current conditions
- **Telegram Bot API**: For bot functionality
- **SQLite**: Local database for user data

## Database Schema

- `users` - User information
- `profiles` - Psychological profiles
- `wardrobe_items` - Clothing inventory
- `sessions` - Conversation state

## Free Tier Optimizations

- Minimal dependencies (Flask + requests only)
- Lightweight Docker image
- Efficient database queries
- No external AI services (rule-based recommendations)

## Troubleshooting

### Bot not responding
- Check that `BOT_TOKEN` is set correctly
- Verify `WEBHOOK_URL` includes your full Render URL + `/webhook`
- Check Render logs for errors

### Weather not loading
- Ensure city name is spelled correctly
- Check internet connectivity
- Open-Meteo API is free but has rate limits

### Database issues
- Database is automatically created on first run
- Data persists between deployments on Render
- No manual setup required

## Support

If you encounter issues:
1. Check Render deployment logs
2. Verify environment variables are set
3. Test bot with `/start` command
4. Check that webhook URL is accessible

---

Made with ❤️ for helping women feel confident in their style choices!
