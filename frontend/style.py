# =============================================================================
# STYLING
# =============================================================================
# Streamlit has no built-in way to restyle things this much, so we inject our
# own CSS. "!important" is used a lot because Streamlit's own styles are specific.
#
# Design rules used throughout:
#   - Dark "ink" base with a slight green cast; surfaces get lighter as they come closer.
#   - Colour carries meaning (status, category, money in / out), never decoration:
#     no gradients, glows, shadows or lift-on-hover.
#   - Type does the work: Newsreader (serif) for titles and figures, Hanken Grotesk for everything else.
#   - Corner radius follows hierarchy: 6px controls, 10px containers.
#   - No emoji as icons. Icons are Material symbols or nothing.
import base64
from pathlib import Path

_FONTS = Path(__file__).with_name("fonts")


def _font_face(family: str, file: str, weights: str) -> str:
    """@font-face with the font embedded (works offline and from any launch folder)."""
    try:
        data = base64.b64encode((_FONTS / file).read_bytes()).decode()
    except OSError:
        return ""                                     # fonts missing: the system fonts below take over
    return (f"@font-face {{ font-family: '{family}'; font-style: normal; font-weight: {weights}; "
            f"font-display: swap; src: url(data:font/woff2;base64,{data}) format('woff2'); }}")


FONT_CSS = (_font_face("Newsreader", "Newsreader-latin-wght.woff2", "200 800")
            + _font_face("Hanken Grotesk", "HankenGrotesk-latin-wght.woff2", "100 900"))

