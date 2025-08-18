# gradio_app_multimodal_gemini.py
# -------------------------------------------------------------
# Requirements:
#   pip install google-genai gradio httpx edge-tts pyttsx3 pillow langdetect
#   export GEMINI_API_KEY=...   (required)
#
# What this does:
# - ChatGPT-like Gradio UI (text + "+" tray + mic)
# - Accepts: text prompt, ONE image (quick attach), MULTIPLE docs (PDF/images/docs), audio (record/upload)
# - Sends raw media directly to Gemini 2.5 Flash (no OCR/ASR step)
# - Auto-uses inline bytes for small files, Files API for larger ones
# - Optional TTS voice reply (Edge-TTS first, pyttsx3 fallback)
# -------------------------------------------------------------

import os
import re
import uuid
import asyncio
import tempfile
import pathlib
from typing import Any, List, Optional, Iterable, Mapping, Tuple

import gradio as gr
from PIL import Image, ExifTags
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0



# Set up API key first
import os
if "GOOGLE_API_KEY" in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
else:
    # Fallback to hardcoded key if environment variable not set
    os.environ["GEMINI_API_KEY"] = 'AIzaSyC038SXpVnq_Iyaf4Jqg9kftp5T_qbOXmk'

GEMINI_MODEL = "gemini-2.5-flash"
# ---- Gemini 2.5 Flash client ----
# pip install google-genai
from google import genai
from google.genai import types
# Initialize client after API key is set
def get_gemini_client():
    """Get or create Gemini client with proper API key"""
    return genai.Client()

# Don't initialize client at module level - do it when needed
client = None


# ------------------------
# Helpers (unchanged / utility)
# ------------------------
_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:\d{2})$")
_VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")
_GENERIC_LABELS = {"text","message","user","agent","assistant","system","task","completed","role","id","kind","type","version","status","event","metadata","content"}

def _looks_like_noise(s: str) -> bool:
    t = s.strip()
    if not t: return True
    if t in _GENERIC_LABELS: return True
    if _UUID_RE.match(t): return True
    if _ISO_TS_RE.match(t): return True
    if _VERSION_RE.match(t): return True
    if len(t) <= 3 and t.isalnum(): return True
    return False

# ------------------------
# Image EXIF GPS (optional, we’ll add as context if present)
# ------------------------
def _convert_to_degrees(value):
    d = float(value[0][0]) / float(value[0][1])
    m = float(value[1][0]) / float(value[1][1])
    s = float(value[2][0]) / float(value[2][1])
    return d + (m / 60.0) + (s / 3600.0)

def extract_gps_from_image(image_path: str) -> Optional[Tuple[float, float]]:
    try:
        img = Image.open(image_path)
        exif = img._getexif()
        if not exif: return None
        exif_data = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        gps_info = exif_data.get("GPSInfo")
        if not gps_info: return None

        gps_data = {}
        for t in gps_info:
            sub_tag = ExifTags.GPSTAGS.get(t, t)
            gps_data[sub_tag] = gps_info[t]

        lat = _convert_to_degrees(gps_data["GPSLatitude"])
        if gps_data.get("GPSLatitudeRef") in ["S", b"S"]:
            lat = -lat
        lon = _convert_to_degrees(gps_data["GPSLongitude"])
        if gps_data.get("GPSLongitudeRef") in ["W", b"W"]:
            lon = -lon
        return (lat, lon)
    except Exception:
        return None

# ------------------------
# MIME + Parts builder for Gemini
# ------------------------
def to_mime(path: str) -> str:
    ext = pathlib.Path(path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".tiff":"image/tiff",

        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document",

        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".flac":"audio/flac",
        ".m4a": "audio/m4a",

        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".webm":"video/webm",
    }.get(ext, "application/octet-stream")

INLINE_LIMIT = 20 * 1024 * 1024  # ~20MB total request guideline

