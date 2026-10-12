---
name: image-viewing
description: Use when you must see an image file's content.
---

# Viewing & Visually Verifying Images

How to get an image into your own context so you can describe/judge/verify it.

## Primary method (verified 2026-09)

`mcp__filesystem__read_media_file(path)` — returns the image directly into context as media content. Works for any local image file: user-sent attachments (download first with curl if they arrive as a URL), generated outputs, screenshots saved by terminal commands.

Use this BEFORE relying on browser screenshot pipelines when the goal is just "look at one image file" — fewer moving parts.

## When to view an image (don't skip)

- **User-facing visual deliverables** (avatars, designs, covers): visually verify before delivering. Skipping the check once led to delivering an avatar the user called ugly unchecked.
- **User sends an image for feedback**: download to /tmp, read it, then comment on what you actually see — never bluff a description.

## Adjacent habits

- Save keeper images (user-chosen finals) to `/root/public/` → durable URL `http://118.89.90.232/<name>` for chat embedding.
- If image generation itself is blocked (no API key), the fallback is a prompt pack for the user's own tools; for portraits this user prefers realistic photography style over anime. (Owned by the nano-banana-pro skill once adopted.)
