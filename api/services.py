import anthropic
import json
from fastapi import HTTPException
from .prompts import generate_paragraph_prompt
from dotenv import load_dotenv
import os
import logging
import math
import random
import re

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key with better error handling
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    logger.error("ANTHROPIC_API_KEY environment variable is not set")
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

try:
    client = anthropic.Anthropic(api_key=api_key)
    logger.info("Successfully initialized Anthropic client")
except Exception as e:
    logger.error(f"Failed to initialize Anthropic client: {str(e)}")
    raise ValueError(f"Failed to initialize Anthropic client: {str(e)}")

# Model output limit (safe for Claude 3 Haiku)
MAX_WORDS_PER_REQUEST = 3500  # Adjust as needed for your model

# CTA templates for paraphrasing
CTA_INTRO = [
    "Before we jump back in, let us know where you're watching from, and if this story resonates, hit subscribe—tomorrow, something special awaits!",
    "Pause for a moment—comment your location and subscribe if this story moves you. Tomorrow, we've got a treat lined up!",
    "Share where you're tuning in from, and if this story speaks to you, subscribe for more—tomorrow brings something unique!"
]
CTA_1500 = [
    "Crafting and narrating this tale took time—if you're enjoying it, please subscribe. Your support means the world! Now, back to the story.",
    "If you're finding this story engaging, consider subscribing to our channel. It helps us a lot! Let's continue.",
    "Enjoying the journey so far? Subscribe to support us, and let's dive back in!"
]
CTA_6000 = [
    "Still with us? Don't forget to subscribe for more stories like this!",
    "If you're enjoying the video so far, hit that subscribe button!",
    "Liking the story? Make sure to subscribe so you never miss an update!"
]
CTA_END = [
    "Up next, two more standout stories await. If this one hit the mark, check them out! And don't forget to subscribe and ring the bell for updates!",
    "There are more great stories on your screen—click and enjoy! Subscribe and turn on notifications so you never miss out!",
    "Ready for more? Two more stories are waiting. Subscribe and hit the bell so you never miss a tale!"
]

def get_paraphrased_cta(cta_list):
    return random.choice(cta_list)

