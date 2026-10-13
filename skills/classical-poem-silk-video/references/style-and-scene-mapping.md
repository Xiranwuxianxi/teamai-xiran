# Style and scene mapping

## Shared Chinese-art series anchor

Use this as the common quality and cultural anchor. Do not require every clause to be visually identical in every scene:

```text
Refined traditional Chinese painting on aged silk, Song-dynasty-inspired gongbi precision for birds, branches, figures, architecture, animals, and foreground textures, blended with restrained Yuan-style pale-ink landscape washes; tall deep-distance composition; delicate dry-brush contours, layered ink modulation, sparse mineral pigments, subtle silk fibers, faint foxing, natural pigment granulation, mist-softened transitions, museum-quality antique handscroll atmosphere. Low-saturation antique parchment beige, ink black, smoky gray, muted blue-gray, pale jade green, and restrained ochre. Quiet, poetic, materially believable, never glossy or digitally slick.
```

The shared anchor governs Chinese visual credibility, historical plausibility, craft quality, detail density, and overall saturation discipline. It does **not** require identical medium, patina, composition, or color grading. For each scene choose the best Chinese-art branch for the verse, such as freehand ink landscape, gongbi bird-and-flower, colored figure-and-horse painting, blue-green landscape, boneless wash, xuan paper, silk, album-leaf framing, or handscroll depth. Let the poem's arc be visible through both color and visual grammar.

Before generation, assign each scene a distinct style lane and composition skeleton. Adjacent scenes should share enough line quality, period detail, or pigment restraint to feel like one film, but should not look like the same template with swapped subjects.

## Scene ledger

For every scene record:

- Assigned line or consecutive line pair.
- Literal visible nouns.
- One dominant action.
- Foreground, middle ground, distance, and sky.
- Emotional job in the full poem.
- Motifs forbidden because they belong to another scene.

## Still prompt pattern

```text
Use case: historical-scene / illustration-story
Asset type: 9:16 initial frame for classical-poetry I2V, scene N of TOTAL
Input image: style reference only; preserve medium, patina, palette, detail density, and atmospheric depth; do not copy its composition or subjects
Poem context: title, poet, era, whole-poem arc
Assigned lines: exact text
Literal imagery: only imagery assigned to this scene
Dominant visual event: one event
Depth layers: foreground / middle ground / distance / sky
Composition: reserve a safe typography zone for two vertical text columns, but vary its exact surrounding geometry and avoid cloning the same left-subject/right-empty layout in every scene
Shared style anchor: paste the fixed anchor verbatim
Lighting and palette: poem-driven scene-specific light, medium, and accent pigments; preserve Chinese-series coherence without cloning the previous scene's color grade or material
Constraints: no generated text, no calligraphy, no watermark, no modern objects, no fantasy effects, accurate anatomy and period details
Forbidden spillover: list motifs reserved for other scenes
```

## Motion prompt pattern

```text
Animate the attached image as a restrained 9:16 Chinese painting brought subtly to life. Keep the camera locked and preserve the exact composition, subjects, anatomy, architecture, colors, brushwork, surface texture, red seal, and typography negative space. Treat architecture, tree trunks, shorelines, body torsos, and the horizon as static anchors. Animate only one dominant existing action plus one or two small supporting natural actions. Generate synchronized location ambience with no spoken dialogue and no music. During the final second, let residual motion settle into a near-still endpoint. Do not add or remove people, animals, birds, buildings, boats, flowers, text, calligraphy, logos, seals, or landmarks. No count changes, detached foliage, decorative cloud conversion, morphing, duplicated anatomy, camera movement, composition reset, fantasy glow, or style change. Output a finished vertical video with its original generated audio.
```

Default to a locked camera rather than a push-in. The source painting is a fixed plate, not a scene to re-stage. Divide the prompt into four parts:

1. **Static anchors:** name the architecture, tree trunks, shorelines, body torsos, negative-space typography zone, and red seal that must not move or be redrawn.
2. **Localized motion zones:** assign only one dominant action plus one or two supporting ambient actions. State the spatial region and a small displacement limit where useful.
3. **Settled ending:** reserve the final 0.8–1.2 seconds for residual motion to calm naturally so a dissolve has a stable endpoint.
4. **Anti-hallucination constraints:** prohibit composition reset, new silhouettes, detached foliage, subject-count changes, decorative cloud conversion, anatomy replacement, and camera motion.

Avoid asking several subjects to travel across the frame. Long translations often cause the video model to reconstruct the painting. Prefer anchored motion: a wingbeat around the same body center, a beak dip and lift, one hoof weight shift, willow fronds oscillating while remaining attached, ripples expanding from an existing contact point, or mist changing density without crossing or covering fixed architecture.

Recommended motion-prompt core:

```text
Create a 10-second image-to-video animation from this exact source painting. LOCKED CAMERA: no zoom, push, pan, tilt, roll, reframing, parallax, crop change, or scene transition. Treat the source as a fixed painted plate. Preserve the first-frame composition throughout; static anchors must remain pixel-stable and must never be repainted, moved, duplicated, mirrored, enlarged, or replaced.

Animate only these localized existing elements: [one dominant anchored action], supported by [one or two small ambient actions]. Keep every moving subject attached to its original body center, branch, ground plane, shoreline, or water contact point unless a short displacement is explicitly assigned. During the final second, let residual motion settle into a calm near-still endpoint.

Generate synchronized natural ambience, no speech and no music. Do not add or remove any subject. No count changes, morphing, detached leaves, new silhouettes, decorative cloud shapes, invented text, camera motion, composition reset, or style change.
```
