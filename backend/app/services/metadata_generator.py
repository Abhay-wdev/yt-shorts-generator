import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger("yt_shorts.metadata")

class MetadataGeneratorService:
    def generate_metadata(self, segment_text: str, source_title: str) -> Dict[str, Any]:
        """
        Generates 5 viral title candidates, SEO description, hashtags, and keywords
        derived from segment transcript and original title.
        """
        clean_text = " ".join(segment_text.split())
        words = clean_text.split()
        first_sentence = clean_text.split(".")[0] if "." in clean_text else clean_text[:60]

        # Extract topical keywords
        stop_words = {"this", "that", "with", "from", "have", "were", "what", "when", "your", "they", "will"}
        tokens = [w.lower().strip(".,!?:;\"'") for w in words if len(w) > 4 and w.lower() not in stop_words]
        top_keywords = list(dict.fromkeys(tokens))[:8]

        kw_phrase = " ".join(top_keywords[:3]).title() if top_keywords else "Viral Moment"

        # Generate 5 Distinct Title Styles
        title_options = [
            f"The Truth About {kw_phrase}! 😱",
            f"Why Nobody Talks About {kw_phrase}...",
            f"Wait Until You See What Happens Next! 🔥",
            f"Did You Know This About {kw_phrase}?",
            f"The #1 Secret to {kw_phrase} Exposed!"
        ]

        # Extract hashtags
        hashtags = ["#shorts", "#viral", "#trending", "#story", "#learning"]
        for kw in top_keywords[:4]:
            tag = f"#{kw.capitalize()}"
            if tag not in hashtags:
                hashtags.append(tag)

        # Build description
        description = (
            f"{clean_text[:180]}...\n\n"
            f"👉 Subscribe for more insightful clips!\n\n"
            f"{' '.join(hashtags)}\n\n"
            f"Source: {source_title}"
        )

        return {
            "title_options": title_options,
            "recommended_title": title_options[0],
            "description": description,
            "hashtags": hashtags,
            "keywords": top_keywords,
            "suggested_category": "Entertainment",
            "suggested_publishing_time": "18:00:00"  # Peak Shorts consumption window
        }

metadata_generator = MetadataGeneratorService()
