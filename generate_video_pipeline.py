import asyncio
import os
import re
import subprocess
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from playwright.async_api import Locator, Page, async_playwright

# region Configuration & Constants
APP_URL = "http://127.0.0.1:7860/"
OUTPUT_DIR = Path("build_video")
FINAL_VIDEO = Path("aegisor_automated_demo.mp4")
FINAL_SRT = Path("aegisor_automated_demo.srt")
VOICE = "en-US-AndrewMultilingualNeural"

SECTIONS = [
    {
        "id": "01_intro",
        "badge": "OVERVIEW",
        "topic": "Autonomous Ambient Clinical Intelligence Guardrail",
        "text": (
            "Welcome to AegisOR: an autonomous ambient clinical intelligence guardrail powered by AssemblyAI. "
            "AegisOR listens to operating room communications, validates surgical safety checklists in real time, "
            "enforces closed-loop communication, and produces an immutable operative audit ledger."
        ),
    },
    {
        "id": "02_screen0",
        "badge": "TAB 0: SETUP",
        "topic": "Pre-Case Lexicon Priming & Specialty Presets",
        "text": (
            "Before the procedure commences, we configure clinical parameters in Tab 0. "
            "Here, we select our specialty preset for Laparoscopic General Surgery and load procedural terms. "
            "This primes the speech recognition engine with custom acoustic probability boosting for critical landmarks like Calot's triangle and the cystic duct. "
            "Clicking 'Save and Update AI Lexicon' activates custom surgical vocabulary boosting instantly."
        ),
    },
    {
        "id": "03_screen1",
        "badge": "TAB 1: TIME-OUT",
        "topic": "The Universal Protocol Pre-Incision Verification",
        "text": (
            "Moving to Tab 1, AegisOR enforces The Joint Commission Universal Protocol before surgical incision. "
            "When the surgical team reviews the checklist, we execute pre-op verification. "
            "AegisOR validates patient identity, procedure, operative site, allergies, and prophylactic antibiotic timing. "
            "The safety status switches to 'Incision Authorized', and multi-speaker diarization confirms unanimous agreement across the surgeon, anesthesiologist, and circulating nurse."
        ),
    },
    {
        "id": "04_screen2",
        "badge": "TAB 2: CLOSED-LOOP",
        "topic": "Intra-Operative Medication & Order Reconciliation",
        "text": (
            "Once surgery is underway, Tab 2 tracks high-acuity verbal orders. "
            "When the surgeon directs five thousand units of Heparin or fentanyl for patient comfort, "
            "AegisOR reconciles the directive against the explicit verbal read-back from nursing. "
            "The active communication ledger confirms order closure in real time while extracting pharmaceutical dosages and surgical instruments automatically."
        ),
    },
    {
        "id": "05_screen3",
        "badge": "TAB 3: SIGN-OUT",
        "topic": "Post-Op Sign-Out & Operative Audit Compilation",
        "text": (
            "At the conclusion of the case, Tab 3 captures the surgical sign-out. "
            "Sponge, needle, and instrument counts are verified, and specimen labeling is logged. "
            "With one click on 'Generate Operative Audit Report', AegisOR compiles the complete operative record, "
            "aggregating pre-op checklist adherence, timestamped medication read-backs, and an executive clinical briefing ready for hospital EHR systems."
        ),
    },
    {
        "id": "06_summary",
        "badge": "SUMMARY",
        "topic": "Active Patient Safety Guardrail & Legal Defense",
        "text": (
            "In summary, AegisOR transforms ambient operating room audio into an active patient safety shield. "
            "It prevents never-events, safeguards healthcare institutions against malpractice liability, "
            "and eliminates manual computer interactions so surgical teams can concentrate entirely on patient care. "
            "Thank you for watching."
        ),
    },
]

