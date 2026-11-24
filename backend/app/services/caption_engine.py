import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("yt_shorts.captions")

def format_ass_timestamp(seconds: float) -> str:
    """Formats seconds into ASS timestamp H:MM:SS.cs."""
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

class CaptionEngine:
    """
    Professional human-grade subtitle generator replicating Premiere Pro / After Effects typography:
    - Balanced 2-3 word visual cadence positioned in lower-third safe zone (MarginV: 220)
    - Clean typography: crisp dark outline, soft drop shadow, no cartoonish distortion
    - Elegant active-word color accent with subtle micro-scale (104%)
    - Opening Hook Title Card with smooth 250ms fade-in and 300ms fade-out (0.0s to 2.8s only),
      leaving the rest of the video 100% free of top-screen obstruction
    """
    STYLES = {
        "editorial_gold": {
            "Fontname": "Arial",
            "Fontsize": "52",
            "PrimaryColour": "&H00FFFFFF&",    # Crisp pure white
            "SecondaryColour": "&H0020D4F0&",  # Warm gold accent highlight (BGR)
            "OutlineColour": "&H00141414&",    # Clean dark charcoal outline
            "BackColour": "&H60000000&",       # Soft translucent shadow
            "Bold": "-1",
            "Outline": "2.5",
            "Shadow": "1.5",
            "Alignment": "2",                  # Bottom center
            "MarginV": "220"
        },
        "modern_minimal": {
            "Fontname": "Arial",
            "Fontsize": "50",
            "PrimaryColour": "&H00FFFFFF&",
            "SecondaryColour": "&H00FFFF00&",  # Modern cyan accent
            "OutlineColour": "&H00141414&",
            "BackColour": "&H60000000&",
            "Bold": "-1",
            "Outline": "2.5",
            "Shadow": "1.0",
            "Alignment": "2",
            "MarginV": "220"
        },
        "bold_yellow": {
            "Fontname": "Arial",
            "Fontsize": "52",
            "PrimaryColour": "&H00FFFFFF&",
            "SecondaryColour": "&H0000FFFF&",  # Clean electric yellow
            "OutlineColour": "&H00101010&",
            "BackColour": "&H70000000&",
            "Bold": "-1",
            "Outline": "2.8",
            "Shadow": "1.5",
            "Alignment": "2",
            "MarginV": "220"
        },
        "cinematic_white": {
            "Fontname": "Trebuchet MS",
            "Fontsize": "48",
            "PrimaryColour": "&H00F5F5F5&",
            "SecondaryColour": "&H00FFFFFF&",  # Pure white highlight
            "OutlineColour": "&H000A0A0A&",
            "BackColour": "&H80000000&",
            "Bold": "-1",
            "Outline": "2.0",
            "Shadow": "2.0",
            "Alignment": "2",
            "MarginV": "210"
        }
    }

    def generate_ass_subtitles(
        self,
        words: List[Dict[str, Any]],
        start_time: float,
        end_time: float,
        output_ass_path: Path,
        style_name: str = "editorial_gold",
        words_per_line: int = 3,
        hook_title: Optional[str] = None,
        enable_emojis: bool = False
    ) -> Path:
        """
        Generates an Advanced SubStation Alpha (.ass) subtitle file.
        Times are normalized relative to clip start (0.0s).
        """
        style = self.STYLES.get(style_name, self.STYLES["editorial_gold"])
        active_color = style["SecondaryColour"]
        duration = max(1.0, end_time - start_time)

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['Fontname']},{style['Fontsize']},{style['PrimaryColour']},{style['SecondaryColour']},{style['OutlineColour']},{style['BackColour']},{style['Bold']},0,0,0,100,100,0,0,1,{style['Outline']},{style['Shadow']},{style['Alignment']},50,50,{style['MarginV']},1
Style: HookCard,Arial,44,&H00FFFFFF&,&H00FFFFFF&,&H00141414&,&H80000000&,-1,0,0,0,100,100,0,0,1,3.0,1.5,8,50,50,160,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        dialogue_lines = []

        # 1. Opening Hook Title Card:
        # Appears at 0.0s, fades in over 250ms, stays until 2.8s, and fades out over 300ms.
        # NEVER persists through the whole video to avoid blocking content or looking like spam.
        if hook_title and hook_title.strip():
            clean_title = hook_title.strip().upper()
            if len(clean_title) > 42:
                clean_title = clean_title[:39] + "..."
            
            card_end_time = min(2.80, duration)
            t_start = format_ass_timestamp(0.0)
            t_end = format_ass_timestamp(card_end_time)
            dialogue_lines.append(
                f"Dialogue: 1,{t_start},{t_end},HookCard,,0,0,0,,{{\\fad(250,300)\\an8\\pos(540,160)\\bord3\\shad1.5\\c&H00FFFFFF&\\3c&H00141414&\\fs44\\b1}}{clean_title}"
            )

        # 2. Filter words within clip interval
        clip_words = [
            w for w in words
            if w["start"] >= (start_time - 0.2) and w["end"] <= (end_time + 0.2)
        ]

        if clip_words:
            # Chunk words into natural visual groups (2-3 words per line for high legibility)
            chunks = []
            for i in range(0, len(clip_words), words_per_line):
                chunks.append(clip_words[i:i + words_per_line])

            for chunk in chunks:
                chunk_start = max(0.0, chunk[0]["start"] - start_time)
                chunk_end = max(chunk_start + 0.3, chunk[-1]["end"] - start_time)

                clean_color = active_color.rstrip("&") + "&"
                # For each word in the chunk, create a timed highlight line with subtle emphasis
                for active_idx, target_word in enumerate(chunk):
                    w_start = max(0.0, target_word["start"] - start_time)
                    w_end = max(w_start + 0.2, target_word["end"] - start_time)

                    text_parts = []
                    for idx, w in enumerate(chunk):
                        word_str = w["word"].upper()
                        if idx == active_idx:
                            # Subtle micro-scale (104%) with active accent color
                            text_parts.append(f"{{\\fscx104\\fscy104\\c{clean_color}}}{word_str}{{\\r}}")
                        else:
                            text_parts.append(word_str)

                    line_text = " ".join(text_parts)
                    t_w_start = format_ass_timestamp(w_start)
                    t_w_end = format_ass_timestamp(w_end)
                    dialogue_lines.append(f"Dialogue: 0,{t_w_start},{t_w_end},Default,,0,0,0,,{line_text}")

        content = header + "\n".join(dialogue_lines) + "\n"
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Generated professional ASS subtitles at {output_ass_path} ({len(dialogue_lines)} events)")
        return output_ass_path

caption_engine = CaptionEngine()
