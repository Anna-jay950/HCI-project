"""Shared visual-condition definitions used by the task screens."""


CONTRAST_PALETTES = {
    "High": ("#f7f7f7", "#111111"),
    "Medium": ("#dedede", "#555555"),
    "Low": ("#bcbcbc", "#858585"),
}
SIZE_FONTS = {"Small": 10, "Medium": 13, "Large": 16}


def shade_color(color, brightness):
    """Scale RGB toward black while preserving at least 35% of the base color."""
    factor = 0.35 + 0.65 * (int(brightness) / 100)
    channels = [int(color[index:index + 2], 16) for index in (1, 3, 5)]
    return "#{:02x}{:02x}{:02x}".format(
        *(round(channel * factor) for channel in channels)
    )
