# YouTube Upload — LLARS Demo (IJCAI 2026)

## Title (max 100 characters)

```
LLARS Demo (IJCAI–ECAI 2026): Prompting, Batch Generation & Hybrid Evaluation
```

## Description

```
We demonstrate LLARS (LLM Assisted Research System), an open-source platform that connects domain experts and developers when building LLM-based systems. The video walks through the full pipeline end-to-end:

• Collaborative Prompt Engineering — real-time co-authoring with version control and instant LLM testing
• Batch Generation — configurable runs across prompts × models × data with cost control
• Hybrid Evaluation — humans and LLM evaluators jointly assess outputs, with live inter-rater agreement statistics and provenance analysis to surface the best model–prompt pair

Live demo: https://llars.e-beratungsinstitut.de
Source code: https://github.com/th-nuernberg/llars

Disclosure: The voice-over narration was generated using a Qwen3 TTS 0.6B model.
```

## Files

| Asset | Path |
|---|---|
| Video | `Paper/demo-video/output/llars.mp4` (100 MB, 8:59 min, 3600×2024 @ 60 fps, 16:9) |
| Thumbnail | `Paper/demo-video/output/thumbnails/thumbnail.png` (2560×1440, 16:9) |

## YouTube Settings

| Field | Value |
|---|---|
| **Made for kids** | No |
| **Age restriction** | None |
| **Visibility** | **Unlisted** (recommended for academic demo: link-only access, no YouTube discovery / spam comments) |
| **A/B Testing** | Off |
| **Playlists** | None |
| **Paid promotion** | No |
| **Subtitles** | Optional — auto-generated is acceptable |
| **Category** | Science & Technology |
| **Tags** *(optional)* | `LLM`, `prompt engineering`, `evaluation`, `IJCAI 2026`, `online counselling`, `human-AI collaboration` |

## After Upload

1. Copy the YouTube URL (format: `https://youtu.be/<id>`)
2. Update Paper footnote in `Paper/ijcai26.tex` line 293:
   ```
   Our demo\footnote{Video: \url{https://youtu.be/<id>}} ...
   ```
3. Re-compile: `cd Paper && ./build.sh`
4. Submit camera-ready PDF + source ZIP to `proceedings.ijcai.org`
