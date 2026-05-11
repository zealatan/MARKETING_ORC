# MARKETING_ORC

Interactive marketing and visualization assets for RF, antenna, wireless communication, and AI-orchestrated technical demos.

This repository currently hosts an interactive 3D antenna radiation pattern UI:

> **UPA Pencil Beam Explorer**  
> A professional, browser-based 3D visualization of a UPA pencil-beam radiation pattern with patch/HFSS-like coloring and interactive steering controls.

---

## Interactive Antenna UI Demo

### Open the Demo

If GitHub Pages is enabled for this repository, open:

[Launch Interactive Antenna UI](https://zealatan.github.io/MARKETING_ORC/upa_pencil_beam_slider_interactive_patch_hfss_pattern.html)

If this repository also contains an `index.html` copy of the demo file, the shorter URL will work:

[Launch Demo Home](https://zealatan.github.io/MARKETING_ORC/)

---

## Demo File

The main HTML demo file is:

```text
upa_pencil_beam_slider_interactive_patch_hfss_pattern.html
```

You can also open it directly from the repository:

[Open HTML Demo File](./upa_pencil_beam_slider_interactive_patch_hfss_pattern.html)

---

## What This Demo Shows

This antenna UI visualizes a professional 3D radiation pattern for a uniform planar array.

Main features:

- Interactive 3D radiation pattern
- UPA pencil-beam visualization
- Patch/HFSS-like radiation model
- HFSS-style color palette
- Beam steering control using θ and φ sliders
- Adjustable array size
- Adjustable element spacing
- Adjustable dB floor
- PNG export button
- Full 3D mouse interaction: rotate, zoom, reset camera

---

## Local Preview

To preview the HTML demo locally:

```bash
cd ~/MARKETING_ORC
python3 -m http.server 8000
```

Then open this URL in a browser:

```text
http://localhost:8000/upa_pencil_beam_slider_interactive_patch_hfss_pattern.html
```

If you copied the HTML file to `index.html`, you can simply open:

```text
http://localhost:8000/
```

---

## Recommended Repository Structure

Recommended structure:

```text
MARKETING_ORC/
├── README.md
├── index.html
└── upa_pencil_beam_slider_interactive_patch_hfss_pattern.html
```

The long HTML filename is useful as the original descriptive demo file.

The `index.html` file is useful for GitHub Pages because it allows a clean demo URL:

```text
https://zealatan.github.io/MARKETING_ORC/
```

To create `index.html` from the existing demo file:

```bash
cp upa_pencil_beam_slider_interactive_patch_hfss_pattern.html index.html
```

---

## Enable GitHub Pages

To publish the interactive HTML demo:

1. Go to the GitHub repository page.
2. Open **Settings**.
3. Open **Pages**.
4. Set source to **Deploy from a branch**.
5. Select:
   - Branch: `main`
   - Folder: `/root`
6. Click **Save**.

After GitHub Pages is deployed, the demo should be available at:

```text
https://zealatan.github.io/MARKETING_ORC/
```

or:

```text
https://zealatan.github.io/MARKETING_ORC/upa_pencil_beam_slider_interactive_patch_hfss_pattern.html
```

---

## Push Commands

From the local workspace:

```bash
cd ~/MARKETING_ORC

rm -f *:Zone.Identifier

cp upa_pencil_beam_slider_interactive_patch_hfss_pattern.html index.html

git add README.md index.html upa_pencil_beam_slider_interactive_patch_hfss_pattern.html
git commit -m "Add interactive UPA antenna radiation pattern demo"
git push
```

---

## Project Direction

This repository can be used as a marketing/demo layer for technical visualization assets.

Possible future demos:

- ULA beam pattern explorer
- UPA beam steering explorer
- mmWave beamforming visualizer
- RFSoC/FPGA system architecture visualizer
- AI Orchestrator workflow visualizer
- Paper-to-product technical demo landing page

The goal is to turn technical work into clear, visual, and shareable web-based demos.

---

## Current Demo Summary

| Item | Description |
|---|---|
| Demo name | UPA Pencil Beam Explorer |
| Main file | `upa_pencil_beam_slider_interactive_patch_hfss_pattern.html` |
| Recommended entry file | `index.html` |
| Visualization type | Interactive 3D radiation pattern |
| Main technology | HTML + JavaScript + Plotly |
| Use case | Antenna/RF/mmWave technical demo |
| Best hosting method | GitHub Pages |

---

## License

This repository is currently a personal technical demo repository.

Add a license file later if the project will be distributed publicly or reused by others.
