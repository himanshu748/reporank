import os
import math
import wave
import struct
from PIL import Image, ImageDraw, ImageFont
import shutil
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ImageClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

# ──────────────────────────────────────────────────────────────────────────
# 1. Synthesize Background Lo-Fi Beat (WAV generator)
# ──────────────────────────────────────────────────────────────────────────
def generate_synth_music(filename="scratch/background_beat.wav", duration=150, sample_rate=44100):
    print(f"Generating synthesized background soundtrack ({duration} seconds)...")
    
    # Setup WAV file
    wav_file = wave.open(filename, "w")
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)
    
    bpm = 85
    seconds_per_beat = 60.0 / bpm
    total_samples = int(duration * sample_rate)
    
    # Chord frequencies (Lo-Fi progression: Cmaj7 - Am7 - Fmaj7 - G7)
    chords = [
        [130.81, 164.81, 196.00, 246.94],  # Cmaj7
        [110.00, 130.81, 164.81, 196.00],  # Am7
        [87.31, 110.00, 130.81, 164.81],   # Fmaj7
        [98.00, 123.47, 146.83, 196.00]    # G7
    ]
    
    # Write sample by sample
    for s in range(total_samples):
        t = s / sample_rate
        beat_idx = int(t / seconds_per_beat)
        chord_idx = (beat_idx // 4) % len(chords)
        current_chord = chords[chord_idx]
        
        # 1. Mellow electric piano synth (sine wave mix)
        synth_val = 0
        for freq in current_chord:
            # Slow envelope per beat
            beat_progress = (t % seconds_per_beat) / seconds_per_beat
            envelope = math.exp(-3.5 * beat_progress) # slow decay
            synth_val += math.sin(2 * math.pi * freq * t) * envelope
        synth_val = (synth_val / len(current_chord)) * 0.25 # volume scaling
        
        # 2. Add deep sub-bass line
        bass_freq = current_chord[0] / 2
        bass_val = math.sin(2 * math.pi * bass_freq * t) * 0.15
        
        # 3. Simple soft hi-hat/percussion beat (white noise envelope)
        perc_val = 0
        # Hi-hat tick on every half-beat
        half_beat_progress = (t % (seconds_per_beat / 2)) / (seconds_per_beat / 2)
        if half_beat_progress < 0.15:
            # Pseudo-random noise tick
            noise = (math.sin(1000 * t) + math.sin(2345 * t)) / 2
            perc_val = noise * math.exp(-25 * half_beat_progress) * 0.05
            
        sample = synth_val + bass_val + perc_val
        # Limit clipping
        sample = max(-1.0, min(1.0, sample))
        
        # Pack to 16-bit PCM integer
        packed_val = struct.pack("<h", int(sample * 32767))
        wav_file.writeframes(packed_val)
        
    wav_file.close()
    print("Soundtrack generation complete!")

# ──────────────────────────────────────────────────────────────────────────
# 2. Render Text Overlays and Banners using Pillow
# ──────────────────────────────────────────────────────────────────────────
def create_text_overlay(text, size=(1280, 80), font_size=24, bg_color=(10, 10, 15, 230), text_color=(126, 254, 109, 255)):
    # Create image with transparent/dark background
    img = Image.new("RGBA", size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try Helvetica or Arial
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    if not os.path.exists(font_path):
        font_path = "/Library/Fonts/Arial.ttf"
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
        
    # Get bounding box of text to center it
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    x = (size[0] - w) // 2
    y = (size[1] - h) // 2 - bbox[1]
    
    draw.text((x, y), text, font=font, fill=text_color)
    return img

def create_title_card(title, subtitle, size=(1280, 800), bg_color=(10, 10, 15, 255)):
    img = Image.new("RGBA", size, bg_color)
    draw = ImageDraw.Draw(img)
    
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    if not os.path.exists(font_path):
        font_path = "/Library/Fonts/Arial.ttf"
        
    try:
        title_font = ImageFont.truetype(font_path, 42)
        sub_font = ImageFont.truetype(font_path, 22)
    except:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        
    # Draw Title
    t_bbox = draw.textbbox((0, 0), title, font=title_font)
    t_w = t_bbox[2] - t_bbox[0]
    t_h = t_bbox[3] - t_bbox[1]
    t_x = (size[0] - t_w) // 2
    t_y = size[1] // 2 - t_h - 10
    draw.text((t_x, t_y), title, font=title_font, fill=(126, 254, 109, 255)) # Glowing green
    
    # Draw Subtitle
    s_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    s_w = s_bbox[2] - s_bbox[0]
    s_h = s_bbox[3] - s_bbox[1]
    s_x = (size[0] - s_w) // 2
    s_y = size[1] // 2 + 20
    draw.text((s_x, s_y), subtitle, font=sub_font, fill=(200, 200, 220, 255))
    
    return img

# ──────────────────────────────────────────────────────────────────────────
# 3. Assemble and Edit
# ──────────────────────────────────────────────────────────────────────────
def edit_demo_video():
    print("=== Starting Video Editor ===")
    
    raw_video_path = "./scratch/raw_walkthrough.webm"
    if not os.path.exists(raw_video_path):
        print(f"Error: {raw_video_path} not found. Run record_demo.py first.")
        return
        
    # Generate beat track
    generate_synth_music()
    
    # Generate PNG frames for titles
    os.makedirs("./scratch/temp_frames", exist_ok=True)
    
    # Create Title Frames
    create_title_card(
        "THE PROBLEM",
        "Open-source impact metrics are fragmented across registries, GitHub, and forums."
    ).save("./scratch/temp_frames/problem_card.png")
    
    create_title_card(
        "THE SOLUTION: REPORANK",
        "A single Coral SQL query aggregates signals, feeding Hugging Face Qwen AI to score & match grants."
    ).save("./scratch/temp_frames/solution_card.png")
    
    create_title_card(
        "REPORANK IN ACTION",
        "Watch RepoRank evaluate a repository and generate a live funding pitch."
    ).save("./scratch/temp_frames/demo_card.png")

    create_title_card(
        "REPORANK BY THE NUMBERS",
        "Calculating Health Radar, strengths, gaps, and grant recommendations."
    ).save("./scratch/temp_frames/radar_card.png")
    
    create_title_card(
        "THE POWER OF CORAL SQL",
        "Inspecting the single federated query running behind the scenes."
    ).save("./scratch/temp_frames/sql_card.png")
    
    create_title_card(
        "SUCCESSFULLY DEPLOYED",
        "RepoRank is now live, public, and ready to evaluate. Happy sailing! 🏴‍☠️"
    ).save("./scratch/temp_frames/outro_card.png")

    # Create Banner Captions
    create_text_overlay("Step 1: Connecting your GitHub profile to load repositories").save("./scratch/temp_frames/cap1.png")
    create_text_overlay("Step 2: Selecting repository to trigger Coral SQL federated queries").save("./scratch/temp_frames/cap2.png")
    create_text_overlay("Step 3: Aggregating stats (downloads, stars, HackerNews buzz, funding)").save("./scratch/temp_frames/cap3.png")
    create_text_overlay("Step 4: AI models process signals, scoring impact and matching active grants").save("./scratch/temp_frames/cap4.png")
    create_text_overlay("Step 5: Interactive SVG Health Radar and copy-pasteable funding pitch").save("./scratch/temp_frames/cap5.png")
    create_text_overlay("Step 6: Inspecting the exact Coral SQL JOIN query executed by the orchestrator").save("./scratch/temp_frames/cap6.png")

    # ── Create Clip Objects ─────────────────────────────────────────────────
    print("Loading video files and creating timelines...")
    
    # 1. Slide Clips
    slide_problem = ImageClip("./scratch/temp_frames/problem_card.png", duration=5)
    slide_solution = ImageClip("./scratch/temp_frames/solution_card.png", duration=5)
    slide_demo = ImageClip("./scratch/temp_frames/demo_card.png", duration=4)
    slide_radar = ImageClip("./scratch/temp_frames/radar_card.png", duration=4)
    slide_sql = ImageClip("./scratch/temp_frames/sql_card.png", duration=4)
    slide_outro = ImageClip("./scratch/temp_frames/outro_card.png", duration=5)
    
    # 2. Main Walkthrough Clips (segmented from raw_walkthrough.webm)
    # 2. Main Walkthrough Clips (segmented from raw_walkthrough.webm)
    walkthrough = VideoFileClip(raw_video_path)
    
    # Timings based on record_demo.py steps:
    # Segment A: Navigating and connecting GitHub modal (0s to 12s in raw)
    clip_connect = walkthrough.subclipped(0, 12)
    cap_connect = ImageClip("./scratch/temp_frames/cap1.png", duration=12).with_position(("center", "bottom"))
    segment_connect = CompositeVideoClip([clip_connect, cap_connect])
    
    # Segment B: Filling username and clicking connect (12s to 18s in raw)
    clip_login = walkthrough.subclipped(12, 18)
    cap_login = ImageClip("./scratch/temp_frames/cap2.png", duration=6).with_position(("center", "bottom"))
    segment_login = CompositeVideoClip([clip_login, cap_login])
    
    # Segment C: Sidebar populating and selecting reporank (18s to 26s in raw)
    clip_select = walkthrough.subclipped(18, 26)
    cap_select = ImageClip("./scratch/temp_frames/cap3.png", duration=8).with_position(("center", "bottom"))
    segment_select = CompositeVideoClip([clip_select, cap_select])
    
    # Segment D: Loading animation (26s to 38s in raw)
    clip_loading = walkthrough.subclipped(26, 38)
    cap_loading = ImageClip("./scratch/temp_frames/cap4.png", duration=12).with_position(("center", "bottom"))
    segment_loading = CompositeVideoClip([clip_loading, cap_loading])
    
    # Segment E: Show result metrics (38s to 43s in raw)
    clip_results = walkthrough.subclipped(38, 43)
    cap_results = ImageClip("./scratch/temp_frames/cap5.png", duration=5).with_position(("center", "bottom"))
    segment_results = CompositeVideoClip([clip_results, cap_results])
    
    # Segment F: Scroll to Radar Chart (43s to 50s in raw)
    clip_radar = walkthrough.subclipped(43, 50)
    cap_radar = ImageClip("./scratch/temp_frames/cap5.png", duration=7).with_position(("center", "bottom"))
    segment_radar_capture = CompositeVideoClip([clip_radar, cap_radar])
    
    # Segment G: Scroll to Coral SQL details and open (50s to 60s in raw)
    clip_sql = walkthrough.subclipped(50, 60)
    cap_sql = ImageClip("./scratch/temp_frames/cap6.png", duration=10).with_position(("center", "bottom"))
    segment_sql_capture = CompositeVideoClip([clip_sql, cap_sql])
    
    # ── Concatenate Timeline ────────────────────────────────────────────────
    print("Concatenating all elements...")
    
    # Construct sequence
    clips_sequence = [
        slide_problem,
        slide_solution,
        slide_demo,
        segment_connect,
        segment_login,
        segment_select,
        segment_loading,
        segment_results,
        slide_radar,
        segment_radar_capture,
        slide_sql,
        segment_sql_capture,
        slide_outro
    ]
    
    # Calculate exact start times to align sequence
    current_time = 0
    positioned_clips = []
    
    for clip in clips_sequence:
        fade_clip = clip.with_start(current_time)
        positioned_clips.append(fade_clip)
        current_time += clip.duration
        
    final_video = CompositeVideoClip(positioned_clips, size=(1280, 800))
    # Make sure video duration matches the timeline total
    final_duration = current_time
    print(f"Final sequence duration: {final_duration} seconds.")
    
    # Overlay the synthesized background music
    print("Applying synthesized background beat...")
    music_track = AudioFileClip("scratch/background_beat.wav").subclipped(0, final_duration)
    final_video = final_video.with_audio(music_track)
    
    # Export
    output_video_path = "./screenshots/reporank_demo.mp4"
    os.makedirs("./screenshots", exist_ok=True)
    
    print(f"Rendering final polished video to {output_video_path}...")
    final_video.write_videofile(
        output_video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4
    )
    
    # Clean up temp frames
    print("Cleaning up temp frames...")
    shutil.rmtree("./scratch/temp_frames")
    
    print("=== Video Compilation Successful ===")

if __name__ == "__main__":
    edit_demo_video()