style = """
    <style>
    %FONTS%

    /* ---- Theme variables: change a color here and it changes everywhere ---- */
    :root {
        --bg: #0e1311;                         /* page: ink with a green cast */
        --surface: #151c19;                    /* inputs, cards */
        --surface-2: #1d2622;                  /* raised: hover, your messages */
        --border: rgba(222, 236, 228, 0.11);   /* hairline */
        --border-strong: rgba(222, 236, 228, 0.24);
        --text: #eef3ef;
        --muted: #b6c3bb;                      /* secondary text, still high contrast */
        --accent: #d6e6dc;                     /* pale glacier: actions and focus */
        --accent-soft: rgba(214, 230, 220, 0.20);
        --good: #86c9a4;                       /* money in, done */
        --warn: #e2b560;                       /* attention, in progress */
        --bad: #e58a78;                        /* money out, alert */
        --serif: 'Newsreader', 'Iowan Old Style', Georgia, serif;
        --sans: 'Hanken Grotesk', -apple-system, 'Segoe UI', system-ui, sans-serif;
    }

    /* ---- Font: applied to text, but NOT to icons (they use their own font) ---- */
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label,
    .stApp button, .stApp textarea, .stApp [data-testid="stMarkdownContainer"] {
        font-family: var(--sans) !important;
        font-feature-settings: 'tnum' 1, 'kern' 1;
    }
    /* Default text color. :where() gives it zero priority, so any more specific
       rule below (muted text, dark text on a light button...) wins easily. */
    :where(.stApp) :where(h1, h2, h3, p, span, label) {
        color: var(--text) !important;
    }

    /* ---- Base: one flat dark color, no Streamlit header strip ---- */
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stMain"] {
        background: var(--bg) !important;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"],
    [data-testid="stDecoration"], #MainMenu, footer {
        display: none !important;
    }

    /* Only clip sideways (the full-width bar is slightly wider than the page).
       We must NOT touch vertical overflow, or long chats can't scroll. */
    .stMain, [data-testid="stMain"], section.main {
        overflow-x: hidden !important;
    }
    /* Let the top bar stretch outside the centered content area */
    .block-container, [data-testid="stMainBlockContainer"], .stTabs, [data-testid="stTabs"] {
        overflow: visible !important;
    }
    /* Centered content column, with extra space at the bottom so the last chat
       message is never hidden behind the pinned input */
    .block-container, [data-testid="stMainBlockContainer"] {
        padding: 14px 1rem 9rem 1rem !important;   /* small top gap above the user strip */
        max-width: 1000px !important;
    }
    /* No gap above the top bar */
    [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }

    /* Slim dark scrollbars */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(222, 236, 228, 0.16);
        border-radius: 999px;
        border: 2px solid var(--bg);
    }
    ::selection { background: var(--accent-soft); }

    /* ---- Top bar: full width, translucent, app name on the left ---- */
    [role="tablist"] {
        position: sticky !important;          /* stays at the top while scrolling */
        top: 0 !important;
        z-index: 100 !important;              /* stays above the content */
        /* Width trick: make the bar as wide as the whole window (100vw) and
           pull it left so it starts at the screen edge instead of the column */
        margin-left: calc(50% - 50vw) !important;
        margin-bottom: 2.25rem !important;
        width: 100vw !important;
        display: flex !important;
        justify-content: center !important;   /* centers "Vertical" and "Chat" */
        gap: 4px !important;
        background: var(--bg) !important;
        padding: 10px 0 !important;
        border-bottom: 1px solid var(--border) !important;
        border-radius: 0 !important;
    }
    /* App name on the far left: an accent dot + text, drawn with CSS only */
    [role="tablist"]::before {
        content: "Sherpas";
        position: absolute;
        left: max(24px, calc(50vw - 500px + 16px));   /* lines up with the content column */
        top: 50%;
        transform: translateY(-50%);
        font-family: var(--serif);
        font-size: 1.28rem;
        font-weight: 500;
        letter-spacing: -0.01em;
        color: var(--text);
    }
    @media (max-width: 760px) {
        [role="tablist"]::before { display: none; }   /* not enough room on phones */
    }
    /* Streamlit draws its own thicker grey line under the tabs; hide it so
       only our thin border above remains */
    [role="tablist"]::after {
        content: none !important;
        display: none !important;
    }
    /* Each tab: plain text; the active one gets a line under it */
    [role="tab"] {
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        padding: 8px 16px !important;
        margin: 0 4px !important;
        font-weight: 500 !important;
        transition: border-color 0.15s ease;
    }
    [role="tab"], [role="tab"] * { color: var(--muted) !important; }
    [role="tab"]:hover, [role="tab"]:hover * { color: var(--text) !important; }
    [role="tab"][aria-selected="true"] { border-bottom-color: var(--text) !important; }
    [role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] * { color: var(--text) !important; }
    /* Remove the colored underline Streamlit draws under the active tab */
    .react-aria-SelectionIndicator,
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* ---- Invisible markers ----
       We drop an empty <span class="marker ..."> inside containers we want to
       style. The CSS below finds the container with :has(). This works no
       matter how Streamlit names its internal wrappers. */
    .element-container:has(.marker) {
        display: none !important;             /* the marker itself takes no space */
    }

    /* ---- Page heading (Vertical tab) ---- */
    .page-title {
        font-family: var(--serif);
        font-size: 2.1rem;
        font-weight: 500;
        letter-spacing: -0.02em;
        line-height: 1.15;
    }
    .page-sub {
        color: var(--muted) !important;
        margin: 6px 0 26px 0;
    }

    /* ---- Cards: flat, one hairline, no shadow, no lift ---- */
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 16px 18px !important;
        margin-bottom: 10px;
        gap: 0.35rem !important;
        transition: border-color 0.15s ease;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker):hover {
        border-color: var(--border-strong) !important;
    }
    .card-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: var(--serif);
        font-size: 1.2rem;
        font-weight: 500;
        letter-spacing: -0.01em;
    }
    .card-desc {
        color: var(--muted) !important;
        font-size: 0.92rem;
        line-height: 1.55;
    }
    /* Status tag: small pill with a colored dot (--dot is set per card in Python) */
    .tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--muted) !important;
    }
    .tag::before {
        content: "";
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--dot);
    }
    /* Title on the left, close button vertically centered on the right */
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] {
        display: flex;
        justify-content: flex-end;            /* pushes the ✕ to the right edge */
    }
    /* The ✕ is a quiet ghost button: only shows a background on hover */
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button {
        width: 2rem;
        height: 2rem;
        min-height: 2rem;
        padding: 0;
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 6px !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button,
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button * {
        color: var(--muted) !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: var(--border) !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button:hover * {
        color: var(--text) !important;
    }

    /* ---- Generic buttons (e.g. "Restore boxes"): subtle outline ---- */
    [data-testid="stButton"] button {
        background: var(--surface) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 6px !important;
        min-height: 2.3rem;
        font-weight: 500;
        transition: background 0.15s ease, border-color 0.15s ease;
    }
    [data-testid="stButton"] button, [data-testid="stButton"] button * {
        color: var(--text) !important;
    }
    [data-testid="stButton"] button:hover {
        background: var(--surface-2) !important;
        border-color: var(--text) !important;
    }
    /* Don't let Streamlit's ellipsis container clip button text */
    [data-testid="stButton"] button [data-testid="stMarkdownContainer"] {
        display: flex;
        justify-content: center;
        overflow: visible !important;
        text-overflow: clip !important;
    }
    [data-testid="stButton"] button p {
        margin: 0;
        line-height: 1;
    }

    /* ---- Chat: centered, narrower column for comfortable reading ---- */
    [data-testid="stVerticalBlock"]:has(> .element-container .chat-marker) {
        max-width: 760px;
        margin: 0 auto;
        gap: 0.25rem !important;
    }
    /* Smooth appearance for new messages */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: none; }
    }
    /* Base message style: no card, just text (this is how replies look) */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 10px 0 !important;
        animation: none;
    }
    /* Your messages: right-aligned bubble, no avatar */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse;
        align-self: flex-end;
        width: fit-content;
        max-width: 80%;
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 10px 16px !important;
        margin: 6px 0;
    }
    [data-testid="stChatMessageAvatarUser"] {
        display: none !important;
    }
    /* Replies: no avatar, just text. A short rule on the left tells them apart from your messages */
    [data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        border-left: 2px solid var(--border-strong) !important;
        padding: 4px 0 4px 16px !important;
        margin: 8px 0;
    }

    /* ---- Chat empty state: heading + suggestion chips ---- */
    .empty-title {
        color: var(--text) !important;
        margin-top: 9vh;
        text-align: center;
        font-family: var(--serif);
        font-size: 2.4rem;
        font-weight: 500;
        letter-spacing: -0.02em;
    }
    .empty-sub {
        text-align: center;
        color: var(--muted) !important;
        margin: 6px 0 28px 0;
    }
    /* Chips are the buttons inside the empty state */
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button {
        min-height: 3.4rem;
        padding: 12px 16px;
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        justify-content: flex-start;
        text-align: left;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button,
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button * {
        color: var(--text) !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button:hover {
        background: var(--surface-2) !important;
        border-color: var(--border-strong) !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button:hover * {
        color: var(--text) !important;
    }

    /* ---- Chat input: floating, pinned bottom, shown only on the Chat tab ---- */
    /* The pinned input bar is hidden everywhere except on the THIRD tab ("Chat Co-Pilot") */
    [data-testid="stBottom"], .stChatFloatingInputContainer {
        display: none !important;
    }
    .stApp:has([role="tablist"] [role="tab"]:nth-child(3)[aria-selected="true"]) [data-testid="stBottom"],
    .stApp:has([role="tablist"] [role="tab"]:nth-child(3)[aria-selected="true"]) .stChatFloatingInputContainer {
        display: block !important;
    }
    /* Without the input bar there is no need for the big bottom space */
    .stApp:not(:has([role="tablist"] [role="tab"]:nth-child(3)[aria-selected="true"])) [data-testid="stMainBlockContainer"] {
        padding-bottom: 3rem !important;
    }
    /* Strip behind the input: fades from transparent into the page color */
    [data-testid="stBottom"], [data-testid="stBottom"] > div {
        background: var(--bg) !important;
    }
    /* The outer element is just a holder, centered and capped at 760px */
    [data-testid="stChatInput"] {
        max-width: 760px !important;
        margin: 0 auto !important;
        background: transparent !important;
        border: none !important;
    }
    /* The visible box is its inner div */
    [data-testid="stChatInput"] > div {
        background: var(--surface) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        transition: border-color 0.15s ease;
    }
    /* While typing: lighter outline, no glow */
    [data-testid="stChatInput"] > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea {
        color: var(--text) !important;
        caret-color: var(--accent) !important;   /* the blinking cursor */
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--muted) !important;
        opacity: 1;
    }
    /* Send button: accent color with a white arrow */
    [data-testid="stChatInputSubmitButton"] {
        background: var(--accent) !important;
        border-radius: 6px !important;
    }
    [data-testid="stChatInputSubmitButton"], [data-testid="stChatInputSubmitButton"] svg {
        color: #0e1311 !important;
        fill: #0e1311 !important;
    }
    /* Send button while the input is empty: dim and neutral */
    [data-testid="stChatInputSubmitButton"]:disabled {
        background: var(--surface-2) !important;
    }
    [data-testid="stChatInputSubmitButton"]:disabled, [data-testid="stChatInputSubmitButton"]:disabled svg {
        color: var(--muted) !important;
        fill: var(--muted) !important;
    }

    /* ---- User strip, figures, dialogs, progress ---- */
    .user-chip, .user-chip strong { color: var(--text) !important; }
    .user-chip { display: flex; align-items: baseline; gap: 12px; padding-top: 4px; flex-wrap: wrap; }
    .user-chip strong { font-family: var(--serif); font-size: 1.35rem; font-weight: 500; letter-spacing: -0.01em; }
    .user-meta { color: var(--muted) !important; font-size: 0.88rem; }

    /* Figures: big serif numbers separated by hairlines (they are a row of facts, not cards) */
    .figures { display: flex; flex-wrap: wrap; margin: 4px 0 8px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
    .figure { flex: 1 1 140px; padding: 16px 20px 16px 0; margin-right: 20px; border-right: 1px solid var(--border); }
    .figure:last-child { border-right: none; margin-right: 0; }
    .figure-label { color: var(--muted) !important; font-size: 0.86rem; }
    .figure-value { font-family: var(--serif); font-size: 2rem; font-weight: 500; line-height: 1.15; letter-spacing: -0.02em; margin-top: 2px; }
    .figure-value.neg { color: var(--bad) !important; }
    .figure-value.pos { color: var(--good) !important; }

    [data-testid="stExpander"] { margin-top: 10px; }
    [data-testid="stExpander"] details {
        background: transparent !important; border: 1px solid var(--border) !important; border-radius: 10px !important;
    }
    [data-testid="stExpander"] summary p { font-weight: 500; }
    [data-testid="stProgress"] > div > div > div { background-color: var(--accent) !important; }
    [data-testid="stPopover"] button, [data-testid="stFormSubmitButton"] button {
        background: var(--surface) !important; border: 1px solid var(--border-strong) !important;
        border-radius: 6px !important;
    }
    [data-testid="stPopover"] button, [data-testid="stPopover"] button *,
    [data-testid="stFormSubmitButton"] button, [data-testid="stFormSubmitButton"] button * {
        color: var(--text) !important;
    }
    [data-testid="stDialog"] [role="dialog"] {
        background: var(--surface) !important; border: 1px solid var(--border-strong) !important;
        border-radius: 10px !important;
    }
    [data-testid="stDialog"] h2, [data-testid="stDialog"] h2 * {
        font-family: var(--serif) !important; font-weight: 500 !important; letter-spacing: -0.01em;
    }
    [data-testid="stDialog"] blockquote {
        border-left: 2px solid var(--border-strong); margin: 12px 0; padding: 2px 0 2px 14px;
        font-family: var(--serif); font-size: 1.15rem;
    }
    [data-testid="stDialog"] { background: rgba(5, 8, 7, 0.8) !important; }
    [data-testid="stDialog"] blockquote p { color: var(--text) !important; opacity: 1 !important; font-family: var(--serif); font-size: 1.2rem; line-height: 1.4; }
    /* Login / suggestion rows: text starts at the left */
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button [data-testid="stMarkdownContainer"] {
        justify-content: flex-start;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button > div {
        justify-content: flex-start !important; width: 100%;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button { min-height: 3.6rem; padding-left: 20px; }
    /* Listen buttons under chat replies: quiet text buttons */
    [data-testid="stChatMessage"] [data-testid="stButton"] button {
        background: transparent !important; border-color: transparent !important; min-height: 1.9rem; padding: 0 8px 0 0 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stButton"] button, [data-testid="stChatMessage"] [data-testid="stButton"] button * { color: var(--muted) !important; }
    [data-testid="stChatMessage"] [data-testid="stButton"] button:hover, [data-testid="stChatMessage"] [data-testid="stButton"] button:hover * { color: var(--text) !important; background: transparent !important; }
    /* Material icons inside buttons keep their own font */
    [data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
    @media (max-width: 760px) {
        [role="tab"] { padding: 7px 8px !important; margin: 0 !important; font-size: 0.88rem !important; }
        .figure-value { font-size: 1.5rem; }
        .figure { flex-basis: 45%; margin-right: 12px; padding-right: 12px; }
        .empty-title { font-size: 1.7rem; }
    }
    </style>
""".replace("%FONTS%", FONT_CSS)
