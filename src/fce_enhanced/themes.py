"""Theme selection helpers for the code editor."""

import flet_code_editor as fce

# Aliases/duplicates to exclude from the theme list.
_EXCLUDED = {"DRAGULA"}

# Map human-readable display names to CodeTheme enum values, sorted alphabetically.
THEMES: dict[str, fce.CodeTheme] = dict(
    sorted(
        (
            (member.name.replace("_", " ").title(), member)
            for name, member in fce.CodeTheme.__members__.items()
            if name not in _EXCLUDED
        ),
        key=lambda item: item[0],
    )
)

DEFAULT_THEME: fce.CodeTheme = fce.CodeTheme.ATOM_ONE_DARK

# Reverse lookup: enum value -> display name.
_THEME_TO_NAME: dict[fce.CodeTheme, str] = {v: k for k, v in THEMES.items()}


def theme_display_name(theme: fce.CodeTheme) -> str:
    """Return the human-readable display name for a CodeTheme value."""
    return _THEME_TO_NAME.get(theme, theme.name.replace("_", " ").title())