INJECTED_OVERLAY_SCRIPT = """
(() => {
    const init = () => {
        // 1. Two-Line Modern Subtitle Card
        const sub = document.createElement('div');
        sub.id = 'aegisor-subtitles';
        sub.style.cssText = `
            position: fixed;
            bottom: 28px;
            left: 50%;
            transform: translateX(-50%);
            width: 88%;
            max-width: 1450px;
            background: rgba(11, 17, 32, 0.94);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 14px;
            padding: 12px 28px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.75);
            z-index: 2147483640;
            pointer-events: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            gap: 6px;
            align-items: center;
            transition: opacity 0.3s ease;
        `;
        sub.innerHTML = `
            <!-- Line 1: Topic / Summarization Line -->
            <div style="display: flex; align-items: center; gap: 10px;">
                <span id="caption-badge" style="background: #00e5ff; color: #0b1120; font-size: 11px; font-weight: 800; letter-spacing: 1px; padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">
                    OVERVIEW
                </span>
                <span id="caption-topic" style="color: #94a3b8; font-size: 13px; font-weight: 600; letter-spacing: 0.5px;">
                    AegisOR Surgical Safety Guardrail
                </span>
            </div>
            <!-- Line 2: Verbatim Spoken Words Line -->
            <div id="caption-spoken" style="color: #ffffff; font-size: 21px; font-weight: 600; line-height: 1.4; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.6);">
                Initializing AegisOR ambient intelligence demonstration...
            </div>
        `;
        (document.body || document.documentElement).appendChild(sub);

        // 2. Modern Precision Cursor (Figma/Linear Sleek Style)
        const cursor = document.createElement('div');
        cursor.id = 'playwright-visible-cursor';
        cursor.style.cssText = `
            position: fixed;
            top: 200px;
            left: 200px;
            width: 36px;
            height: 36px;
            pointer-events: none;
            z-index: 2147483647;
            display: block;
            filter: drop-shadow(0 4px 10px rgba(0,0,0,0.6)) drop-shadow(0 0 10px rgba(0, 229, 255, 0.7));
        `;
        cursor.innerHTML = `
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <defs>
                    <linearGradient id="modernCursorGrad" x1="4" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#00F0FF" />
                        <stop offset="1" stop-color="#3B82F6" />
                    </linearGradient>
                </defs>
                <path d="M4 2.5L22 11.5L12.5 14L10 23.5L4 2.5Z" fill="url(#modernCursorGrad)" stroke="#ffffff" stroke-width="1.8" stroke-linejoin="round"/>
            </svg>
            <!-- Glowing Laser Point at Precision Tip -->
            <div style="position: absolute; top: 0px; left: 1px; width: 8px; height: 8px; background: #00F0FF; border-radius: 50%; box-shadow: 0 0 10px #00F0FF, 0 0 22px #00E5FF; animation: laser-pulse 1s infinite alternate;"></div>
        `;
        (document.body || document.documentElement).appendChild(cursor);

        // 3. Animation Styles
        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes laser-halo-expand {
                0% { width: 12px; height: 12px; opacity: 1; border-width: 3px; }
                100% { width: 85px; height: 85px; opacity: 0; border-width: 1px; }
            }
            @keyframes laser-pulse {
                0% { transform: scale(0.9); opacity: 0.85; }
                100% { transform: scale(1.3); opacity: 1; }
            }
            .aegisor-popped-element {
                outline: 3px solid #00e5ff !important;
                box-shadow: 0 0 0 4px rgba(0, 229, 255, 0.4), 0 0 35px rgba(0, 229, 255, 0.85) !important;
                transform: scale(1.02) !important;
                transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
                z-index: 100 !important;
                position: relative !important;
            }
        `;
        document.head.appendChild(style);

        // 4. Global Bridge Methods
        window.activeTimers = [];

        window.scheduleVerbatimCaptions = (badge, topic, sentenceList) => {
            // Clear any pending timers
            window.activeTimers.forEach(t => clearTimeout(t));
            window.activeTimers = [];

            const elBadge = document.getElementById('caption-badge');
            const elTopic = document.getElementById('caption-topic');
            const elSpoken = document.getElementById('caption-spoken');

            if (elBadge) elBadge.innerText = badge;
            if (elTopic) elTopic.innerText = topic;

            sentenceList.forEach(s => {
                const timer = setTimeout(() => {
                    if (elSpoken) {
                        elSpoken.style.opacity = '0';
                        setTimeout(() => {
                            elSpoken.innerText = s.text;
                            elSpoken.style.opacity = '1';
                        }, 80);
                    }
                }, Math.max(0, s.start * 1000));
                window.activeTimers.push(timer);
            });
        };

        window.updateCursor = (x, y) => {
            const el = document.getElementById('playwright-visible-cursor');
            if (el) {
                el.style.left = x + 'px';
                el.style.top = y + 'px';
            }
        };

        window.emitRipple = (x, y) => {
            const rip = document.createElement('div');
            rip.style.cssText = `
                position: fixed;
                left: ${x}px;
                top: ${y}px;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                border: 3px solid #00e5ff;
                background: rgba(0, 229, 255, 0.3);
                box-shadow: 0 0 18px #00e5ff;
                pointer-events: none;
                z-index: 2147483646;
                transform: translate(-50%, -50%);
                animation: laser-halo-expand 0.5s ease-out forwards;
            `;
            document.body.appendChild(rip);
            setTimeout(() => rip.remove(), 550);
        };
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
"""
# endregion


