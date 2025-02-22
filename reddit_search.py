
import praw
import time
import logging
import sys
from datetime import datetime, timedelta
from fpdf import FPDF
import os
from typing import Optional, Dict
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)

class RedditAnalyzer:
    def __init__(self):
        # Initialize Reddit API
        self.reddit = praw.Reddit(
            client_id="your_client_id",
            client_secret="your_client_secret",
            user_agent="your_user_agent",
            username="your_reddit_username",
            password="your_reddit_password"
        )
        
        # Initialize Gemini API with a dummy key
        genai.configure(api_key="your_gemini_api_key")
        self.model = genai.GenerativeModel("gemini-pro")

    def search_and_analyze(self, subreddit_name: str, search_query: str = None, time_limit: int = 365) -> str:
        """
        Search reddit content, analyze with Gemini model, and generate PDF report
        """
        try:
            # Initialize PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Scrape Reddit data
            subreddit = self.reddit.subreddit(subreddit_name)
            scraped_data = []
            # one_year_ago = datetime.now() - timedelta(days=time_limit)

            print(f"Searching Reddit posts in r/{subreddit_name}...")
            
            # Use search if query provided, otherwise get all posts
            if search_query:
                posts = subreddit.search(query = search_query, sort='relevance', time_filter='all')
                print(vars(posts))
            else:
                posts = subreddit.new(limit=None)

            for post in posts:
                print("Posts" , post.title ,  post.url )
                post_date = datetime.fromtimestamp(post.created_utc)
                # if post_date < one_year_ago:
                #     continue

                post_data = {
                    "title": post.title,
                    "url": post.url,
                    "date": post_date,
                    "score": post.score,
                    "comments": [],
                    "content": post.selftext
                }

                try:
                    # post.comments.replace_more(limit=0)
                    # comments = post.comments.list()[:5]  # Get top 5 comments
                    # post_data["comments"] = [comment.body for comment in comments]
                    scraped_data.append(post_data)
                    print("data" , scraped_data)
                    
                except Exception as e:
                    logging.error(f"Error processing post {post.title}: {e}")
                    continue

            # Sort posts by date (most recent first)
            scraped_data.sort(key=lambda x: x["date"], reverse=True)

            # Generate PDF
            # self._generate_pdf_report(scraped_data, search_query, subreddit_name)
            
            # Analyze content with Gemini
            analysis = self._analyze_content(scraped_data)
            self._save_analysis(analysis, scraped_data)
            
            return "Analysis and PDF report generated successfully."

        except Exception as e:
            logging.error(f"Error in analysis: {e}")
            raise

    def _generate_pdf_report(self, posts, search_query, subreddit_name):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Add title
        pdf.set_font("Arial", "B", 16)
        title = f"Reddit Analysis Report: r/{subreddit_name}"
        if search_query:
            title += f" - Search: {search_query}"
        pdf.cell(0, 10, title, ln=True, align='C')
        
        # Add generation date
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.ln(10)

        # Add posts
        for post in posts:
            # Post title
            pdf.set_font("Arial", "B", 14)
            pdf.multi_cell(0, 10, post["title"])
            
            # Post metadata
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 5, f"Date: {post['date'].strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            pdf.cell(0, 5, f"Score: {post['score']}", ln=True)
            pdf.cell(0, 5, f"URL: {post['url']}", ln=True)
            
            # Post content
            if post["content"]:
                pdf.set_font("Arial", "", 12)
                pdf.multi_cell(0, 10, post["content"][:500] + "..." if len(post["content"]) > 500 else post["content"])
            
            # Comments
            if post["comments"]:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Top Comments:", ln=True)
                pdf.set_font("Arial", "", 10)
                for comment in post["comments"]:
                    pdf.multi_cell(0, 5, "- " + (comment[:200] + "..." if len(comment) > 200 else comment))
            
            pdf.ln(10)
            pdf.cell(0, 0, "_" * 90, ln=True)
            pdf.ln(10)

        # Save PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_analysis_{subreddit_name}_{timestamp}.pdf"
        pdf.output(filename)

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
        
        print(f"Saving analysis to {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Indian Stock Market Reddit Analysis\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write the Gemini analysis
            f.write("## Analysis Summary\n\n")
            f.write(analysis)
            f.write("\n\n")
            
            # Write raw data in a structured format
            f.write("## Raw Data\n\n")
            for post in raw_data:
                f.write(f"### {post['title']}\n")
                f.write(f"[Link to post]({post['url']})\n\n")
                f.write("#### Top Comments:\n")
                for comment in post['comments']:
                    f.write(f"- {comment[:500]}...\n")  # Truncate long comments
                f.write("\n---\n\n")

def main():
    print("Starting Reddit Analysis...")
    
    try:
        analyzer = RedditAnalyzer()
        # Example usage with search query
        result = analyzer.search_and_analyze(
            subreddit_name="IndianStockMarket",
            search_query="transarail",  # Optional search query
            time_limit=365  # Days to look back
        )
        print(result)
            
    except Exception as e:
        print(f"Error in main execution: {e}")
        logging.error(f"Main execution error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
