# Brand assets

The bundled artwork identifies Autodarts in Home Assistant. It comes from the official Autodarts website, retrieved on 2026-09-18:

- `icon.svg`: <https://autodarts.com/favicon.svg>
- `logo.svg`: <https://autodarts.com/brand/autodarts-logo-colored.svg>

The SVG sources are preserved unchanged. PNG exports live in `custom_components/autodarts/brand/`:

- `icon.png` (256 × 256) and `icon@2x.png` (512 × 512), transparent and shared by both themes through Home Assistant's dark-icon fallback.
- `logo.png` (250 × 60) and `logo@2x.png` (500 × 120), with dark lettering for light themes.
- `dark_logo.png` and `dark_logo@2x.png`, the original white lettering for dark themes, at the same sizes.

The colored symbol and all paths are unchanged; only the light-theme wordmark's white fill is replaced with dark slate. PNG rendering needs no fonts, network access or runtime integration dependency.

To regenerate from the repository root using a separate development environment:

```sh
python3 -m venv /tmp/autodarts-brand-renderer-venv
/tmp/autodarts-brand-renderer-venv/bin/pip install resvg-py==0.5.0
/tmp/autodarts-brand-renderer-venv/bin/python scripts/render_brand.py
```

Home Assistant [supports local custom-integration brand assets from 2026.3](https://developers.home-assistant.io/docs/core/integration/brand_images/). The folder is included in HACS and manual installations. No manifest `icon` property or cloud authorization is needed.

Autodarts and Winmau names and artwork belong to their respective owners and are excluded from this project's MIT license. Their use identifies the supported product and does not imply affiliation or endorsement.
