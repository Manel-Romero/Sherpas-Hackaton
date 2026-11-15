# =============================================================================
# 1. STYLING
# =============================================================================
# Streamlit has no built-in way to restyle things this much, so we inject our
# own CSS. We use "!important" a lot because Streamlit's own styles are quite
# specific and would otherwise win.
#
# Design rules used throughout:
#   - Surfaces get lighter as they come "closer": page < card < raised/hover.
#   - Borders are faint (white at ~8% opacity), never solid white.
#   - ONE accent color (--accent) for the things you can act on.
#   - Rounded corners: 10px for small things, 16px for cards, 999px for pills.

style = """
    <style>
    /* Load the Inter font (falls back to the system font if offline) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ---- Theme variables: change a color here and it changes everywhere ---- */
    :root {
        --bg: #0a0b0f;                         /* page background */
        --surface: #111318;                    /* cards, input */
        --surface-2: #181b23;                  /* raised: hover, user bubbles */
        --border: rgba(255, 255, 255, 0.08);   /* faint outline */
        --border-strong: rgba(255, 255, 255, 0.16);
        --text: #f4f5f7;
        --muted: rgba(244, 245, 247, 0.62);    /* secondary text */
        --accent: #4f8cff;                     /* the one accent color */
        --accent-soft: rgba(79, 140, 255, 0.22);
    }

    /* ---- Font: applied to text, but NOT to icons (they use their own font) ---- */
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label,
    .stApp button, .stApp textarea, .stApp [data-testid="stMarkdownContainer"] {
        font-family: 'Inter', -apple-system, 'Segoe UI', system-ui, sans-serif !important;
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
        padding: 0 1rem 9rem 1rem !important;
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
        background: rgba(255, 255, 255, 0.12);
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
        background: rgba(10, 11, 15, 0.82) !important;
        backdrop-filter: blur(14px);          /* frosted-glass effect */
        padding: 10px 0 !important;
        border-bottom: 1px solid var(--border) !important;
        border-radius: 0 !important;
    }
    /* App name on the far left: an accent dot + text, drawn with CSS only */
    [role="tablist"]::before {
        content: "Workspace";
        position: absolute;
        left: max(24px, calc(50vw - 500px + 16px));   /* lines up with the content column */
        top: 50%;
        transform: translateY(-50%);
        padding-left: 22px;
        font-weight: 600;
        letter-spacing: -0.01em;
        color: var(--text);
        background: radial-gradient(circle, var(--accent) 0 4.5px, transparent 5.5px)
                    no-repeat left center / 12px 12px;
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
    /* Each tab: quiet by default, raised pill when active */
    [role="tab"] {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        padding: 7px 18px !important;
        font-weight: 500 !important;
        transition: background 0.2s ease, border-color 0.2s ease;
    }
    [role="tab"], [role="tab"] * {
        color: var(--muted) !important;
    }
    [role="tab"]:hover {
        background: var(--surface) !important;
    }
    [role="tab"]:hover, [role="tab"]:hover * {
        color: var(--text) !important;
    }
    [role="tab"][aria-selected="true"] {
        background: var(--surface-2) !important;
        border-color: var(--border-strong) !important;
    }
    [role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] * {
        color: var(--text) !important;
    }
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
        font-size: 1.9rem;
        font-weight: 650;
        letter-spacing: -0.03em;
        line-height: 1.2;
    }
    .page-sub {
        color: var(--muted) !important;
        margin: 6px 0 26px 0;
    }

    /* ---- Cards ---- */
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        padding: 18px 20px !important;
        margin-bottom: 12px;                  /* space between cards */
        gap: 0.35rem !important;              /* space between title and text */
        /* faint top highlight + soft drop shadow = a bit of depth */
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset,
                    0 10px 30px -14px rgba(0, 0, 0, 0.7);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    /* On hover: slight lift, stronger outline, deeper shadow */
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker):hover {
        border-color: var(--border-strong) !important;
        transform: translateY(-1px);
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.06) inset,
                    0 18px 40px -16px rgba(0, 0, 0, 0.85);
    }
    .card-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.05rem;
        font-weight: 600;
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
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 500;
        color: var(--muted) !important;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--border);
        border-radius: 999px;
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
        border-radius: 10px !important;
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
        border-radius: 10px !important;
        min-height: 2.2rem;
        transition: background 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="stButton"] button, [data-testid="stButton"] button * {
        color: var(--text) !important;
    }
    [data-testid="stButton"] button:hover {
        background: var(--surface-2) !important;
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
        animation: fadeUp 0.3s ease backwards;
    }
    /* Your messages: right-aligned bubble, no avatar */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse;
        align-self: flex-end;
        width: fit-content;
        max-width: 80%;
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 18px 18px 6px 18px !important;
        padding: 10px 16px !important;
        margin: 6px 0;
    }
    [data-testid="stChatMessageAvatarUser"] {
        display: none !important;
    }
    /* Reply avatar: small rounded square in the accent color */
    [data-testid="stChatMessageAvatarAssistant"] {
        background: var(--accent) !important;
        border-radius: 8px !important;
    }
    [data-testid="stChatMessageAvatarAssistant"],
    [data-testid="stChatMessageAvatarAssistant"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    /* ---- Chat empty state: heading + suggestion chips ---- */
    .empty-title {
        margin-top: 9vh;
        text-align: center;
        font-size: 2rem;
        font-weight: 650;
        letter-spacing: -0.03em;
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
        border-radius: 14px !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button,
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button * {
        color: var(--muted) !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button:hover {
        background: var(--surface-2) !important;
        border-color: var(--border-strong) !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .empty-marker) [data-testid="stButton"] button:hover * {
        color: var(--text) !important;
    }

    /* ---- Chat input: floating, pinned bottom, shown only on the Chat tab ---- */
    /* When the FIRST tab ("Vertical") is selected, hide the pinned input bar */
    .stApp:has([role="tablist"] [role="tab"]:first-child[aria-selected="true"]) [data-testid="stBottom"],
    .stApp:has([role="tablist"] [role="tab"]:first-child[aria-selected="true"]) .stChatFloatingInputContainer {
        display: none !important;
    }
    /* Strip behind the input: fades from transparent into the page color */
    [data-testid="stBottom"], [data-testid="stBottom"] > div {
        background: linear-gradient(to top, var(--bg) 55%, transparent) !important;
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
        border-radius: 16px !important;
        box-shadow: 0 12px 40px -12px rgba(0, 0, 0, 0.8);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    /* While typing: accent outline with a soft glow */
    [data-testid="stChatInput"] > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-soft), 0 12px 40px -12px rgba(0, 0, 0, 0.8) !important;
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
        border-radius: 10px !important;
    }
    [data-testid="stChatInputSubmitButton"], [data-testid="stChatInputSubmitButton"] svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    /* Send button while the input is empty: dim and neutral */
    [data-testid="stChatInputSubmitButton"]:disabled {
        background: rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stChatInputSubmitButton"]:disabled, [data-testid="stChatInputSubmitButton"]:disabled svg {
        color: var(--muted) !important;
        fill: var(--muted) !important;
    }
    </style>
    """