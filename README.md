# Reddit Market Analysis Bot

This project scrapes hot posts from the `r/IndianStockMarket` subreddit, analyzes their content using Google's Gemini AI, and generates a summarized report with key insights.

## 🚀 Features

- Scrapes Reddit posts and comments
- Uses Google's Gemini AI for content analysis
- Generates a markdown report with market insights
- Saves the analysis to a file

## 📌 Prerequisites

- Python 3.8+
- A Reddit Developer Account
- Google Gemini AI API Key

## 🛠 Installation

1. **Clone the Repository:**

   ```sh
   git clone https://github.com/your-username/reddit-market-analysis.git
   cd reddit-market-analysis
   ```

2. **Install Dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables:** Create a `.env` file in the root directory and add your credentials:

   ```ini
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=your_user_agent
   REDDIT_USERNAME=your_reddit_username
   REDDIT_PASSWORD=your_reddit_password
   GEMINI_API_KEY=your_gemini_api_key
   ```

## 🔄 Usage

Run the script to scrape Reddit posts and generate an analysis report:

```sh
python main.py
```

## 📂 Output

The analysis report is saved as a markdown file (`market_analysis_YYYYMMDD_HHMMSS.md`). It contains:

- **Hot topics being discussed**
- **Key insights from comments**
- **Notable stocks and trends**
- **Market sentiment indicators**

## 🛡 Security Notice

**DO NOT** hardcode your API keys in the script. Use environment variables instead.

## 🤝 Contributing

Pull requests are welcome! Please open an issue first to discuss any major changes.

## 📜 License

This project is licensed under the [MIT License](LICENSE).