def _part_from_path(path: str):
    """Return a Part (inline) or a Files API object depending on size."""
    p = pathlib.Path(path)
    if not p.exists() or not p.is_file():
        return None
    mime = to_mime(str(p))
    size = p.stat().st_size
    if size < INLINE_LIMIT:
        return types.Part.from_bytes(data=p.read_bytes(), mime_type=mime)
    # Large: upload via Files API
    gemini_client = get_gemini_client()
    uploaded = gemini_client.files.upload(file=str(p), config={"mime_type": mime})
    return uploaded

def build_parts(prompt_text: str, file_paths: List[str], image_path: Optional[str], audio_path: Optional[str]) -> List[Any]:
    """
    Build multimodal 'contents' array for Gemini: raw bytes or Files API refs.
    Ordering: media first, then instruction text.
    """
    parts: List[Any] = []

    # single quick image attach
    if image_path:
        part = _part_from_path(image_path)
        if part is not None:
            parts.append(part)
            # Optional EXIF -> hint text
            gps = extract_gps_from_image(image_path)
            if gps:
                prompt_text = f"[Image EXIF GPS lat={gps[0]:.5f}, lon={gps[1]:.5f}]\n{prompt_text or ''}"

    # multi-docs (PDFs / images / docs)
    for fp in file_paths or []:
        if not fp: 
            continue
        part = _part_from_path(fp)
        if part is not None:
            parts.append(part)

    # audio (recorded/uploaded) — send raw audio; no ASR needed
    if audio_path:
        part = _part_from_path(audio_path)
        if part is not None:
            parts.append(part)

    # finally the instruction text
    parts.append(prompt_text or "")
    return parts