# region TTS Generation & Verbatim Timestamps
async def generate_narration_audio() -> list[dict]:
    print("[VideoGen-generate_narration_audio] Generating speech narration and extracting sentence boundaries...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    clips = []

    for item in SECTIONS:
        mp3_path = OUTPUT_DIR / f"{item['id']}.mp3"
        print(f"[VideoGen-generate_narration_audio] Synthesizing '{item['id']}': {item['topic']}")
        comm = edge_tts.Communicate(item["text"], VOICE)

        audio_bytes = bytearray()
        sentences = []

        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_bytes.extend(chunk["data"])
            elif chunk.get("type") == "SentenceBoundary":
                start_s = chunk["offset"] / 10_000_000.0
                dur_s = chunk["duration"] / 10_000_000.0
                sentences.append({
                    "start": start_s,
                    "end": start_s + dur_s,
                    "text": chunk["text"].strip(),
                })

        with open(mp3_path, "wb") as f_out:
            f_out.write(audio_bytes)

        # Get total audio duration via imageio_ffmpeg
        res = subprocess.run(
            [ffmpeg_exe, "-i", str(mp3_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if match:
            hours, mins, secs = map(float, match.groups())
            duration = hours * 3600 + mins * 60 + secs
        else:
            duration = 10.0

        print(f"[VideoGen-generate_narration_audio] '{item['id']}' duration: {duration:.2f}s, {len(sentences)} verbatim sentences")
        clips.append({
            "id": item["id"],
            "badge": item["badge"],
            "topic": item["topic"],
            "mp3_path": mp3_path,
            "duration": duration,
            "sentences": sentences,
        })

    # Compile sentence-by-sentence SRT Subtitle File
    def format_srt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    current_t = 0.0
    srt_index = 1
    with open(FINAL_SRT, "w", encoding="utf-8") as f_srt:
        for clip in clips:
            for s in clip["sentences"]:
                start_str = format_srt_time(current_t + s["start"])
                end_str = format_srt_time(current_t + s["end"])
                f_srt.write(f"{srt_index}\n{start_str} --> {end_str}\n{s['text']}\n\n")
                srt_index += 1
            current_t += clip["duration"]

    print(f"[VideoGen-generate_narration_audio] Saved sentence-level SRT subtitles to {FINAL_SRT}")
    return clips
# endregion


# region Visual Focus & Navigation Helpers
async def smooth_move_cursor(
    page: Page,
    target_x: float,
    target_y: float,
    steps: int = 35,
) -> None:
    curr = await page.evaluate(
        "() => ({ x: parseFloat(document.getElementById('playwright-visible-cursor')?.style.left || '960'), y: parseFloat(document.getElementById('playwright-visible-cursor')?.style.top || '540') })"
    )
    start_x, start_y = curr["x"], curr["y"]

    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3.0 - 2.0 * t)
        cx = start_x + (target_x - start_x) * ease
        cy = start_y + (target_y - start_y) * ease
        await page.evaluate(f"([x, y]) => window.updateCursor(x, y)", [cx, cy])
        await page.mouse.move(cx, cy)
        await asyncio.sleep(0.016)


async def smooth_cursor_click(
    page: Page,
    locator: Locator,
    steps: int = 35,
    dwell_ms: int = 300,
) -> None:
    box = await locator.bounding_box()
    if box:
        target_x = box["x"] + box["width"] / 2
        target_y = box["y"] + box["height"] / 2
        await smooth_move_cursor(page, target_x, target_y, steps=steps)
        await page.wait_for_timeout(dwell_ms)
        await page.evaluate("([x, y]) => window.emitRipple(x, y)", [target_x, target_y])
        await page.mouse.down()
        await page.wait_for_timeout(100)
        await page.mouse.up()
        await locator.click()
    else:
        await locator.click()


async def pop_element(page: Page, locator: Locator, focus_label: str = "") -> None:
    await clear_pop(page)
    box = await locator.bounding_box()
    if box:
        # Move modern cursor to point at the popped element
        await smooth_move_cursor(page, box["x"] + 20, box["y"] + 20, steps=25)
        # Apply glowing highlight class
        await locator.evaluate(
            """(el, label) => {
                el.classList.add('aegisor-popped-element');
                if (label) {
                    const rect = el.getBoundingClientRect();
                    const badge = document.createElement('div');
                    badge.id = 'aegisor-focus-badge';
                    badge.innerText = 'FOCUS: ' + label.toUpperCase();
                    badge.style.cssText = `
                        position: fixed;
                        top: ${Math.max(10, rect.top - 26)}px;
                        left: ${rect.left}px;
                        background: #00e5ff;
                        color: #0b1120;
                        font-size: 11px;
                        font-weight: 800;
                        letter-spacing: 0.8px;
                        padding: 3px 8px;
                        border-radius: 4px;
                        box-shadow: 0 4px 14px rgba(0, 229, 255, 0.7);
                        z-index: 2147483642;
                        pointer-events: none;
                    `;
                    document.body.appendChild(badge);
                }
            }""",
            focus_label,
        )


async def clear_pop(page: Page) -> None:
    await page.evaluate(
        """() => {
            const badge = document.getElementById('aegisor-focus-badge');
            if (badge) badge.remove();
            document.querySelectorAll('.aegisor-popped-element').forEach(el => {
                el.classList.remove('aegisor-popped-element');
            });
        }"""
    )
# endregion


# region Browser Recording Session
async def record_presentation(clips: list[dict]) -> Path:
    print("[VideoGen-record_presentation] Initializing browser recording with verbatim captions & modern cursor...")
    raw_video_dir = OUTPUT_DIR / "raw_recordings"
    raw_video_dir.mkdir(parents=True, exist_ok=True)
    clips_by_id = {c["id"]: c for c in clips}

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(raw_video_dir),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        # Inject modern overlay script
        await page.add_init_script(INJECTED_OVERLAY_SCRIPT)
        print("[VideoGen-record_presentation] Navigating to AegisOR application...")
        await page.goto(APP_URL, wait_until="networkidle")
        await page.wait_for_timeout(1500)

        # -------------------------------------------------------------
        # Part 1: Intro (01_intro)
        # -------------------------------------------------------------
        print("[VideoGen-record_presentation] Recording Part 1: Intro...")
        start_time = asyncio.get_event_loop().time()
        c_intro = clips_by_id["01_intro"]
        await page.evaluate(
            "([b, t, s]) => window.scheduleVerbatimCaptions(b, t, s)",
            [c_intro["badge"], c_intro["topic"], c_intro["sentences"]],
        )

        # Smoothly guide modern cursor across the title banner
        await smooth_move_cursor(page, 480, 180, steps=25)
        await page.wait_for_timeout(1000)
        await smooth_move_cursor(page, 800, 200, steps=30)
        await page.wait_for_timeout(1200)

        elapsed = asyncio.get_event_loop().time() - start_time
        remaining = max(0.5, c_intro["duration"] - elapsed)
        await page.wait_for_timeout(remaining * 1000)

        # -------------------------------------------------------------
        # Part 2: Screen 0 (02_screen0)
        # -------------------------------------------------------------
        print("[VideoGen-record_presentation] Recording Part 2: Screen 0...")
        start_time = asyncio.get_event_loop().time()
        c_sc0 = clips_by_id["02_screen0"]
        await page.evaluate(
            "([b, t, s]) => window.scheduleVerbatimCaptions(b, t, s)",
            [c_sc0["badge"], c_sc0["topic"], c_sc0["sentences"]],
        )

        tab0 = page.get_by_role("tab", name="0. Pre-Case Setup & Lexicon Tuning")
        await smooth_cursor_click(page, tab0, steps=30)
        await page.wait_for_timeout(1000)

        btn_preset = page.get_by_role("button", name="Load Specialty Preset")
        await pop_element(page, btn_preset, "Specialty Preset Selector")
        await page.wait_for_timeout(1500)
        await smooth_cursor_click(page, btn_preset, steps=30)
        await page.wait_for_timeout(1000)

        btn_save = page.get_by_role("button", name="Save & Update AI Lexicon")
        await pop_element(page, btn_save, "Save & Update AI Lexicon")
        await page.wait_for_timeout(1500)
        await smooth_cursor_click(page, btn_save, steps=30)
        await page.wait_for_timeout(1200)

        await clear_pop(page)
        await smooth_move_cursor(page, 1380, 320, steps=30)

        elapsed = asyncio.get_event_loop().time() - start_time
        remaining = max(0.5, c_sc0["duration"] - elapsed)
        await page.wait_for_timeout(remaining * 1000)

        # -------------------------------------------------------------
        # Part 3: Screen 1 (03_screen1)
        # -------------------------------------------------------------
        print("[VideoGen-record_presentation] Recording Part 3: Screen 1...")
        start_time = asyncio.get_event_loop().time()
        c_sc1 = clips_by_id["03_screen1"]
        await page.evaluate(
            "([b, t, s]) => window.scheduleVerbatimCaptions(b, t, s)",
            [c_sc1["badge"], c_sc1["topic"], c_sc1["sentences"]],
        )

        tab1 = page.get_by_role("tab", name="1. Pre-Op Time-Out Verification")
        await smooth_cursor_click(page, tab1, steps=30)
        await page.wait_for_timeout(1000)

        btn_verify = page.get_by_role("button", name="Execute Pre-Op Verification")
        await pop_element(page, btn_verify, "Execute Pre-Op Verification")
        await page.wait_for_timeout(1500)
        await smooth_cursor_click(page, btn_verify, steps=30)
        await page.wait_for_timeout(2000)

        # Pop out checklist table
        table1 = page.locator("table").first
        if await table1.count() > 0:
            await pop_element(page, table1, "Universal Protocol Checklist")
            await page.wait_for_timeout(2500)

        elapsed = asyncio.get_event_loop().time() - start_time
        remaining = max(0.5, c_sc1["duration"] - elapsed)
        await page.wait_for_timeout(remaining * 1000)

        # -------------------------------------------------------------
        # Part 4: Screen 2 (04_screen2)
        # -------------------------------------------------------------
        print("[VideoGen-record_presentation] Recording Part 4: Screen 2...")
        start_time = asyncio.get_event_loop().time()
        c_sc2 = clips_by_id["04_screen2"]
        await page.evaluate(
            "([b, t, s]) => window.scheduleVerbatimCaptions(b, t, s)",
            [c_sc2["badge"], c_sc2["topic"], c_sc2["sentences"]],
        )

        tab2 = page.get_by_role("tab", name="2. Intra-Op Closed-Loop Tracking")
        await smooth_cursor_click(page, tab2, steps=30)
        await page.wait_for_timeout(1000)

        btn_track = page.get_by_role("button", name="Track Closed-Loop Orders")
        await pop_element(page, btn_track, "Track Closed-Loop Orders")
        await page.wait_for_timeout(1500)
        await smooth_cursor_click(page, btn_track, steps=30)
        await page.wait_for_timeout(2000)

        # Pop out communication table
        table2 = page.locator("table").first
        if await table2.count() > 0:
            await pop_element(page, table2, "Communication Ledger Table")
            await page.wait_for_timeout(2500)

        elapsed = asyncio.get_event_loop().time() - start_time
        remaining = max(0.5, c_sc2["duration"] - elapsed)
        await page.wait_for_timeout(remaining * 1000)

        # -------------------------------------------------------------
        # Part 5: Screen 3 (05_screen3)
        # -------------------------------------------------------------
        print("[VideoGen-record_presentation] Recording Part 5: Screen 3...")
        start_time = asyncio.get_event_loop().time()
        c_sc3 = clips_by_id["05_screen3"]
        await page.evaluate(
            "([b, t, s]) => window.scheduleVerbatimCaptions(b, t, s)",
            [c_sc3["badge"], c_sc3["topic"], c_sc3["sentences"]],
        )

        tab3 = page.get_by_role("tab", name="3. Post-Op Sign-Out & Operative Report")
        await smooth_cursor_click(page, tab3, steps=30)
        await page.wait_for_timeout(1000)

        btn_report = page.get_by_role("button", name="Generate Operative Audit Report")
        await pop_element(page, btn_report, "Generate Operative Audit Report")
        await page.wait_for_timeout(1500)
        await smooth_cursor_click(page, btn_report, steps=30)
        await page.wait_for_timeout(2200)

        await clear_pop(page)
        await smooth_move_cursor(page, 1350, 450, steps=30)
        await page.mouse.wheel(0, 320)
        await page.wait_for_timeout(1500)

        elapsed = asyncio.get_event_loop().time() - start_time
        remaining = max(0.5, c_sc3["duration"] - elapsed)
        await page.wait_for_timeout(remaining * 1000)

        # -------------------------------------------------------------
        # Part 6: Summary & Outro (06_summary)
        # -------------------------------------------------------------
        print("[VideoGen-record_presentation] Recording Part 6: Summary...")
        c_sc6 = clips_by_id["06_summary"]
        await page.evaluate(
            "([b, t, s]) => window.scheduleVerbatimCaptions(b, t, s)",
            [c_sc6["badge"], c_sc6["topic"], c_sc6["sentences"]],
        )

        await page.mouse.wheel(0, -320)
        await page.wait_for_timeout(800)
        await smooth_move_cursor(page, 960, 500, steps=30)
        await page.wait_for_timeout(c_sc6["duration"] * 1000)

        video_path = await page.video.path()
        await context.close()
        await browser.close()

    print(f"[VideoGen-record_presentation] Video recorded to: {video_path}")
    return Path(video_path)
# endregion


# region Media Assembly
def assemble_final_mp4(
    raw_video: Path,
    clips: list[dict],
) -> Path:
    print("[VideoGen-assemble_final_mp4] Concatenating audio tracks and muxing with video...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    concat_file = OUTPUT_DIR / "audio_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in clips:
            f.write(f"file '{clip['mp3_path'].resolve().as_posix()}'\n")

    combined_audio = OUTPUT_DIR / "combined_narration.mp3"
    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(combined_audio),
        ],
        check=True,
    )

    print(f"[VideoGen-assemble_final_mp4] Muxing video and audio into {FINAL_VIDEO}...")
    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-i",
            str(raw_video),
            "-i",
            str(combined_audio),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(FINAL_VIDEO),
        ],
        check=True,
    )

    size_mb = FINAL_VIDEO.stat().st_size / (1024 * 1024)
    print(f"[VideoGen-assemble_final_mp4] Successfully generated {FINAL_VIDEO} ({size_mb:.2f} MB)")
    return FINAL_VIDEO
# endregion


# region Entrypoint
async def main():
    print("[VideoGen-main] Starting video production with verbatim spoken captions & modern precision cursor...")
    clips = await generate_narration_audio()
    raw_video = await record_presentation(clips)
    assemble_final_mp4(raw_video, clips)
    print("[VideoGen-main] Enhanced video production complete!")


if __name__ == "__main__":
    asyncio.run(main())
# endregion
