"""Rendering helpers for the ambiguous-figure identification activity."""

from main_settings import CONTRAST_PALETTES, shade_color


IDENTIFICATION_RESPONSES = (
    "A vase",
    "Two faces",
    "Both interpretations",
    "Something else",
)


def draw_ambiguous_figure(canvas, settings):
    """Draw the same two-tone Rubin-style vase/profile figure for every condition."""
    background, foreground = CONTRAST_PALETTES[settings["contrast"]]
    background = shade_color(background, settings["brightness"])
    foreground = shade_color(foreground, settings["brightness"])
    canvas.delete("all")
    canvas.configure(background=foreground)

    center = 350
    vase = [
        center - 85, 40, center + 85, 40,
        center + 72, 75, center + 38, 100,
        center + 30, 130, center + 34, 144,
        center + 43, 151, center + 32, 157,
        center + 39, 163, center + 30, 169,
        center + 34, 178, center + 30, 190, center + 54, 220,
        center + 72, 260, center + 72, 280,
        center - 72, 280, center - 72, 260,
        center - 54, 220, center - 30, 190,
        center - 34, 178, center - 30, 169,
        center - 39, 163, center - 32, 157,
        center - 43, 151, center - 34, 144, center - 30, 130,
        center - 38, 100, center - 72, 75,
    ]
    canvas.create_polygon(vase, fill=background, outline=background, smooth=True, width=3)