def ask_gemini(prompt_text: str, files: List[str], image_path: Optional[str], audio_path: Optional[str]) -> str:
    # System prompt to guide AI behavior
    system_prompt = """You are a helpful, knowledgeable, and friendly AI assistant. You excel at:

1. **Multimodal Understanding**: You can analyze images, documents, PDFs, and audio files with expertise
2. **Clear Communication**: Provide clear, concise, and helpful responses
3. **Context Awareness**: Consider all provided media and text when formulating responses
4. **Professional Tone**: Maintain a helpful and professional demeanor
5. **Accuracy**: When uncertain, acknowledge limitations and suggest alternatives
6. **File Analysis**: When documents or images are provided, analyze them thoroughly and reference specific content
7. **Audio Processing**: For audio inputs, provide relevant insights or transcriptions when possible

Always be helpful, accurate, and considerate in your responses.
some extra facts to be used when needed:
"🌾 **Comprehensive Farm Conditions Report for Chandigarh** 🌾\n\nHere's your 7-day farming outlook:\n\n📍 **Location:** Chandigarh, India\n📅 **Analysis Period:** August 18, 2025 (7 days)\n\n🌡️ **Current Conditions**\n*   Temperature: 32.0°C (Feels like 38.1°C)\n*   Humidity: 70%\n*   Weather: Partly cloudy ⛅\n*   Wind Speed: 15.3 km/h\n*   Precipitation: 0.0 mm\n*   Soil Temperature: 26.3°C\n*   Soil Moisture: 0.314 m³/m³\n\n📊 **7-Day Outlook**\n*   Average High: 31.4°C\n*   Total Expected Rainfall: 23.6 mm\n*   Rainy Days Expected: 6\n*   Soil Status: 🟢 Good\n\n🚜 **Farming Recommendations**\n*   🌪️ High winds - avoid spraying pesticides\n*   🌧️ Wet week expected - check drainage systems\n\n**Overall:** Be prepared for a wet week and avoid spraying due to high winds. Make sure your drainage is functioning well.\n"


Based on the information provided, here's what I can tell you about government loan schemes and financing facilities for Indian farmers:\n\nOne significant government initiative is the **Agriculture Infrastructure Fund (AIF)**. This is a Central Sector Scheme announced to provide a financing facility of **₹1 lakh crore** for funding Agriculture Infrastructure Projects.\n\nKey details about the Agriculture Infrastructure Fund:\n*   **Purpose:** It aims to mobilize medium to long-term debt financing for investments in viable projects related to post-harvest management infrastructure and community farming assets. This includes developing infrastructure at farm-gate and aggregation points.\n*   **Beneficiaries:** Eligible beneficiaries include Primary Agricultural Cooperative Societies, Farmers Producer Organizations, Agriculture entrepreneurs, and Start-ups, among others.\n*   **Rationale:** The scheme recognizes the crucial role of infrastructure in agricultural development, particularly at the post-harvest stage, to optimize produce utilization, add value, and ensure fair deals for farmers.\n\nIn addition to specific schemes like the AIF, institutional credit for farmers in India is generally channeled through a multi-agency network that includes:\n*   **Commercial Banks (CBs)**\n*   **Regional Rural Banks (RRBs)**\n*   **Cooperative Societies**\n\nThese institutions provide various types of agricultural loans:\n*   **Short-term credit:** Typically for pre-harvest and post-harvest activities like purchasing inputs, weeding, harvesting, sorting, and transporting.\n*   **Long-term credit:** Generally for investments in agricultural machinery and equipment, irrigation, and other developmental activities.\n\nThe **Self-Help Groups (SHGs) - Bank Linkage** program, initiated by the National Bank for Agriculture and Rural Development (NABARD), is another approach developed to provide microfinance and reach the poorest segments of the rural population.\n\nIt's important to note that access to formal credit can be a challenge for some farmers, particularly small and marginal farmers, often due to issues like not holding formal land titles. These farmers may sometimes rely more on informal sources of credit.\n\nWhile the provided context highlights the Agriculture Infrastructure Fund and the general framework of institutional credit, it does not list a comprehensive catalog of all government loan schemes available to farmers."



I consulted the Market Intelligence Agent for Indian Agriculture. Here's their detailed response regarding potato markets in West Bengal:\n\nI've already provided the list of markets for potato in West Bengal in our previous interaction. Here it is again for your convenience:\n\nAcross West Bengal, here are the markets where potato is sold:\n\n🏪 **Available Markets (6 found):**\n\n1.  **Kalimpong** (ID: 704)\n    *   State ID: 19, District ID: 327\n2.  **Siliguri** (ID: 2923)\n    *   State ID: 19, District ID: 327\n3.  **Matigara** (ID: 3939)\n    *   State ID: 19, District ID: 327\n4.  **Darjeeling(Klimpong)** (ID: 3940)\n    *   State ID: 19, District ID: 327\n5.  **Karsiyang(Matigara)** (ID: 4335)\n    *   State ID: 19, District ID: 327\n6.  **Darjeeling** (ID: 4336)\n    *   State ID: 19, District ID: 327
use these information to answer the user's query
"""

    # Build contents with system prompt first, then user content
    contents = [
        types.Part.from_text(text=system_prompt),
        *build_parts(prompt_text, files, image_path, audio_path)
    ]
    
    # Get client when needed
    gemini_client = get_gemini_client()
    resp = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=contents)
    return getattr(resp, "text", "") or ""

# ------------------------
# TTS (edge first, pyttsx3 fallback)
# ------------------------
import edge_tts, pyttsx3, wave

