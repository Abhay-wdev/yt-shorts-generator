import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("yt_shorts.reframer")

class SmartReframingService:
    def calculate_crop_window(
        self,
        face_coordinates: List[Dict[str, Any]],
        start_time: float,
        end_time: float,
        source_width: int = 1920,
        source_height: int = 1080
    ) -> Tuple[float, str]:
        """
        Determines the optimal horizontal crop center for 9:16 aspect ratio:
        - Works universally on 16:9 widescreen, 4:3, square, and vertical inputs.
        - Uses min(iw, ih*9/16) and min(ih, iw*16/9) to ensure valid dimensions.
        - Centers horizontally around the detected face / motion x_ratio.
        - Safely clamps within frame boundaries [0, iw - out_w].
        """
        clip_faces = [
            fc for fc in face_coordinates
            if start_time <= fc["time"] <= end_time
        ]

        if clip_faces:
            ratios = [fc["x_ratio"] for fc in clip_faces]
            ratios.sort()
            median_ratio = ratios[len(ratios) // 2]
            clamped_ratio = max(0.25, min(0.75, median_ratio))
        else:
            clamped_ratio = 0.5  # Safe center fallback

        # Return crop expression properly formatted with quoted dimensions for FFmpeg
        crop_expr = (
            f"w='min(iw,ih*9/16)':"
            f"h='min(ih,iw*16/9)':"
            f"x='max(0,min(iw-out_w,(iw*{clamped_ratio:.3f})-(out_w/2)))':"
            f"y='(ih-out_h)/2'"
        )

        return clamped_ratio, crop_expr

    def build_layout_filter_complex(
        self,
        layout_mode: str,
        duration: float,
        face_x_ratio: float = 0.5,
        subtitle_filename: str = None,
        apply_unsharp: bool = True
    ) -> str:
        """
        Builds professional human-grade editorial filter graphs replicating Adobe Premiere Pro / After Effects:
        - 'screen_focus' / 'screen_demo': Optimizes horizontal scale so charts/code/UI elements are sharp and legible on mobile, with a dark atmospheric backdrop and subtle frame border.
        - 'portrait_focus' / 'talking_head': Rule-of-thirds eye-line framing (y=0.35) with smooth subject centering.
        - 'split_screen': Balanced dual stack.
        - Minimalist 3px editorial progress line (crisp, unobtrusive, modern).
        - High-frequency unsharp mask for razor-sharp edge contrast without pixel distortion.
        """
        sub_tag = f",ass={subtitle_filename}" if subtitle_filename else ""
        dur = max(1.0, duration)
        
        # Professional 3px minimalist progress line (no crude thick yellow bars)
        p_bar = f",drawbox=x=0:y=1916:w='1080*(t/{dur:.2f})':h=3:color=white@0.45:t=fill"
        sharp_tag = ",unsharp=3:3:0.35:3:3:0.0" if apply_unsharp else ""

        mode = (layout_mode or "screen_focus").lower().strip()

        if mode in ("screen_focus", "ai_blur_canvas", "blur_canvas", "trading", "screen_demo"):
            # Professional Editorial Screen Layout:
            # - Deep atmospheric background with gentle blur (26px) and rich contrast
            # - Foreground scaled with optimal mobile readability (1080:-2 for even dimensions)
            # - Exact 1px subtle frame border with soft alpha
            return (
                f"[0:v]split=2[bg_raw][fg_raw];"
                f"[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=26:3,eq=brightness=-0.35:contrast=1.12[bg];"
                f"[fg_raw]scale=1080:-2{sharp_tag},drawbox=x=0:y=0:w=iw:h=ih:color=white@0.08:t=1[fg];"
                f"[bg][fg]overlay=0:(1920-h)/2{p_bar}{sub_tag},format=yuv420p[outv]"
            )
        elif mode in ("split_screen", "split", "interview"):
            return (
                f"[0:v]split=2[top_raw][bot_raw];"
                f"[top_raw]crop=w='min(iw,ih*9/8)':h='min(ih,iw*8/9)':x='(iw-out_w)/2':y=0,scale=1080:960{sharp_tag}[top];"
                f"[bot_raw]scale=1080:960{sharp_tag}[bot];"
                f"[top][bot]vstack,drawbox=x=0:y=959:w=1080:h=2:color=white@0.2:t=fill{p_bar}{sub_tag},format=yuv420p[outv]"
            )
        else:  # portrait_focus / smart_face / talking_head
            return (
                f"[0:v]crop=w='min(iw,ih*9/16)':h='min(ih,iw*16/9)':x='max(0,min(iw-out_w,(iw*{face_x_ratio:.3f})-(out_w/2)))':y='(ih-out_h)*0.35',"
                f"scale=1080:1920:flags=bicubic{sharp_tag}{p_bar}{sub_tag},format=yuv420p[outv]"
            )

smart_reframer = SmartReframingService()
