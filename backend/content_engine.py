"""
content_engine.py — AI Content Generation using Google Gemini
Generates carousel slide copy, captions, and hashtags for each news item
"""
import json
import re
from typing import List, Dict
from config import settings

# Import new Google Gen AI SDK
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


def _get_gemini_client():
    """Get a fresh Gemini client using current settings"""
    if not GEMINI_AVAILABLE:
        return None
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None
    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        print(f"[Gemini] Init error: {e}")
        return None


def _gemini_generate(prompt: str) -> str:
    """Call Gemini 2.0 Flash and return text response"""
    client = _get_gemini_client()
    if not client:
        return ""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini] Generation error: {e}")
        return ""


def _template_slides(article: Dict) -> Dict:
    """Fallback template-based content when Gemini is unavailable"""
    title = article.get("title", "AI News Update")[:80]
    summary = article.get("summary", "A major AI development has emerged.")[:300]
    source = article.get("source", "AI News")

    # Create smart bullets from the summary
    words = summary.split()
    chunk = len(words) // 3
    b1 = " ".join(words[:chunk])[:100] if words else "Major AI breakthrough announced."
    b2 = " ".join(words[chunk:chunk*2])[:100] if len(words) > chunk else "Industry leaders are paying attention."
    b3 = " ".join(words[chunk*2:])[:100] if len(words) > chunk*2 else "Early adopters will have an advantage."

    return {
        "slide1": {
            "headline": title.upper()[:70],
            "subtext": f"via {source}",
        },
        "slide2": {
            "header": "WHAT IS THIS?",
            "bullets": [b1 or "A major AI development.", b2 or "The industry is watching.", b3 or "This changes everything."]
        },
        "slide3": {
            "header": "WHY IT MATTERS",
            "bullets": [
                "Changes how creators and businesses use AI tools.",
                "Opens new possibilities for workflow automation.",
                "Could reshape the AI landscape significantly.",
            ]
        },
        "slide4": {
            "header": "HOW YOU CAN USE IT",
            "bullets": [
                "Integrate into your daily AI workflow immediately.",
                "Use it to boost content creation and productivity.",
                "Stay ahead by experimenting with it today.",
            ]
        },
        "slide5": {
            "header": "KEY TAKEAWAY",
            "summary": "AI is moving fast — stay updated to stay ahead.",
            "cta": "Would you use this AI tool? Comment below!",
            "engagement": "Save this for later!",
        }
    }


