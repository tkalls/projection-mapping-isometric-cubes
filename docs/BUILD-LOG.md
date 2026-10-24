# corner — lab brief

Bedroom corner: ceiling + left wall + right wall. Three planes, three creases, one vertex where
all three meet. HY300 again. Sibling to PROJECTOR.md, REFRACT.md and BRIEF.md.
Written 2026-10-23 while Tobi watched a movie. TouchDesigner was not opened.

---

## 1. What a three-plane corner actually is

A concave trihedral corner is the inside of a cube seen from within: three faces at 90°, three
creases, one vertex. Last session's crease (two planes) gave one fold. This gives a full 3D
reference frame, and that changes two things:

1. **Every face has a different real normal.** Light the scene with a virtual lamp and each face
   gets a different brightness (Lambert: `brightness = max(dot(N, L), 0)`). The room shades
   itself like a 3D object, and it looks right from anywhere in the room.
2. **It is the ideal shape for projector calibration.** camSchnappr needs 6+ known 3D points that
   are not all on one plane. A corner gives you three axes for free: the vertex is the origin and
   each crease is an axis.

The corner can also be read two ways (Michael Bach's "missing corner" illusion). The same three
lines read as a room corner going IN or a cube corner poking OUT. Draw the other edges of a cube
around the creases and the brain flips the corner into a solid cube. That is a free illusion.

## 2. Two modes of mapping (know which one you're in)

| | Surface-true | Viewpoint-true (anamorphic) |
|---|---|---|
| Looks right from | anywhere | one eye or lens only |
| Needs | the 3 faces mapped (Kantan quads are enough) | a measured room model + calibrated projector + known viewer position |
| Good for | the live room, music, people walking around | VIDEO. A phone on a tripod IS the single eye |
| Examples | edge pulses, virtual lighting, colour relay, chrome sheen on the faces | a chrome cube floating in the corner, walls "opening" into a deeper room |

**Bot & Dolly's "Box" lesson:** their whole film was captured in-camera with no post. The 3D
illusion only works from the lens position, so they locked the camera. For your recordings, lock
the phone on a tripod and render the virtual scene from where the phone is.

**The trap:** if the viewer stands where the projector is, every image looks flat and undistorted
whatever surface it lands on. The projector's own viewpoint can never see the trick. Put the phone
somewhere else, ideally centred on the corner at eye height.

## 3. Light, black and contrast: the physics

You cannot project black. Black is the room's own light plus the projector's leak. Four separate
problems:

### 3a. Ambient light
- Kill every source: door gap, router and charger LEDs, the laptop screen. Turn the laptop away
  from the corner or set its brightness to 0; it lights the walls more than you'd think.
- Research on projection mapping under room light: ambient light raises the dark areas globally,
  and contrast collapses. Lumens do not fix it. Only darkness does.

### 3b. Projector leak (the HY300 specifically)
- It is an LCD projector. An LCD panel sending "0" still leaks light, so the whole frame shows as
  a faint grey rectangle.
- **Digital fix:** a black-crush on the final output. Values under ~2–3% go to exactly 0 so the
  panel's near-black noise doesn't shimmer. In TD that is a Level TOP on the output with
  `blacklevel` ≈ 0.02–0.03.
- **Physical fix (the old theatre trick):** a matte-black card in front of the lens, cut into
  roughly the silhouette of the corner area. Close to the lens it is out of focus, so it gives a
  soft-edged mask that kills the grey rectangle wherever there's nothing to show. Cardboard and
  black tape, no money.

### 3c. Inter-reflection (the corner-specific one)
- A concave corner lights itself. Light bouncing off one wall lands on its neighbour.
- For two equal squares that share an edge at 90°, the radiative form factor is ≈ 0.20, so ~20%
  of what leaves face A lands on face B. With white paint (albedo ~0.8), a fully white left wall
  lifts the right wall's "black" by roughly 16% of the left wall's brightness.
- **Design rule:** don't fill two adjacent faces bright at the same moment. Alternate:
  bright / dark / bright. That gives maximum contrast, and the 3D reads stronger because adjacent
  faces always differ (the colour relay from last night already obeys this).
- Keep the **average picture level** low: thin lines, sparse highlights, chrome streaks on black.
  The less total light in the room, the deeper every black.

### 3d. Uneven brightness across faces (cosine and inverse-square)
- Illuminance on a face ∝ `cos(incidence angle) / distance²`.
- A projector low on a table hits the ceiling at a grazing angle. At 70° incidence, cos 70° ≈ 0.34,
  so the ceiling gets about a third of the light per area that a face hit square-on would.
- You can't make the dim face brighter (it's already at 1.0), so **dim the bright faces to match**:
  a per-face gain.
