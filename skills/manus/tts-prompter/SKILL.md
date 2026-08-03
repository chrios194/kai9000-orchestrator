---
name: tts-prompter
description: Prompt crafting for text-to-speech (TTS) tasks. Separates spoken text from style instructions. Use BEFORE entering generate mode for TTS.
---

# TTS Prompter

## Framework
1. Separate spoken text from style instructions
2. Use markup tags vs natural language for emotions
3. Non-speech sounds: explicit markers ([laugh], [pause], [gasp])
4. Voice characteristics: separate from content
5. Pacing: words-per-minute target

## Anti-Pattern
Don't mix style instructions into spoken text — use markup tags.
