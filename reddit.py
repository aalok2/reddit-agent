import praw
import time
import logging
import sys
from datetime import datetime, timedelta
from fpdf import FPDF
import os
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)

class RedditAnalyzer:
import os

class RedditAnalyzer:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id="your_client_id",
            client_secret="your_client_secret",
            user_agent="your_user_agent",
            username="your_reddit_username",
            password="your_reddit_password"
        )
        
        genai.configure(api_key="your_gemini_api_key")
        self.model = genai.GenerativeModel("gemini-pro")


    def search_and_analyze(self, subreddit_name: str, search_query: str = None, time_limit: int = 365) -> str:
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            subreddit = self.reddit.subreddit(subreddit_name)
            scraped_data = []
            
            if search_query:
                posts = subreddit.search(query=search_query, sort='relevance', time_filter='all')
            else:
                posts = subreddit.new(limit=None)

            for post in posts:
                post_date = datetime.fromtimestamp(post.created_utc)
                post_data = {
                    "title": post.title,
                    "url": post.url,
                    "date": post_date,
                    "score": post.score,
                    "comments": [],
                    "content": post.selftext
                }
                
                try:
                    scraped_data.append(post_data)
                except Exception as e:
                    logging.error(f"Error processing post {post.title}: {e}")
                    continue

            scraped_data.sort(key=lambda x: x["date"], reverse=True)
            
            analysis = self._analyze_content(scraped_data)
            self._save_analysis(analysis, scraped_data)
            
            return "Analysis and PDF report generated successfully."

        except Exception as e:
            logging.error(f"Error in analysis: {e}")
            raise

    def _analyze_content(self, posts):
        analysis_prompt = self._prepare_analysis_prompt(posts)
        return self._get_gemini_analysis(analysis_prompt)

    def _prepare_analysis_prompt(self, posts):
        prompt = """Analyze these Reddit posts and provide:
        1. A brief overview of the main topics
        2. Key insights from the comments
        3. Notable trends or patterns
        4. Overall sentiment analysis
        
        Here are the posts and comments:
        """
        
        for post in posts:
            prompt += f"\nPOST: {post['title']}\n"
            prompt += f"DATE: {post['date']}\n"
            prompt += f"CONTENT: {post['content'][:500]}...\n"
            prompt += "COMMENTS:\n"
            for comment in post['comments']:
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
        filename = f"search_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Indian Stock Market Reddit Analysis\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Analysis Summary\n\n")
            f.write(analysis)
            f.write("\n\n")
            f.write("## Raw Data\n\n")
            for post in raw_data:
                f.write(f"### {post['title']}\n")
                f.write(f"[Link to post]({post['url']})\n\n")
                f.write("#### Top Comments:\n")
                for comment in post['comments']:
                    f.write(f"- {comment[:500]}...\n")
                f.write("\n---\n\n")

def main():
    try:
        analyzer = RedditAnalyzer()
        result = analyzer.search_and_analyze(
            subreddit_name="IndianStockMarket",
            search_query="transrail",
            time_limit=365
        )
        print(result)
            
    except Exception as e:
        logging.error(f"Main execution error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
