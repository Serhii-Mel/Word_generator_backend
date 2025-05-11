def generate_script_prompt(title: str, transcript: str, word_count: int, forbidden_words: list[str]) -> str:
    prompt = f"""You are a professional scriptwriter with a talent for creating compelling, narration-friendly video scripts. Your task is to write a new script inspired by the tone, structure, and pacing of the following reference transcript.

**Project Details**
- **Title**: {title}
- **Target Word Count**: {word_count}
- **Forbidden Words**: {', '.join(forbidden_words) if forbidden_words else 'None'}

**Reference Transcript**
Use the transcript below as inspiration for structure, flow, and emotional impact. Do not copy it directly—use it as a creative foundation:
{transcript}

**Script Requirements**
Please generate an original video script that:
1. Mirrors the style and structure of the reference transcript
2. Captures and holds viewer attention throughout
3. Features smooth, natural transitions between ideas
4. Has a clear and engaging beginning, middle, and end
5. Is optimized for spoken delivery in a video format
6. Completely avoids using any of the forbidden words
7. Is approximately {word_count} words in total

**Output Format**
Return ONLY a valid JSON array of strings, where each string is a paragraph of the script.
Do not include any blank lines, empty strings, or extra whitespace between array elements.
Do not include any text before or after the JSON array.

**Example Format**
[
    "This is the opening paragraph that sets the stage...",
    "Here's a continuation that builds on the idea...",
    "This paragraph drives the story toward the conclusion...",
    "And here's a strong closing paragraph to wrap things up."
]

Ensure your response is properly formatted as a JSON array of strings only.

The structure of the script should be:
    Initial Setting & Disruption

    Establish peaceful everyday scene
    Introduce antagonist force
    First signs of conflict

    Hero Introduction

    Reveal protagonist's special skills/background
    Show composed character under pressure
    Hint at mysterious past

    First Victory

    Initial confrontation
    Demonstration of capability
    Temporary resolution

    Power Dynamic Shift

    Stronger opposition emerges
    Clear threats established
    Community impact revealed

    Integration & Connection

    Protagonist bonds with locals
    Key relationships form
    Deeper problems uncovered

    Investigation & Discovery

    Hidden conspiracy revealed
    Trusted ally betrays
    Critical evidence found

    Trap & Deception

    Seemingly perfect opportunity
    Hidden dangers emerge
    True scale of threat revealed

    Climactic Confrontation

    High-stakes showdown
    Life-threatening situation
    Critical moment of truth

    Victory & Justice

    Evil plot exposed
    Justice served
    Community saved

    New Chapter

    Hero finds belonging
    Future threat teased
    Story potential continues
"""
    prompt += (
        "\nReturn ONLY a valid JSON array of strings, where each string is a paragraph of the script."
        "\nDo not include any blank lines, empty strings, or extra whitespace between array elements."
        "\nDo not include any text before or after the JSON array."
        "\nExample: [\"Paragraph 1 text.\", \"Paragraph 2 text.\", ...]"
    )
    return prompt


def generate_paragraph_prompt(context: str, index: int) -> str:
    return f"""You are an expert script writer. Your task is to regenerate a specific paragraph in a video script.

ONLY return a single JSON object with one field: "content", which contains the regenerated paragraph as a string.

Do NOT include any introduction, explanation, or formatting before or after the JSON.
Do NOT wrap the JSON string inside another JSON.
Do NOT use markdown formatting (no ```json).

---

Current script context:
{context}

Please regenerate paragraph {index + 1} with the following requirements:
1. Create a completely new version that maintains the same key information but uses different wording and structure
2. Keep the same tone and style as the surrounding paragraphs
3. Ensure smooth transitions with the paragraphs before and after
4. Make the new version more engaging and impactful
5. Do NOT simply rephrase the existing paragraph - create something new while maintaining narrative consistency

Return format:
{{"content": "The new paragraph text goes here."}}

Make sure the JSON is strictly valid and not nested inside another object or surrounded by any commentary."""