def _detect_lang_code(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "en"

VOICE_EDGE = {
    "bn": "bn-IN-TanishaaNeural",
    "hi": "hi-IN-SwaraNeural",
    "en": "en-US-AriaNeural",
}
def _pick_edge_voice(text: str) -> str:
    code = _detect_lang_code(text)
    return VOICE_EDGE.get(code, VOICE_EDGE["en"])

async def tts_edge_mp3(text: str) -> Optional[str]:
    if not text or not text.strip():
        return None
    voice = _pick_edge_voice(text)
    out_path = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.mp3")
    try:
        await edge_tts.Communicate(text, voice=voice).save(out_path)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
            return out_path
    except Exception as e:
        print("edge-tts failed:", e)
    return None

def _pick_pyttsx3_voice(engine, text: str):
    def detect_lang_code_quick(txt):
        if any(ch in txt for ch in "অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহ"):
            return "bn"
        if any(ch in txt for ch in "अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह"):
            return "hi"
        return "en"
    target = {"bn": "bn-IN", "hi": "hi-IN", "en": "en-US"}[detect_lang_code_quick(text)].lower()

    def norm_langs(v):
        out = []
        if hasattr(v, "languages") and v.languages:
            for item in v.languages:
                if isinstance(item, bytes):
                    out.append(item.decode(errors="ignore").lower())
                elif isinstance(item, str):
                    out.append(item.lower())
                else:
                    out.append(str(item).lower())
        return out

    voices = engine.getProperty("voices") or []
    for v in voices:
        vid = (getattr(v, "id", "") or "").lower()
        name = (getattr(v, "name", "") or "").lower()
        langs = norm_langs(v)
        if target in vid or target in name or any(target in l for l in langs):
            return v.id
    fam = target.split("-")[0]
    for v in voices:
        vid = (getattr(v, "id", "") or "").lower()
        name = (getattr(v, "name", "") or "").lower()
        langs = norm_langs(v)
        if fam in vid or fam in name or any(fam in l for l in langs):
            return v.id
    for v in voices:
        if "en" in (getattr(v, "id", "") or "").lower() or "english" in (getattr(v, "name", "") or "").lower():
            return v.id
    return voices[0].id if voices else None

def tts_pyttsx3_wav(text: str) -> Optional[str]:
    if not text or not text.strip():
        return None
    engine = pyttsx3.init()
    vid = _pick_pyttsx3_voice(engine, text)
    if vid:
        engine.setProperty("voice", vid)
    engine.setProperty("rate", 180)
    engine.setProperty("volume", 1.0)
    out_wav = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.wav")
    engine.save_to_file(text, out_wav)
    engine.runAndWait()
    try:
        with wave.open(out_wav, "rb") as wf:
            if wf.getnframes() <= 0:
                return None
    except Exception:
        return None
    return out_wav

async def synthesize_tts_hybrid(text: str) -> Optional[str]:
    try:
        mp3 = await tts_edge_mp3(text)
        if mp3:
            return mp3
    except Exception as e:
        print("edge-tts fatal:", e)
    try:
        return tts_pyttsx3_wav(text)
    except Exception as e:
        print("pyttsx3 fatal:", e)
        return None

# ------------------------
# Gradio handler (Gemini backend)
# ------------------------
async def send_query(user_text, img_path, audio_path, doc_files, messages):
    """
    user_text: str
    img_path: str | None (single quick image)
    audio_path: str | None (recorded/uploaded audio)
    doc_files: list[str] | None (multiple PDFs/images/docs)
    messages: running chat state (ignored for context here, but we preserve UI history)
    """
    messages = messages or []

    # Collect multi-doc file paths
    file_paths: List[str] = []
    if isinstance(doc_files, list):
        for f in doc_files:
            if isinstance(f, dict) and "name" in f:  # older Gradio payloads may pass dicts
                file_paths.append(f["name"])
            elif isinstance(f, str):
                file_paths.append(f)
    elif isinstance(doc_files, str) and doc_files:
        file_paths.append(doc_files)

    prompt = (user_text or "").strip()

    # --- Call Gemini (run in a worker thread so async Gradio stays happy)
    reply_text = await asyncio.to_thread(ask_gemini, prompt, file_paths, img_path, audio_path)
    if not reply_text:
        reply_text = "I couldn't generate a reply. Please try a smaller/shorter file or a clearer prompt."

    # TTS voice reply
    tts_path = await synthesize_tts_hybrid(reply_text)
    audio_component_value = tts_path if tts_path else gr.update(value=None)

    # Update chat history for the Chatbot UI
    user_msg_preview = prompt if prompt else "(media attached)"
    messages.append({"role": "user", "content": user_msg_preview})
    messages.append({"role": "assistant", "content": reply_text})

    return messages, audio_component_value, messages

# ==== DROP-IN UI (ChatGPT-style composer with "+" and "mic") ====
theme = gr.themes.Soft(
    primary_hue="green",
    neutral_hue="zinc",
).set(
    body_background_fill="linear-gradient(180deg, #0b1220 0%, #0f172a 100%)",
    block_shadow="0 10px 30px rgba(0,0,0,.18)",
    button_primary_background_fill="linear-gradient(90deg,#22c55e,#16a34a)",
    button_primary_text_color="white",
)

CSS = """
/* layout width similar to ChatGPT */
.container { max-width: 980px !important; margin: 0 auto !important; }

/* chat card */
.chat-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px;
  padding: 8px;
  backdrop-filter: blur(6px);
}

/* sticky composer like ChatGPT */
.composer {
  position: sticky; bottom: 0; z-index: 10;
  padding-top: 10px;
  background: linear-gradient(180deg, rgba(11,18,32,0), rgba(11,18,32,1) 40%);
}

/* input dock: big rounded bar */
.input-dock {
  display: grid;
  grid-template-columns: 44px 1fr 44px 52px; /* + | text | mic | send */
  gap: 10px; align-items: center;
  background: #1f2937;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 999px;
  padding: 6px 6px 6px 8px;
}

/* round icon buttons */
.icon-btn {
  height: 44px; width: 44px; border-radius: 999px;
  display:flex; align-items:center; justify-content:center;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.16);
  color: #e5e7eb; font-size: 20px;
}
.icon-btn:hover { background: rgba(255,255,255,0.10); }

/* send button at right */
.send-btn { height: 44px; border-radius: 999px; font-weight: 700; }

/* flat textbox inside the dock */
#msg_box textarea {
  min-height: 44px; max-height: 140px;
  background: transparent !important; border: none !important;
  box-shadow: none !important; color: #e5e7eb !important;
  padding-left: 2px;
}

/* attachments tray */
.attach-tray {
  margin-top: 8px;
  background: #0f172a;
  border: 1px dashed rgba(255,255,255,0.18);
  border-radius: 14px;
  padding: 10px;
}

/* remove extra chrome on inline components */
.flat .container, .flat .wrap, .flat .form, .flat .block, .flat .label-wrap {
  border:none !important; box-shadow:none !important;
  margin:0 !important; padding:0 !important;
}
"""

with gr.Blocks(title="Multimodal Gemini Assistant", theme=theme, css=CSS) as demo:
    # Header
    gr.Markdown(
        """
        <div class="container" style="padding:14px 0 6px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <img src="https://em-content.zobj.net/thumbs/240/apple/354/seedling_1f331.png" width="24">
            <div style="color:#e5e7eb;font-size:20px;font-weight:700;">Multimodal Gemini Assistant</div>
            <div style="margin-left:auto;color:#86efac;font-size:13px;">● Connected</div>
          </div>
        </div>
        """
    )

    with gr.Column(elem_classes=["container"]):
        # Chat area
        with gr.Group(elem_classes=["chat-card"]):
            chatbot = gr.Chatbot(
                type="messages",
                height=480,
                bubble_full_width=False,
                show_copy_button=True,
            )

        # === Sticky composer & trays (REPLACED) ===
        with gr.Column(elem_classes=["composer"]):
            # Rounded input bar
            with gr.Row(elem_classes=["input-dock"]):
                plus_btn = gr.Button("＋", elem_classes=["icon-btn"], value="＋")
                msg = gr.Textbox(
                    placeholder="Ask anything… or attach PDFs/images/audio with ＋",
                    lines=2, show_label=False, container=False, elem_id="msg_box"
                )
                mic_btn = gr.Button("🎤", elem_classes=["icon-btn"], value="🎤")
                send_btn = gr.Button("Send ➤", variant="primary", elem_classes=["send-btn"])

            # Attachments tray (PDFs / images). Shown ONLY by ＋
            with gr.Column(visible=False, elem_classes=["attach-tray"]) as attach_tray:
                with gr.Row():
                    # Quick single image picker (filepath)
                    img_in = gr.Image(type="filepath", label=None, elem_classes=["flat"])
                    # Multi-file picker: PDFs / images / docs
                    doc_in = gr.File(
                        file_count="multiple", label=None, elem_classes=["flat"],
                        file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".doc", ".docx"]
                    )

            # Audio tray (mic / upload). Shown ONLY by 🎤
            with gr.Column(visible=False, elem_classes=["attach-tray"]) as audio_tray:
                audio_in = gr.Audio(
                    type="filepath",
                    sources=["microphone","upload"],
                    label=None,
                    elem_classes=["flat"],
                )

        # Voice reply (autoplay)
        tts_out = gr.Audio(label="Voice Reply", type="filepath", autoplay=True)

        # State for chat history + tray toggles
        history = gr.State([])
        attach_open = gr.State(False)
        audio_open = gr.State(False)

        # --- Actions ---

        def _toggle_attach(is_open_attach: bool, is_open_audio: bool):
            """Toggle ONLY the attachments tray; close audio tray if open."""
            new_attach = not is_open_attach
            # Close audio tray if we open attachments
            new_audio = False if new_attach else is_open_audio
            return (
                new_attach,                     # attach_open
                new_audio,                      # audio_open
                gr.update(visible=new_attach),  # attach_tray
                gr.update(visible=new_audio)    # audio_tray
            )

        plus_btn.click(
            _toggle_attach,
            inputs=[attach_open, audio_open],
            outputs=[attach_open, audio_open, attach_tray, audio_tray]
        )

        def _toggle_audio(is_open_audio: bool, is_open_attach: bool):
            """Toggle ONLY the audio tray; close attachments tray if open."""
            new_audio = not is_open_audio
            # Close attachments tray if we open audio
            new_attach = False if new_audio else is_open_attach
            return (
                new_attach,                      # attach_open
                new_audio,                       # audio_open
                gr.update(visible=new_attach),   # attach_tray
                gr.update(visible=new_audio)     # audio_tray
            )

        mic_btn.click(
            _toggle_audio,
            inputs=[audio_open, attach_open],
            outputs=[attach_open, audio_open, attach_tray, audio_tray]
        )

        def _audio_chosen(_path):
            # Hide audio tray after recording/upload
            return False, gr.update(visible=False)

        audio_in.change(
            _audio_chosen,
            inputs=audio_in,
            outputs=[audio_open, audio_tray]
        )

        def _post_send_cleanup():
            # Hide both trays after send and clear the text box
            return (
                False, gr.update(visible=False),  # attach_open, attach_tray
                False, gr.update(visible=False),  # audio_open, audio_tray
                ""                                # clear msg box
            )

        # Send (button + Enter)
        send_btn.click(
            fn=send_query,
            inputs=[msg, img_in, audio_in, doc_in, history],
            outputs=[chatbot, tts_out, history],
            queue=True
        ).then(
            _post_send_cleanup,
            inputs=None,
            outputs=[attach_open, attach_tray, audio_open, audio_tray, msg]
        )

        msg.submit(
            fn=send_query,
            inputs=[msg, img_in, audio_in, doc_in, history],
            outputs=[chatbot, tts_out, history],
            queue=True
        ).then(
            _post_send_cleanup,
            inputs=None,
            outputs=[attach_open, attach_tray, audio_open, audio_tray, msg]
        )


if __name__ == "__main__":
    # Public link:
    demo.queue().launch(share=True)
    # demo.queue().launch()
