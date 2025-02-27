import os
import logging
from typing import Dict, Optional, Tuple

from bs4 import BeautifulSoup
import openai
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

#Load keys
load_dotenv()

class Summarizer:
    """Service to summarize HTML content using OpenAI API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the summarizer with an OpenAI API key."""
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)

        if not self.api_key:
            raise ImproperlyConfigured("OpenAI API key is required. Set it as OPENAI_API_KEY in Django settings or environment variable.")

        openai.api_key = self.api_key

    def clean_html(self, html_content: str) -> str:
        """Extract and clean text from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()

        # Get text and clean it
        text = soup.get_text()

        # Remove extra whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def estimate_token_count(self, text: str) -> int:
        """Estimate the number of tokens in the given text."""
        # A rough estimate: 1 token ~= 4 characters for English text
        return len(text) // 4

    def chunk_text(self, text: str, max_tokens: int = 4000) -> list:
        """Split text into chunks of approximately max_tokens."""
        estimated_total_tokens = self.estimate_token_count(text)
        if estimated_total_tokens <= max_tokens:
            return [text]

        # Split by paragraphs
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = []
        current_token_count = 0

        for paragraph in paragraphs:
            paragraph_token_count = self.estimate_token_count(paragraph)

            if current_token_count + paragraph_token_count > max_tokens:
                # Save current chunk and start a new one
                chunks.append('\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_token_count = paragraph_token_count
            else:
                current_chunk.append(paragraph)
                current_token_count += paragraph_token_count

        # Add the last chunk if not empty
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def summarize_text(self, text: str, max_length: int = 1000) -> Tuple[str, int]:
        """
        Summarize text using OpenAI API.

        Args:
            text: The text to summarize
            max_length: Maximum length of the summary in characters

        Returns:
            Tuple of (summary, token_count)
        """
        try:
            chunks = self.chunk_text(text)
            summaries = []
            total_tokens = 0

            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1} of {len(chunks)}")

                prompt = f"""
                Summarize the following text in a clear, concise manner. 
                Focus on the main ideas and key information.

                {chunk}
                """

                response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a skilled summarizer that extracts key information from text."},
                            {"role": "user", "content": prompt}
                            ],
                        max_tokens=1000,
                        temperature=0.3
                        )

                chunk_summary = response.choices[0].message.content.strip()
                chunk_tokens = response.usage.total_tokens
                total_tokens += chunk_tokens
                summaries.append(chunk_summary)

                logger.debug(f"Chunk {i+1} summary: {chunk_summary[:100]}...")
                logger.debug(f"Tokens used: {chunk_tokens}")

            # Combine individual summaries
            if len(summaries) > 1:
                combined_summary = "\n\n".join(summaries)

                # If we have multiple chunks, create a meta-summary
                if len(combined_summary) > max_length:
                    logger.info("Creating meta-summary from multiple chunk summaries")

                    meta_prompt = f"""
                    Create a cohesive, unified summary from these section summaries:

                        {combined_summary}
                    """

                    meta_response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a skilled editor that creates cohesive summaries from multiple text sections."},
                                {"role": "user", "content": meta_prompt}
                                ],
                            max_tokens=1000,
                            temperature=0.3
                            )

                    final_summary = meta_response.choices[0].message.content.strip()
                    total_tokens += meta_response.usage.total_tokens
                else:
                    final_summary = combined_summary
            else:
                final_summary = summaries[0]

            return final_summary, total_tokens

        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
            raise

    def summarize_html(self, html_content: str, max_length: int = 1000) -> Dict:
        """
        Summarize HTML content.

        Args:
            html_content: HTML content to summarize
            max_length: Maximum length of the summary in characters

        Returns:
            Dict with summary and token count
        """
        clean_text = self.clean_html(html_content)
        summary, token_count = self.summarize_text(clean_text, max_length)

        return {
                "summary": summary,
                "token_count": token_count
                }