def generate_post_content(article: Dict, log_fn=None) -> Dict:
    """
    Generate full carousel content for one article.
    Returns dict with slide_texts, caption, hashtags.
    """
    def log(msg):
        print(f"[ContentEngine] {msg}")
        if log_fn:
            log_fn(msg)

    title = article.get("title", "")
    summary = article.get("summary", "")
    source = article.get("source", "")

    # Check if Gemini is configured
    if not settings.GEMINI_API_KEY:
        log("Gemini API key not set — using template content")
        slides = _template_slides(article)
        slides["caption"] = _generate_template_caption(article)
        slides["hashtags"] = _default_hashtags()
        return slides

    log(f"Generating content with Gemini 2.0 Flash for: {title[:60]}...")

    prompt = f"""You are a world-class AI social media content strategist.
Create a 5-slide Instagram carousel post about this AI news.

NEWS TITLE: {title}
NEWS SUMMARY: {summary[:400]}
SOURCE: {source}

Return ONLY a valid JSON object with this EXACT structure (no markdown, no extra text):
{{
  "slide1": {{
    "headline": "POWERFUL HOOK IN CAPS (max 10 words, viral)",
    "subtext": "One-line context sentence (max 12 words)"
  }},
  "slide2": {{
    "header": "WHAT IS THIS?",
    "bullets": ["clear explanation point 1", "clear explanation point 2", "clear explanation point 3"]
  }},
  "slide3": {{
    "header": "WHY IT MATTERS",
    "bullets": ["real-world impact point 1", "real-world impact point 2", "real-world impact point 3"]
  }},
  "slide4": {{
    "header": "HOW YOU CAN USE IT",
    "bullets": ["creator use case 1", "business use case 2", "productivity tip 3"]
  }},
  "slide5": {{
    "header": "KEY TAKEAWAY",
    "summary": "One powerful summary sentence (max 20 words)",
    "cta": "Engaging question with emoji?",
    "engagement": "Save or share CTA with emoji"
  }},
  "caption": "150-200 word Instagram caption. Hook first line. Use emojis. 3 value points. Strong CTA at end. No hashtags in body.",
  "hashtags": ["AI", "ArtificialIntelligence", "MachineLearning", "ChatGPT", "OpenAI", "GoogleAI", "Gemini", "AITools", "AINews", "TechNews", "FutureOfAI", "AIAutomation", "GenerativeAI", "AIAgent", "LLM", "AIStartup", "TechTrends", "Innovation", "AIUpdates", "DigitalTransformation", "AIRevolution", "AIForBusiness", "CreatorEconomy", "ProductivityTools", "AIProductivity"]
}}"""

    raw = _gemini_generate(prompt)

    if not raw:
        log("  Gemini returned empty response — using template fallback")
        slides = _template_slides(article)
        slides["caption"] = _generate_template_caption(article)
        slides["hashtags"] = _default_hashtags()
        return slides

    # Extract JSON from response (handle markdown code blocks)
    try:
        # Strip markdown code fences
        cleaned = re.sub(r'```json\s*', '', raw)
        cleaned = re.sub(r'```\s*', '', cleaned).strip()

        # Find JSON object boundaries
        start = cleaned.find('{')
        end = cleaned.rfind('}') + 1
        if start >= 0 and end > start:
            cleaned = cleaned[start:end]

        data = json.loads(cleaned)
        log("  Gemini content generated successfully")
        return data
    except (json.JSONDecodeError, ValueError) as e:
        log(f"  JSON parse failed ({e}) — using template fallback")
        slides = _template_slides(article)
        slides["caption"] = _generate_template_caption(article)
        slides["hashtags"] = _default_hashtags()
        return slides


def _generate_template_caption(article: Dict) -> str:
    title = article.get("title", "AI News")
    source = article.get("source", "AI News")
    return f"""Breaking AI Update You Need to Know!

{title}

This is one of the most important AI developments right now — and it could change the way you work, create, and grow.

Here's why this matters to you:

AI is evolving faster than ever before. The tools and platforms launching TODAY will define who leads tomorrow. Early movers always win.

What this means for you:
- Stay ahead of the curve with daily AI updates
- Apply these tools to your workflow NOW
- Share knowledge to grow your community

The question isn't IF AI will change your industry. It already is.

Save this post so you can reference it later.
Comment your thoughts below — would you use this?
Share with someone who needs to see this!

Source: {source}

Follow for daily AI updates delivered straight to your feed."""


def _default_hashtags() -> List[str]:
    return [
        "AI", "ArtificialIntelligence", "MachineLearning", "DeepLearning",
        "ChatGPT", "OpenAI", "GoogleAI", "Gemini", "AITools", "AINews",
        "TechNews", "FutureOfAI", "AIAutomation", "GenerativeAI", "AIAgent",
        "LLM", "AIStartup", "TechTrends", "Innovation", "AIUpdates",
        "DigitalTransformation", "AIRevolution", "AIForBusiness", "CreatorEconomy",
        "ProductivityTools", "AIProductivity", "TechCommunity", "AIContent",
        "FutureTech", "AIWorld"
    ]


def generate_all_posts(articles: List[Dict], log_fn=None) -> List[Dict]:
    """Generate content for all top 5 articles"""
    posts = []
    for i, article in enumerate(articles):
        if log_fn:
            log_fn(f"Generating content for article {i+1}/5: {article.get('title', '')[:60]}")
        content = generate_post_content(article, log_fn=log_fn)
        posts.append({
            "article": article,
            "content": content,
        })
    return posts