class AnthropicService:
    def __init__(self):
        self.model = "claude-3-5-sonnet-20240620"
        self.system_prompt = "You are an expert script writer who creates engaging, well-structured video scripts."
    

    async def continue_script(self, title: str, transcript: str, forbidden_words: list[str], structure_prompt: str, current_story: list, remaining_words: int):
        try:
            forbidden_words_str = ", ".join(forbidden_words) if isinstance(forbidden_words, list) else str(forbidden_words)
            context = "\n".join(current_story[-5:]) if len(current_story) >= 5 else "\n".join(current_story)
            part_word_count = min(MAX_WORDS_PER_REQUEST, remaining_words)
            prompt = f"""
You are a professional, versatile scriptwriter for YouTube videos. Continue the following story, making sure to add new content and not repeat or summarize previous parts. Do not end the story until the word count is met.

Title: {title}
Target Word Count for this part: {part_word_count}
Forbidden Words: {forbidden_words_str if forbidden_words else 'None'}
Inspirational Transcript: {transcript}

{f'Follow this structure: {structure_prompt}' if structure_prompt else ''}

Continue the story from the following context:
{context}

**Script Requirements:**
- Continue the story, do not repeat or summarize previous content.
- The script MUST be as close as possible to {part_word_count} words for this part. Do NOT generate fewer words. Do NOT exceed the word count by more than 5%.
- The script should be divided into paragraphs, each as a string in a JSON array.
- The script should be original, not copying the transcript, but using it for pacing, style, and structure.
- The script should be suitable for narration and keep viewers engaged.
- Do NOT include any text before or after the JSON array. Return ONLY a valid JSON array of strings, where each string is a paragraph.

**Example Output:**
["Paragraph 1...", "Paragraph 2...", ...]
"""
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            script_text = response.content[0].text.strip()
            try:
                paragraphs = json.loads(script_text)
                if not isinstance(paragraphs, list):
                    paragraphs = [script_text]
            except Exception as e:
                logging.warning(f"Failed to parse JSON: {e}. Returning plain text.")
                paragraphs = [script_text]
            updated_story = current_story + paragraphs
            total_words = len(" ".join(updated_story).split())
            completed = total_words >= (len(" ".join(current_story).split()) + remaining_words)
            next_context = "\n".join(updated_story[-5:])
            return {
                "paragraphs": updated_story,
                "total_words": total_words,
                "context": next_context,
                "remaining_words": max(0, (len(" ".join(current_story).split()) + remaining_words) - total_words),
                "completed": completed
            }
        except Exception as e:
            logging.error(f"Script continuation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Script continuation failed: {str(e)}")


    async def generate_script(self, title: str, word_count: int, forbidden_words: list[str], transcript: str = None, structure_prompt: str = ""):
        try:
            forbidden_words_str = ", ".join(forbidden_words) if isinstance(forbidden_words, list) else str(forbidden_words)
            num_parts = math.ceil(word_count / MAX_WORDS_PER_REQUEST)
            words_per_part = math.ceil(word_count / num_parts)
            all_paragraphs = []
            total_words = 0
            context = ""
            for part in range(num_parts):
                part_start = part * words_per_part
                part_end = min((part + 1) * words_per_part, word_count)
                part_word_count = part_end - part_start
                # Insert CTAs at the right points
                cta = ""
                if part == 0:
                    cta = get_paraphrased_cta(CTA_INTRO)
                elif part_start >= 1500 and part_start < 6000:
                    cta = get_paraphrased_cta(CTA_1500)
                elif part_start >= 6000:
                    cta = get_paraphrased_cta(CTA_6000)
                prompt = f"""
You are a professional, versatile scriptwriter for YouTube videos. Your task is to write a compelling, original script based on the new video title.

Title: {title}
Target Word Count for this part: {part_word_count}
Forbidden Words: {forbidden_words_str if forbidden_words else 'None'}
{f'Inspirational Transcript: {transcript}' if transcript else ''}

{f'Follow this structure: {structure_prompt}' if structure_prompt else ''}

Continue the story from the following context (if any):
{context}

{f'Include this call to action at a natural point in this part: "{cta}"' if cta else ''}

**Script Requirements:**
- The script MUST be as close as possible to {part_word_count} words for this part. Do NOT generate fewer words. Do NOT exceed the word count by more than 5%.
- The script should be divided into paragraphs, each as a string in a JSON array.
- The script should be original and creative, using the title as inspiration.
- The script should be suitable for narration and keep viewers engaged.
- Do NOT include any text before or after the JSON array. Return ONLY a valid JSON array of strings, where each string is a paragraph.

**Example Output:**
["Paragraph 1...", "Paragraph 2...", ...]
"""
                response = client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.7,
                    system=self.system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                script_text = response.content[0].text.strip()
                try:
                    paragraphs = json.loads(script_text)
                    if not isinstance(paragraphs, list):
                        paragraphs = [script_text]
                except Exception as e:
                    logging.warning(f"Failed to parse JSON: {e}. Returning plain text.")
                    paragraphs = [script_text]
                all_paragraphs.extend(paragraphs)
                context = "\n".join(all_paragraphs[-5:])  # Provide last 5 paragraphs as context for next part
                total_words = len(" ".join(all_paragraphs).split())
            # Add final CTA at the end
            all_paragraphs.append(get_paraphrased_cta(CTA_END))
            total_words = len(" ".join(all_paragraphs).split())
            completed = total_words >= word_count
            # Prepare context for next chunk (last 5 paragraphs)
            next_context = "\n".join(all_paragraphs[-5:])
            return {
                "paragraphs": all_paragraphs,
                "total_words": total_words,
                "context": next_context,
                "remaining_words": max(0, word_count - total_words),
                "completed": completed
            }
        except Exception as e:
            logging.error(f"Script generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

    def regenerate_segment(
        self,
        context_before: str,
        context_after: str,
        segment_word_count: int,
        title: str,
        inspirational_transcript: str = None,
        forbidden_words: list[str] = None,
        structure_prompt: str = ""
    ) -> dict:
        """Regenerate a segment of the script."""
        prompt = f"""You are a professional scriptwriter. Your task is to regenerate a segment of a video script.

Current script context before the segment:
{context_before}

Current script context after the segment:
{context_after}

Please generate a new segment that:
1. Maintains narrative consistency with the surrounding context
2. Has approximately {segment_word_count} words
3. Follows the same style and tone as the rest of the script
4. Creates smooth transitions with the paragraphs before and after
5. Is optimized for spoken delivery

{f'Inspirational Transcript: {inspirational_transcript}' if inspirational_transcript else ''}

Return ONLY a valid JSON object with two fields:
1. "content": The regenerated segment text
2. "wordCount": The number of words in the segment

Example format:
{{"content": "The segment text goes here.", "wordCount": 500}}

Make sure the JSON is strictly valid and not nested inside another object or surrounded by any commentary."""

        response = client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        try:
            # Get the response text
            response_text = response.content[0].text.strip()
            
            # Extract content and word count using regex
            content_match = re.search(r'"content":\s*"([^"]*)"', response_text)
            word_count_match = re.search(r'"wordCount":\s*(\d+)', response_text)
            
            if content_match and word_count_match:
                content = content_match.group(1)
                word_count = int(word_count_match.group(1))
                
                # Unescape any escaped characters in the content
                content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                
                return {
                    "content": content,
                    "wordCount": word_count
                }
            else:
                # If we can't extract the fields, use the whole text as content
                return {
                    "content": response_text,
                    "wordCount": len(response_text.split())
                }
                
        except Exception as e:
            logging.error(f"Failed to process model response: {str(e)}")
            raise ValueError(f"Failed to process model response: {str(e)}")