- **Measure, don't guess:** project pure white on all three faces, lock the phone camera's exposure,
  take one photo, and read each face's brightness. Set the gains so the faces match, or
  deliberately don't match if the design wants a lit side and a shadow side.
- Placement guidance from mapping guides: put the projector 30–45° off-axis and slightly above, so
  it sees all faces. Past ~60° faces stretch and dim badly. A smaller image is brighter:
  brightness ∝ 1/area.
- Projector menu: keystone OFF, any "dynamic contrast", "sharpness" or "motion smoothing" OFF.
  Focus on a sharp edge, then never touch the projector again; any nudge means re-mapping.

## 4. Chrome: why it suits a dim projector, and three ways to make it

Chrome is almost entirely black, with thin, very bright highlight streaks. That is exactly what a
weak projector does best: low average picture level and high local contrast.

Chrome is reflection only. With no environment, metal reads flat grey. The look comes from WHAT it
reflects: a few hard bright strips on black (a "studio softbox" environment) give the classic
liquid-chrome streaks.

**A. PBR MAT + Environment Light COMP (true 3D).** Metallic 1, roughness 0.03–0.12, and an
Environment Light COMP fed by an equirectangular environment. Build the environment as a GLSL TOP
(black with 3–5 white bars) rather than a photo HDRI, because a photo gives muddy reflections.
The geometry needs normals and tangents: Attribute Create SOP.

**B. Raymarched rounded cube in a GLSL TOP (my pick for the cube).** No geometry at all. The cube
is a signed distance function, reflections are computed per pixel, and the edges get a real bevel
radius. The bevel is where chrome sings: a sharp cube has no bevel to catch light, while a rounded
edge throws a continuous highlight line. Costs one full-screen shader at 1280×720, which is cheap.

**C. Matcap (cheapest).** Turn the view-space normal into a UV on a painted "chrome sphere" image.
Highlights don't move with the light, so animate by rotating the matcap lookup. Good for
lots of small chrome objects.

**Chrome on the walls themselves (surface-true variant):** treat each real face as a mirror with
its real normal. Reflect a rough view direction off it and look up the strip environment. The
sheen slides continuously across a face and **breaks direction exactly at each crease**, which
makes the creases pop. This needs no calibration.

## 5. Design concepts for the lab (pick one or two per session)

1. **Crease pulse (Lemercier / Valbuena school).** Only the three creases and the vertex glow; the
   faces stay black. On each kick a pulse races along all three creases into the vertex, and on
   the snare it bursts back out. Lowest light level possible, so maximum contrast. The best first
   build.
2. **Virtual lamp.** A light orbits inside the corner. Each face shades by its real normal, and
   virtual objects in the room cast soft shadows onto the real walls. Surface-true. Pablo
   Valbuena's "Augmented Sculpture" is this idea: a physical layer plus a projected virtual light
   layer.
3. **Corner flip (Necker cube).** Draw the six missing edges of a cube that shares the real vertex,
   in chrome or white line. From the tripod the room corner flips into a solid cube poking OUT of
   the room. Animate the cube's size breathing with the bass so it inflates out of the wall.
   Viewpoint-true.
4. **Chrome cube in the corner.** The raymarched rounded chrome cube "sitting" in the corner,
   rotating slowly, reflecting strip lights, its reflections smeared across all three walls from
   the tripod's view. The flagship video piece. Viewpoint-true, needs calibration.
5. **Opening the walls.** Each face shows a receding grid or tunnel as if the wall were a window
   into a deeper box, so the corner becomes the mouth of a bigger room. Viewpoint-true.
