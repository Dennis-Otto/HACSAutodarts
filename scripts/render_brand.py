"""Export bundled Home Assistant brand PNGs from the official SVG sources.

Development-only dependency: resvg-py==0.5.0. See docs/branding/README.md.
"""

from pathlib import Path

from resvg_py import svg_to_bytes

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "docs" / "branding"
DESTINATION = ROOT / "custom_components" / "autodarts" / "brand"


def main() -> None:
    """Render transparent icons and theme-specific wordmarks at both densities."""
    DESTINATION.mkdir(parents=True, exist_ok=True)
    icon = (SOURCES / "icon.svg").read_text(encoding="utf-8")
    dark_logo = (SOURCES / "logo.svg").read_text(encoding="utf-8")
    light_logo = dark_logo.replace('fill="white"', 'fill="#0f172a"')
    for scale, suffix in ((1, ""), (2, "@2x")):
        for name, source, width in (
            ("icon", icon, 256),
            ("logo", light_logo, 250),
            ("dark_logo", dark_logo, 250),
        ):
            destination = DESTINATION / f"{name}{suffix}.png"
            destination.write_bytes(
                svg_to_bytes(
                    svg_string=source, width=width * scale, skip_system_fonts=True
                )
            )


if __name__ == "__main__":
    main()
