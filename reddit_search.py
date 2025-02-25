import praw
import time
import logging
import sys
import os
import requests
from datetime import datetime, timedelta
from fpdf import FPDF
from typing import Optional, Dict
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)


class TelegramSender:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}/"
        
    def send_message(self, message):
        """Send a text message via Telegram"""
        url = f"{self.base_url}sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message
        }
        response = requests.post(url, data=data)
        return response.json()
    
    def send_document(self, file_path, caption=None):
        """Send a document via Telegram"""
        url = f"{self.base_url}sendDocument"
        data = {
            "chat_id": self.chat_id
        }
        if caption:
            data["caption"] = caption
            
        with open(file_path, 'rb') as file:
            files = {'document': file}
            response = requests.post(url, data=data, files=files)
        
        return response.json()


class RedditAnalyzer:
    def __init__(self, telegram_token=None, telegram_chat_id=None):
        self.reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=os.environ.get("REDDIT_USER_AGENT", "user-agent"),
            username=os.environ.get("REDDIT_USERNAME"),
            password=os.environ.get("REDDIT_PASSWORD"),
        )

        # Initialize Gemini
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-pro")
        
        # Initialize Telegram sender if credentials are provided
        self.telegram = None
        if telegram_token and telegram_chat_id:
            self.telegram = TelegramSender(telegram_token, telegram_chat_id)

    def search_and_analyze(
        self, subreddits: list, keywords: list, time_limit: int = 365
    ) -> str:
        """
        Search Reddit content in multiple subreddits for multiple keywords,
        analyze with Gemini model, and generate PDF report.
        """
        try:
            # Initialize PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            scraped_data = []

            for subreddit_name in subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                print(f"Searching Reddit posts in r/{subreddit_name}...")

                for keyword in keywords:
                    print(f"Searching for keyword: {keyword}")
                    posts = subreddit.search(
                        query=keyword, sort="relevance", time_filter="day"
                    )

                    for post in posts:
                        post_date = datetime.fromtimestamp(post.created_utc)

                        post_data = {
                            "title": post.title,
                            "url": post.url,
                            "date": post_date,
                            "score": post.score,
                            "comments": [],
                            "content": post.selftext,
                        }

                        scraped_data.append(post_data)
                        print(f"Fetched post: {post.title}")

            # Check if scraped_data is empty
            if not scraped_data:
                message = "No Reddit posts found matching the search criteria today."
                logging.info(message)
                
                # Send message to Telegram if configured
                if self.telegram:
                    self.telegram.send_message(message)
                    
                return message

            # If we have data, proceed with analysis
            scraped_data.sort(key=lambda x: x["date"], reverse=True)
            analysis = self._analyze_content(scraped_data)
            report_file = self._save_analysis(analysis, scraped_data)
            
            # Send report via Telegram if configured
            if self.telegram:
                self._send_report_via_telegram(report_file)
                
            return f"Analysis and report generated successfully: {report_file}"

        except Exception as e:
            error_msg = f"Error in analysis: {e}"
            logging.error(error_msg)
            
            # Send error message to Telegram if configured
            if self.telegram:
                self.telegram.send_message(f"❌ Error running Reddit analysis: {str(e)}")
                
            raise

    def _analyze_content(self, posts):
        analysis_prompt = self._prepare_analysis_prompt(posts)
        return self._get_gemini_analysis(analysis_prompt)

    def _prepare_analysis_prompt(self, posts):
        prompt = """
        Analyze these Reddit posts and provide:
        1. A brief overview of the main topics
        2. Key insights from the comments
        3. Notable trends or patterns
        4. Overall sentiment analysis
        """
        for post in posts:
            prompt += f"\nPOST: {post['title']}\n"
            prompt += f"DATE: {post['date']}\n"
            prompt += f"CONTENT: {post['content'][:500]}...\n"
            prompt += "COMMENTS:\n"
            for comment in post["comments"]:
                prompt += f"- {comment[:200]}...\n"
            prompt += "---\n"
        return prompt

    def _get_gemini_analysis(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error during Gemini analysis: {e}")
            return "Error during analysis. Please check the logs."

    def _save_analysis(self, analysis, raw_data):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_analysis_{timestamp}.md"

        print(f"Saving analysis to {filename}...")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("# Reddit Analysis Report\n\n")
            f.write(
                f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            f.write("## Analysis Summary\n\n")
            f.write(analysis)
            f.write("\n\n")
            f.write("## Raw Data\n\n")
            for post in raw_data:
                f.write(f"### {post['title']}\n")
                f.write(f"[Link to post]({post['url']})\n\n")
                f.write("#### Top Comments:\n")
                for comment in post["comments"]:
                    f.write(f"- {comment[:500]}...\n")
                f.write("\n---\n\n")
                
        return filename
    
    def _send_report_via_telegram(self, file_path):
        """Send the generated report via Telegram and delete it afterward"""
        if not self.telegram:
            logging.warning("Telegram credentials not configured. Skipping send.")
            return False
            
        try:
            logging.info(f"Sending report via Telegram: {file_path} to chat ID: {self.telegram.chat_id}")
            
            # Send a message first
            message_result = self.telegram.send_message(f"📊 Reddit Analysis Report - {datetime.now().strftime('%Y-%m-%d')}")
            if not message_result.get("ok"):
                logging.error(f"Failed to send message: {message_result}")
                return False
            
            # Then send the document
            caption = "Daily Reddit market analysis report"
            result = self.telegram.send_document(file_path, caption)
            
            # Delete the file after sending
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Deleted report file: {file_path}")
            
            if result.get("ok"):
                logging.info("Report sent successfully via Telegram")
                return True
            else:
                logging.error(f"Failed to send report via Telegram: {result}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending report via Telegram: {e}")
            # Try to delete the file even if sending failed
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Deleted report file after error: {file_path}")
            return False


def main():
    print("Starting Reddit Analysis...")
    try:
        # Get Telegram credentials from environment variables
        telegram_token = os.environ.get("TELEGRAM_TOKEN")
        telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        # Initialize analyzer with Telegram credentials
        analyzer = RedditAnalyzer(telegram_token, telegram_chat_id)
        
        result = analyzer.search_and_analyze(
            subreddits=["IndianStockMarket", "StockMarket"],
            keywords=["KPI Green", "Gensol", "Olectra Greentech", "NDR Auto", "KP Energy", "Waaree Energies"],
            time_limit=365,
        )
        print(result)
    except Exception as e:
        print(f"Error in main execution: {e}")
        logging.error(f"Main execution error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