6. **Colour relay (last night's piece), three-way.** Ceiling → left → right, with neighbours never
   matching. Already built: it just needs a third face.

## 6. Music: getting real beats instead of loudness

Last session's `aud_lvl` / `aud_bass` were loudness envelopes, so everything breathed with the
volume. For punchy reactions you want **onsets**: the instant a hit starts.

**Built-in:** the `audioAnalysis` palette component gives low/mid/high levels plus kick, snare and
rhythm channels (0/1 pulses) and spectral centroid. Known bug from the forum: the top-level
Active toggles for kick, snare and rhythm weren't bound to the inner components, so turn on
Active inside the sub-component.

**Hand-built kick detector (worth building once to learn it):**
```
audiodevicein → audiofilter (lowpass ~110 Hz) → analyze (RMS power)  = fast
                                              → lag (~1.5 s)          = slow, the recent average
kick when  fast > slow × 1.4  AND  fast > floor          (adaptive threshold, ignores volume changes)
→ trigger CHOP (attack 0.005, decay ~0.25 s)  = a clean 0→1→0 envelope per kick
```
Same pattern for the snare with a bandpass around 1.5–4 kHz, and hats above 8 kHz.

**Mapping music to the corner** (one role per band, so it reads clearly):
- kick → crease pulse / cube scale punch
- snare → swap which face is lit
- hats → sparkle on the chrome highlights
- low band level → chrome cube rotation speed
- spectral centroid → brightness of the reflected environment

Cleaner audio: route the Mac's output through BlackHole, which is already installed, into TD
instead of the mic. It's sharper, with no room noise; set up a Multi-Output Device in Audio MIDI
Setup so you still hear it.

## 7. Running smoothly (lessons paid for in crashes)

- **Fresh file: `corner.toe`**, not mapping.toe. mapping.toe now carries ~5M particles' worth of
  networks. Import `mcp_webserver_base.tox`, and keep the file directly in `~/TD-Lab` next to
  `modules/`.
- **Native canvas 1280×720.** It matches both the HY300 panel and the Non-Commercial cap.
- **Build one node per call**, ~1.5 s apart. Multi-node exec calls crashed TD three times.
- **Save after every working step.** `project.save()` from the bridge worked at the end of the last
  session, and Cmd+S always works.
- **Perform mode** (F1) for recording: TD stops drawing its editor UI.
- **Diagnose before optimising:** Performance Monitor (alt+y). If dropping the render resolution
  to 64×64 speeds things up, it's GPU-bound.
- Only one bloom pass, at half or quarter resolution.
- Anything not on screen must not cook: disconnect it or turn off its viewer.
- While a movie is playing: don't open TD at all (you said so).

## 8. Code sketches (to drop in when TD is open)

### 8a. Per-face virtual lighting (surface-true; one shader, face id as uniform)
```glsl
// face: 0 ceiling, 1 left wall, 2 right wall. Inward-facing normals of the corner.
uniform vec4 uP;      // x time, y kick, z bass
uniform vec4 uF;      // x face id, y gain (per-face brightness match)
out vec4 fragColor;
vec3 faceN(int f){ return f==0 ? vec3(0,-1,0) : (f==1 ? vec3(1,0,0) : vec3(0,0,1)); }
void main(){
  vec2 uv = vUV.st;
  int f = int(uF.x + 0.5);
  vec3 L = normalize(vec3(sin(uP.x*0.4), -0.6, cos(uP.x*0.4)));   // orbiting lamp inside the corner
  float lam = max(dot(faceN(f), -L), 0.0);
  // crease glow: uv edge 0 is the shared crease on each face (set up the quads that way)
  float crease = exp(-min(uv.x, uv.y)*120.0) * (0.3 + 1.7*uP.y);
  vec3 c = vec3(lam*0.6) + vec3(1.0)*crease;
  fragColor = TDOutputSwizzle(vec4(c*uF.y, 1.0));
}
```

### 8b. Raymarched rounded chrome cube (GLSL TOP, viewer camera in room coordinates)
```glsl
// Room frame: vertex at origin, +x along the right-wall/ceiling crease, +z along the
// left-wall/ceiling crease, -y down the wall/wall crease. Units: metres.
uniform vec4 uCam;    // xyz viewer (phone) position, w time
uniform vec4 uCube;   // xyz cube centre, w half-size
uniform vec4 uA;      // x bevel radius, y spin, z kick, w exposure
out vec4 fragColor;
float sdRoundBox(vec3 p, vec3 b, float r){ vec3 q = abs(p) - b; return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0) - r; }
mat3 rotY(float a){ float c=cos(a), s=sin(a); return mat3(c,0,-s, 0,1,0, s,0,c); }
float map(vec3 p){ p = rotY(uCam.w*uA.y) * (p - uCube.xyz); return sdRoundBox(p, vec3(uCube.w*(1.0+0.08*uA.z)), uA.x); }
vec3 nrm(vec3 p){ vec2 e = vec2(1e-3, 0); return normalize(vec3(map(p+e.xyy)-map(p-e.xyy), map(p+e.yxy)-map(p-e.yxy), map(p+e.yyx)-map(p-e.yyx))); }
vec3 env(vec3 d){               // studio: black with hard white strips = liquid chrome streaks
  float s = smoothstep(0.985, 1.0, abs(sin(d.y*7.0 + 0.6*sin(d.x*2.0))));
  float top = smoothstep(0.6, 0.95, d.y);
  return vec3(s*1.4 + top*0.9);
}
void main(){
  // build the view ray for this pixel from a camera looking at the vertex (refine with real FOV later)
  vec3 ro = uCam.xyz, ta = vec3(0.0, -0.3, 0.0);
  vec3 fw = normalize(ta - ro), rt = normalize(cross(fw, vec3(0,1,0))), up = cross(rt, fw);
  vec2 q = (vUV.st - 0.5)*vec2(1280.0/720.0, 1.0);
  vec3 rd = normalize(fw*1.6 + rt*q.x + up*q.y);
  float t = 0.0; bool hit = false;
  for (int i = 0; i < 96; i++){ float d = map(ro + rd*t); if (d < 1e-4){ hit = true; break; } t += d; if (t > 20.0) break; }
  vec3 c = vec3(0.0);
  if (hit){
    vec3 p = ro + rd*t, n = nrm(p);
    vec3 r = reflect(rd, n);
    float fres = 0.6 + 0.4*pow(1.0 - max(dot(-rd, n), 0.0), 3.0);
    c = env(r)*fres;
  }
  fragColor = TDOutputSwizzle(vec4(c*uA.w, 1.0));
}
```
This renders what the PHONE should see. Section 8c puts it onto the real walls correctly.

### 8c. Viewpoint-true pipeline (projective texturing)
1. Model the room: three big Rectangle SOPs (ceiling, left wall, right wall) meeting at the origin,
   in metres from tape measurements.
2. Calibrate the projector with **camSchnappr** (Palette → Mapping) against that model: click 6+
   points (the vertex plus 2–3 marks along each crease at measured distances). It solves the
   projector's position, rotation and lens. Projector digital keystone and zoom must be off/reset.
3. A `viewer` Camera COMP sits at the phone's measured position, looking at the vertex.
4. Render the virtual scene (8b, or real geometry) from `viewer` → texture `sScene`.
5. Render the ROOM MODEL from the calibrated projector camera, with a material that looks each
   point up in `sScene` through the viewer's eyes:
```glsl
// vertex (GLSL MAT on the room model)
uniform mat4 uViewerVP;            // viewer projection * inverse(viewer world transform)
out vec4 vViewerClip;
void main(){ vec4 wp = TDDeform(P); vViewerClip = uViewerVP*wp; gl_Position = TDWorldToProj(wp); }
// pixel
uniform sampler2D sScene; uniform vec4 uGain; in vec4 vViewerClip; layout(location=0) out vec4 fragColor;
void main(){ vec2 uv = vViewerClip.xy/vViewerClip.w*0.5 + 0.5; fragColor = TDOutputSwizzle(vec4(texture(sScene, uv).rgb*uGain.x, 1.0)); }
```
   `uViewerVP` comes from Python each frame (`viewer.projection(w,h) * viewer.worldTransform` inverted;
   verify the exact TD calls in-session). The projector then throws light that, seen from the
   phone, assembles into the floating cube.

## 9. Lab session plan

**Before TD (no CPU needed):**
- Darken the room. Find every LED.
- Tape measure: from the vertex, mark points on each crease at 30 / 60 / 90 cm (painter's tape,
  small dots). These are the calibration points.
- Decide projector and tripod positions, and photograph both. The projector must not move after
  mapping.
- Photo of the corner with the projector showing a plain white image (the brightness and spill
  check from 3d).

**In TD:**
1. `corner.toe`, MCP tox, 1280×720 output window on display 1, black-crush Level TOP on the output.
2. Three Kantan quads (ceiling / left / right) all sharing the vertex point. That's the
   surface-true layer, built in 10 minutes.
3. **Concept 1, crease pulse, plus the hand-built kick detector.** Learn onsets.
4. **Concept 2, virtual lamp, with per-face gains** set from the white-photo measurement.
5. Room model + camSchnappr calibration → **concept 4, chrome cube**, filmed from the tripod.

**Things to bring back:** the reference photos, the corner measurements (the three crease lengths
visible in the projection), and where the projector and phone will sit.

## Sources
- Lazy Lighting — first 3D projection mapping guide (corner = inside-out box; 30–45° off-axis; vary each face; respect gravity; seam checking): https://lazylighting.com/en/blog/creating-your-first-3d-projection-mapping
- garageCube forum — projecting a box across floor + two walls only works from one viewpoint: https://forum.garagecube.com/viewtopic.php?t=8711
- Michael Bach — "Missing Corner" cube illusion: https://michaelbach.de/ot/sze-missCornerCube/
- Derivative — camSchnappr: https://derivative.ca/UserGuide/Palette%3AcamSchnappr
- Derivative — Projection Mapping overview: https://docs.derivative.ca/Projection_Mapping
- Mirror Pillar — anamorphic corner method (correct only from the projector/eye position): https://mirrorpillar.nfshost.com/downloads/Anamorphic%20Projection%20Activities.pdf
- UCSB CS291A — off-axis projection for head-tracked windows: https://sites.cs.ucsb.edu/~holl/CS291A/Assignments/Assignments-3/Assignment3VRPortal.html
- Stanford EE368 — perspective-corrected projection on a wall corner: https://web.stanford.edu/class/ee368/Project_Autumn_1516/Reports/Lin_Wang_Chen.pdf
- Motionographer — Bot & Dolly "Box" behind the scenes (in-camera, single lens): https://motionographer.com/2013/10/01/bot-dolly-box-interview-and-behind-the-scenes
- arXiv 2403.02547 — projection mapping under environmental lighting (ambient light kills dark areas): https://arxiv.org/pdf/2403.02547
- HeavyM — choosing a projector (lumens vs room darkness): https://www.heavym.net/choose-your-projector/
- Lightform — picking a projector (contrast ratio; projectors can't project darkness): https://lightform.com/blog/lightform-compatible-projector-how-to-pick-a-projector
- AVFX — projection mapping best practices: https://www.avfx.com/2019/11/projection-mapping-best-practices/
- Derivative Learn — PBR in TouchDesigner (Environment Light COMP, tangents): https://learn.derivative.ca/courses/100-fundamentals/lessons/104-rendering-3d-scenes/topic/physically-based-rendering/
- Derivative — PBR MAT: https://derivative.ca/UserGuide/PBR_MAT
- clicktorelease — spherical environment mapping / matcap math: https://clicktorelease.com/blog/creating-spherical-environment-mapping-shader
- Derivative — audioAnalysis palette: https://derivative.ca/UserGuide/Palette:audioAnalysis
- Derivative forum — audioAnalysis kick/snare/rhythm Active toggle bug: https://forum.derivative.ca/t/audio-analysis-not-detecting-kick-snare-and-rhythm/293931
- Interactive & Immersive HQ — making anything audio reactive: https://interactiveimmersive.io/blog/touchdesigner-lessons/how-to-make-anything-audio-reactive-in-touchdesigner/
- Derivative — Optimize: https://derivative.ca/UserGuide/Optimize
- Derivative — Performance Monitor: https://derivative.ca/UserGuide/Performance_Monitor
- Augmented Sculpture (Pablo Valbuena) — physical layer + projected virtual layer: https://we-make-money-not-art.com/what_is_your_ba_1/
- CDM — AntiVJ / Joanie Lemercier, light revealing geometry: https://cdm.link/plays-of-shadow-and-light-into-digital-topography-new-antivj-work/

---

## 10. Reference techniques (Tobi's 11 GIFs, ~/Desktop/corner-refs, 2026-10-23)

The refs are not chrome or cubes. They are a GRAPHIC-STYLE mood board, and the common thread is
**retro display artifacts + limited palettes + print textures + line art + human figures**. Each
one, and how to build it in TD:

| # | File | What it is | Technique(s) |
|---|---|---|---|
| 1 | 4CF4559F | crowds walking; blue-on-blue, then green-black on acid yellow | **duotone gradient map**, luminance **inversion**, ghosted figures (**frame echo**), grain |
| 2 | 11097150 | blue TV static | **tinted noise** as a texture / beat transition |
| 3 | FC03AA60 | face on a curved old TV, neon wireframe city over it, red vs cyan | **CRT barrel distortion + rounded vignette**, scanlines, **RGB split**, line-art overlay, complementary pair |
| 4 | B05C52E4 | dancer in 1-bit-ish magenta/green/white | **ordered (Bayer) dither**, 3-colour palette, moiré lines |
| 5 | 7DB4D773 | archival animal-eye close-ups with VHS "TCR … PLAY LOCK" | **found-footage cut on the beat**, **VCR on-screen text**, tape grain |
| 6 | 03A59589 | two silhouettes counter-orbiting a glowing sun, red rings | **radial composition**, rotational symmetry, **ring bursts on hits**, glow |
| 7 | E35BCA98 | 60s liquid light show: colour blobs, film-gate edges | **metaballs / fluid blobs**, gradient map, analog film frame |
| 8 | 47CF14FD | letter "W" made of horizontal slices twisting like a ribbon | **slit-scan / per-row offset** (each scanline shifted by `sin(y + t)`), ribbon shading by `|cos|`, bloom |
| 9 | A8C9385C | Spider-Verse: Miles mid-swing | **halftone / Ben-Day dots**, **misregistered print** (chromatic offset), bold palettes, **stepped "on twos" animation** |
| 10 | C2A05EF9 | spider logo re-rendered in a new style every beat | **style switch on the beat**, offset print, halftone, flat → chrome → dots |
| 11 | 8F7E15AC | wireframe map lines, red/blue doubled, on a curved screen | **plexus** (points joined by lines when near), **RGB-split line art**, CRT curve |

### Translating them for a PROJECTOR (the big caveat)
Several refs are full-frame bright (01's yellow, 06's orange). On a wall corner that becomes a
lit room: ~20% inter-reflection washes every face (section 3c). **Rule: the darkest stop of every
palette is pure black.** Duotone becomes black → colour A → colour B, never colour → colour.

The good news: **dither, halftone, line art and plexus are the most projection-friendly looks
there are.** Pixels are either fully on or fully off, the average light level stays low, and
blacks stay black. That suits an LCD projector exactly.

### Recipes
- **Gradient map / duotone (01, 07):** Lookup TOP. Input = luminance (Monochrome TOP), lookup = a
  1D Ramp TOP (black → deep colour → bright colour). Changing the ramp re-colours everything.
- **RGB split (03, 9, 10, 11):** one GLSL line:
  `c = vec3(tex(uv+o).r, tex(uv).g, tex(uv-o).b);` with `o` kicked by the snare.
- **CRT (03, 11):** barrel `uv' = c + d*(1 + k*dot(d,d))` where `d = uv - 0.5`; scanlines
  `*= 0.8 + 0.2*sin(uv.y*π*rows)`; rounded-rectangle SDF vignette.
- **Ordered dither (04):** 4×4 Bayer matrix threshold, then snap to a 3-colour palette (black,
  magenta, green). Lock the dither to the projector's pixel grid (gl_FragCoord), never to uv,
  or it swims.
- **Halftone (9, 10):** dot grid; dot radius ∝ √(luminance); rotate the grid per channel
  (15°/45°/75°) for print misregistration.
- **Slit-scan ribbon (08):** per row `x' = x + A*sin(y*f + t)` and horizontal scale `cos(phase)`,
  brightness `|cos|`. Any glyph from the letter sheet becomes a twisting ribbon.
- **Frame echo (01):** Feedback TOP → Level (opacity ~0.85) → Composite "maximum" with the new frame.
- **Liquid light (07):** 6–10 metaballs (smooth-min of circle SDFs) drifting on noise, then the
  gradient map, plus a film-gate border.
- **Orbit + ring burst (06):** polar coordinates; ring = `exp(-abs(r - R(t))*k)` with R growing
  from 0 on each kick.
- **Plexus (11):** ~40 drifting points; a line between any pair closer than d, alpha `1 - dist/d`.
  O(N²) per pixel in a GLSL TOP is fine at N≈40, or use a Line MAT over a SOP for larger N.
- **Stepped animation (09):** hold every other frame (Cache TOP / time quantised to 1/12 s).
  Snaps motion into "comic" rhythm.
- **Style switch (10):** a Switch TOP over 4–6 treatments, index = Count CHOP on the kick
  detector.
- **VCR overlay (05):** Text TOP, Menlo, white on a black box, timecode from `absTime.frame`.
- **Static transition (02):** Noise TOP (seed animated per frame) through a blue gradient map,
  flashed for 2–3 frames on a big hit.

### Content source: figures
The refs keep returning to human figures (01, 04, 06, 09). There's no footage library, but
**TD-Lab already has MediaPipe**. A live webcam silhouette of Tobi (selfie segmentation mask) fed
through these treatments gives dithered and duotone figures that are his own, with no rights
issues. Don't reuse the Spider-Verse or archival footage itself: technique yes, frames no.

### Corner concepts built from the refs
- **A. Three Screens.** Each face is an old curved TV (CRT barrel + vignette), and each runs a
  different treatment from the board: left = dither, ceiling = plexus line art, right =
  halftone. On the kick, all three shift style (ref 10). The creases become the bezels between
  three screens, so the 3D comes from three different "devices" meeting.
- **B. Walker across the corner.** A webcam silhouette, duotone and frame-echoed (ref 01), walks
  off the left wall, through the vertex and onto the right wall, while the ceiling holds a slow
  radial sun with ring bursts on the kick (ref 06).
- **C. Plexus room.** Plexus points live on all three faces in room coordinates, so lines connect
  ACROSS the creases. A line that bends at a crease shows the 3D fold. Red/blue split (ref 11) on
  black: lowest light, highest contrast.
- **D. Liquid light in the corner.** Metaball blobs (ref 07) that flow down the walls with gravity
  and pool along the creases, a black-based gradient map per face, and a film-gate edge on each face.

---

## 11. THE GOAL: a perfect cube from three faces + clip playback

### 11a. Why "perfect cube" is a measuring job, not an eyeballing job
The corner already IS the inside of a cube: three planes at 90°. To make it read as a perfect
cube, the three mapped faces must be **equal squares that share the vertex**. Projector angle
doesn't matter, because a square marked on the wall IS a square, whatever the projector sees.
So: **mark the squares physically with tape, then drag the Kantan corners onto the tape.**

Marking (side length L, start with L = 50 cm and grow until it no longer fits the beam):
1. The vertex V (where ceiling, left and right meet).
2. On each crease, a mark at distance L from V. That's three marks: A (left wall / ceiling
   crease), B (right wall / ceiling crease), C (down the wall/wall crease).
3. Each face's far corner:
   - ceiling far corner = L from A and L from B (or √2·L ≈ 1.414·L from V)
   - left wall far corner = L from A and L from C
   - right wall far corner = L from B and L from C
   **Fastest method:** cut a cardboard square of side L, put one corner on V, lay it flat on each
   face and mark the opposite corner. Seven tape dots in total.
4. Kantan: three quads (Ceiling, Left, Right), each with one corner on V and its edges on the
   creases. With Show Guides on, drag the corners onto the tape dots, watching the wall.

### 11b. The magic viewpoint: the room's diagonal
From a point on the cube's main diagonal, looking straight into V, the three equal squares show
as a **perfect regular hexagon split into three rhombi**: the classic isometric cube drawing. The
brain can then read it either way: a room corner going in, or a solid cube coming out (the Necker
flip from section 1).

The diagonal points away from the ceiling corner at 45° between the two walls, angled down at
**35.26° below horizontal** (`atan(1/√2)`). For a phone at distance D from V:
- horizontal distance out from the corner: **0.816 × D** (along the 45° line between the walls)
- height below the ceiling: **0.577 × D**
- example: D = 2.5 m → **2.04 m out, 1.44 m below the ceiling** (≈ 1.26 m off the floor with a
  2.7 m ceiling)

**Bonus physics:** put the PROJECTOR near the same diagonal and it hits all three faces at the
same 54.7° incidence (cos = 1/√3), so all faces get equal brightness and no per-face gain is
needed. Projector and phone can't share the exact spot; put the projector just below or beside
the phone.

### 11c. Clip playback mode ("the images as video")
Clips: `~/TD-Lab/corner_clips/`. These are Tobi's 11 GIFs, centre-cropped to 720×720 squares
(cube faces are squares) and stored as H.264 MP4, short seamless loops of 0.2–5 s:
`01_crowd_duotone · 02_blue_static · 03_crt_face · 04_dither_dancer · 05_vhs_eyes ·
06_orbit_sun · 07_liquid_light · 08_ribbon_w · 09_spiderverse · 10_spider_styles · 11_plexus_map`

Network (one chain per face, three in total):
```
Folder DAT (corner_clips/*.mp4) ─┐
                                 ├─ face_N_clip  Movie File In TOP (file = list[assign[N]], play, loop)
                                 │      └─ face_N_twist  GLSL TOP: optional treatment, mix 0..1
                                 │            (black-crush, duotone remap, RGB split on snare, CRT curve)
                                 │                  └─ Kantan quad N (Ceiling / Left / Right)
controls: Shuffle (pulse) · Auto Shuffle (s) · Stagger (s) · Twist mix · Face gains
```
- **Assignment** = a 3-number list (which clip on which face). Shuffle = random pick of 3 distinct
  clips. Keep a small "favourites" table: when an order looks right, press Keep and it's logged
  with a timestamp, so we can compare orders afterwards.
- **"A different image at a different time"** = the **Stagger**: faces change one after another
  (ceiling, then left, then right), Stagger seconds apart, not all at once. The cube "turns
  over" face by face.
- **On-beat option:** a shuffle step on every Nth kick instead of a timer.
- **Twist mix 0 → 1:** 0 = raw clip, 1 = our treatment. That's our own iterative twist on top of
  the source footage.
- **Projector rules still apply:** some clips are bright full-frame (crowd yellow, orange sun, blue
  static). Put at most ONE bright clip on adjacent faces at a time, or the corner bounces light into
  itself (section 3c). The face gains and black-crush keep each face's "black" black.

### 11d. Order-finding (what makes three clips look good together)
A heuristic to test against your eye:
- **One bright, two dark.** One face carries a bright clip, the other two dark-based ones. This
  gives the strongest 3D, because the faces differ in brightness the way a lit cube's do.
- **Complementary hues across a crease** (blue static next to orange sun) make the crease
  sharpest.
- **Motion direction:** clips that move DOWN (liquid, falling figures) suit the walls; radial or
  orbiting ones (sun, plexus) suit the ceiling.
- **Ceiling candidates:** 06 orbit sun, 11 plexus map, 07 liquid light.
  **Wall candidates:** 04 dither dancer, 01 crowd, 03 CRT face, 09 spiderverse.
  **Accent / transition:** 02 static (flash it on big hits), 08 ribbon W, 10 spider styles.
