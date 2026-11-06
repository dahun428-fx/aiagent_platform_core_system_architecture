"""Inline line pictograms for the portal. `{{icon:name}}` in Markdown becomes an inline SVG.

Inline SVG (not <img> or <use href>) keeps the icons offline-safe under file://, and
stroke="currentColor" lets them follow the light/dark theme.
"""
import re

PATHS = {
    "gateway": '<path d="M4 21V9l8-6 8 6v12"/><path d="M9 21v-7h6v7"/><path d="M2 21h20"/>',
    "runtime": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M10 9l5 3-5 3z"/>',
    "model": '<rect x="7" y="7" width="10" height="10" rx="1.5"/><path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"/>',
    "tools": '<path d="M14.7 6.3a4 4 0 0 0-5.3 5.3L3.5 17.5a1.5 1.5 0 0 0 0 2.1l.9.9a1.5 1.5 0 0 0 2.1 0l5.9-5.9a4 4 0 0 0 5.3-5.3l-2.6 2.6-2.3-.6-.6-2.3z"/>',
    "identity": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2"/><path d="M6 16c.6-1.4 1.6-2 3-2s2.4.6 3 2M14.5 10h4M14.5 13.5h3"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M16.5 6.5l2.5 2.5M14 9l2 2"/>',
    "knowledge": '<path d="M4 19.5V5a2 2 0 0 1 2-2h13v15H6a2 2 0 0 0-2 2 2 2 0 0 0 2 2h13"/><path d="M9 7h6M9 11h4"/>',
    "control": '<path d="M12 9v12M8 21h8"/><circle cx="12" cy="7" r="2"/><path d="M7.8 2.8a6 6 0 0 0 0 8.4M16.2 2.8a6 6 0 0 1 0 8.4"/>',
    "trace": '<circle cx="5" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="M7 6h8a3 3 0 0 1 0 6H9a3 3 0 0 0 0 6h8"/>',
    "shield": '<path d="M12 3l8 3v6c0 4.8-3.4 8-8 9-4.6-1-8-4.2-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/>',
    "agent": '<rect x="4" y="8" width="16" height="12" rx="3"/><path d="M12 4v4"/><circle cx="12" cy="3.5" r="1"/><circle cx="9" cy="14" r="1.2"/><circle cx="15" cy="14" r="1.2"/>',
    "agents": '<rect x="2" y="9" width="10" height="9" rx="2"/><rect x="12" y="6" width="10" height="9" rx="2"/><circle cx="5.5" cy="13.5" r=".8"/><circle cx="8.5" cy="13.5" r=".8"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7"/>',
    "cross": '<path d="M6 6l12 12M18 6L6 18"/>',
    "manifest": '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
    "laptop": '<rect x="4" y="5" width="16" height="11" rx="1.5"/><path d="M2 19h20"/>',
    "cloud": '<path d="M7 18a4 4 0 0 1-.6-8A6 6 0 0 1 18 9.5a4.3 4.3 0 0 1-.5 8.5z"/>',
    "server": '<rect x="4" y="4" width="16" height="7" rx="1.5"/><rect x="4" y="13" width="16" height="7" rx="1.5"/><path d="M8 7.5h.01M8 16.5h.01"/>',
    "target": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/>',
    "bulb": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.8 10.6c.6.6.8 1.4.8 2.4h6c0-1 .2-1.8.8-2.4A6 6 0 0 0 12 3z"/>',
    "question": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.3a2.6 2.6 0 1 1 3.6 2.4c-.7.3-1.1.9-1.1 1.6v.7"/><path d="M12 17h.01"/>',
    "eye": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "workflow": '<circle cx="5" cy="6" r="2.5"/><circle cx="19" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M7.5 6h9M6.3 8.2l4.4 7.6M17.7 8.2l-4.4 7.6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "approve": '<circle cx="9" cy="8" r="4"/><path d="M2 21c.8-3.7 3.3-6 7-6 1.4 0 2.6.3 3.6.9"/><path d="M15 18l2 2 4-4"/>',
    "test": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3"/><path d="M7.5 15h9"/>',
    "code": '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>',
    "book": '<path d="M2 5h6a4 4 0 0 1 4 4v11a3 3 0 0 0-3-3H2zM22 5h-6a4 4 0 0 0-4 4v11a3 3 0 0 1 3-3h7z"/>',
    "map": '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
    "rocket": '<path d="M5 15c-1.5 1.2-2 3.5-2 6 2.5 0 4.8-.5 6-2"/><path d="M9 18l-3-3c1.5-5 5.5-10 13-12-2 7.5-7 11.5-12 13z"/><circle cx="14.5" cy="9.5" r="1.5"/>',
    "warn": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18h.01"/>',
}


def svg(name, cls="icon"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{PATHS[name]}</svg>')


def expand(body):
    """Replace {{icon:name}} placeholders, leaving <pre> blocks untouched."""
    parts = re.split(r"(<pre>.*?</pre>)", body, flags=re.S)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"\{\{icon:([a-z]+)\}\}", lambda m: svg(m.group(1)), parts[i])
    return "".join(parts)
