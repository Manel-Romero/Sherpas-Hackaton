# =============================================================================
# 1. STYLING - SHERPAS WEALTH OFFICIAL DESIGN SYSTEM
# =============================================================================
# Diseno refinado inspirado en https://sherpaswealth.com/
# Paleta: Obsidian navy (#04070d), cobalt accent (#4565d6), Poppins & Inter.

style = """
    <style>
    /* Google Fonts: Inter para datos/cuerpo y Poppins para cabeceras y marca */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@500;600;700;800&display=swap');

    /* Variables del tema oficial Sherpas Wealth */
    :root {
        --bg: #04070d;                         /* obsidian profundo */
        --surface: #0a0f18;                    /* tarjetas y contenedores */
        --surface-2: #0e1626;                  /* elementos elevados */
        --surface-3: #141f36;                  /* hover y modales */
        --border: rgba(255, 255, 255, 0.08);   /* bordes sutiles */
        --border-strong: rgba(69, 101, 214, 0.28);
        --text: #f8fafc;                       /* texto principal de alto contraste */
        --muted: #94a3b8;                      /* texto secundario refinado */
        --accent: #4565d6;                     /* cobalto oficial Sherpas */
        --accent-light: #6586fc;
        --accent-soft: rgba(69, 101, 214, 0.16);
        --accent-glow: rgba(69, 101, 214, 0.35);
        --success: #10b981;
        --success-soft: rgba(16, 185, 129, 0.14);
        --danger: #ef4444;
        --danger-soft: rgba(239, 68, 68, 0.14);
    }

    /* Tipografia base */
    .stApp, .stApp p, .stApp label,
    .stApp button, .stApp textarea, .stApp [data-testid="stMarkdownContainer"] {
        font-family: 'Inter', -apple-system, 'Segoe UI', system-ui, sans-serif !important;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .page-title, .brand-title {
        font-family: 'Poppins', -apple-system, sans-serif !important;
        letter-spacing: -0.02em;
    }
    :where(.stApp) :where(h1, h2, h3, p, span, label) {
        color: var(--text) !important;
    }

    /* Fondo general */
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stMain"] {
        background: var(--bg) !important;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"],
    [data-testid="stDecoration"], #MainMenu, footer {
        display: none !important;
    }

    .stMain, [data-testid="stMain"], section.main {
        overflow-x: hidden !important;
    }
    .block-container, [data-testid="stMainBlockContainer"], .stTabs, [data-testid="stTabs"] {
        overflow: visible !important;
    }
    .block-container, [data-testid="stMainBlockContainer"] {
        padding: 0 1.25rem 9rem 1.25rem !important;
        max-width: 1200px !important;
    }
    [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }

    /* Barras de scroll oscuras */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.12);
        border-radius: 999px;
        border: 2px solid var(--bg);
    }
    ::selection { background: var(--accent-soft); }

    /* Barra superior fija de pestanas */
    [role="tablist"] {
        position: sticky !important;
        top: 0 !important;
        z-index: 100 !important;
        margin-left: calc(50% - 50vw) !important;
        margin-bottom: 1.75rem !important;
        width: 100vw !important;
        display: flex !important;
        justify-content: center !important;
        gap: 6px !important;
        background: rgba(4, 7, 13, 0.90) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        padding: 12px 0 !important;
        border-bottom: 1px solid var(--border) !important;
        border-radius: 0 !important;
    }
    [role="tablist"]::before {
        content: "SHERPAS WEALTH";
        position: absolute;
        left: max(24px, calc(50vw - 600px + 20px));
        top: 50%;
        transform: translateY(-50%);
        padding-left: 20px;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700;
        font-size: 0.92rem;
        letter-spacing: 0.05em;
        color: var(--text);
        background: radial-gradient(circle, var(--accent) 0 4.5px, transparent 5.5px)
                    no-repeat left center / 12px 12px;
    }
    @media (max-width: 820px) {
        [role="tablist"]::before { display: none; }
    }
    [role="tablist"]::after {
        content: none !important;
        display: none !important;
    }
    [role="tab"] {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        padding: 8px 20px !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        transition: all 0.18s ease;
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
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
    }
    [role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] * {
        color: #ffffff !important;
    }
    .react-aria-SelectionIndicator,
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Marcador invisible */
    .element-container:has(.marker) {
        display: none !important;
    }

    /* Titulo de pagina */
    .page-title {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.25;
        color: #ffffff !important;
    }
    .page-sub {
        color: var(--muted) !important;
        margin: 6px 0 24px 0;
        font-size: 0.95rem;
    }

    /* Tarjetas de accion */
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        padding: 18px 22px !important;
        margin-bottom: 12px;
        gap: 0.35rem !important;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset,
                    0 10px 30px -14px rgba(0, 0, 0, 0.7);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
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
    .tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 10px;
        font-size: 0.72rem;
        font-weight: 600;
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
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] {
        display: flex;
        justify-content: flex-end;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button {
        width: 2rem;
        height: 2rem;
        min-height: 2rem;
        padding: 0;
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button,
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button * {
        color: var(--muted) !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button:hover {
        background: rgba(239, 68, 68, 0.16) !important;
        border-color: rgba(239, 68, 68, 0.3) !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container .box-marker) [data-testid="stButton"] button:hover * {
        color: #ef4444 !important;
    }

    /* Botones globales */
    [data-testid="stButton"] button {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        min-height: 2.2rem;
        font-weight: 500 !important;
        transition: all 0.18s ease;
    }
    [data-testid="stButton"] button, [data-testid="stButton"] button * {
        color: var(--text) !important;
    }
    [data-testid="stButton"] button:hover {
        background: var(--surface-3) !important;
        border-color: var(--border-strong) !important;
    }
    [data-testid="stButton"] button [data-testid="stMarkdownContainer"] {
        display: flex;
        justify-content: center;
        overflow: visible !important;
        text-overflow: clip !important;
    }
    [data-testid="stButton"] button p {
        margin: 0;
        line-height: 1.2;
    }

    /* Chat: contenedor estilizado */
    [data-testid="stVerticalBlock"]:has(> .element-container .chat-marker) {
        max-width: 860px;
        margin: 0 auto;
        gap: 0.35rem !important;
    }
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: none; }
    }
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 12px 0 !important;
        animation: fadeUp 0.25s ease backwards;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse;
        align-self: flex-end;
        width: fit-content;
        max-width: 85%;
        background: var(--surface-2) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 16px 16px 4px 16px !important;
        padding: 12px 18px !important;
        margin: 6px 0;
    }
    [data-testid="stChatMessageAvatarUser"] {
        display: none !important;
    }
    [data-testid="stChatMessageAvatarAssistant"] {
        background: var(--accent) !important;
        border-radius: 8px !important;
        box-shadow: 0 0 14px var(--accent-glow) !important;
    }
    [data-testid="stChatMessageAvatarAssistant"],
    [data-testid="stChatMessageAvatarAssistant"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    /* Entrada de chat flotante */
    .stApp:has([role="tablist"] [role="tab"]:first-child[aria-selected="true"]) [data-testid="stBottom"],
    .stApp:has([role="tablist"] [role="tab"]:first-child[aria-selected="true"]) .stChatFloatingInputContainer {
        display: none !important;
    }
    [data-testid="stBottom"], [data-testid="stBottom"] > div {
        background: linear-gradient(to top, var(--bg) 60%, transparent) !important;
    }
    [data-testid="stChatInput"] {
        max-width: 860px !important;
        margin: 0 auto !important;
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stChatInput"] > div {
        background: var(--surface) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 16px !important;
        box-shadow: 0 12px 40px -12px rgba(0, 0, 0, 0.8);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stChatInput"] > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-soft), 0 12px 40px -12px rgba(0, 0, 0, 0.8) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: var(--text) !important;
        caret-color: var(--accent-light) !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--muted) !important;
        opacity: 1;
    }
    [data-testid="stChatInputSubmitButton"] {
        background: var(--accent) !important;
        border-radius: 10px !important;
    }
    [data-testid="stChatInputSubmitButton"], [data-testid="stChatInputSubmitButton"] svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    [data-testid="stChatInputSubmitButton"]:disabled {
        background: rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stChatInputSubmitButton"]:disabled, [data-testid="stChatInputSubmitButton"]:disabled svg {
        color: var(--muted) !important;
        fill: var(--muted) !important;
    }

    /* Componentes ejecutivos y tarjetas de presentacion */
    .top-header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: var(--surface);
        padding: 12px 20px;
        border-radius: 14px;
        border: 1px solid var(--border);
        margin-bottom: 18px;
    }
    .brand-logo-text {
        font-family: 'Poppins', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: #ffffff;
    }
    .brand-sub-text {
        font-size: 0.76rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .persona-card {
        background: linear-gradient(135deg, rgba(14, 22, 38, 0.95) 0%, rgba(10, 15, 24, 0.95) 100%);
        border: 1px solid var(--border-strong);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }
    .persona-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 600;
        background: var(--accent-soft);
        color: #93c5fd;
        border: 1px solid var(--border-strong);
    }
    .kpi-pill {
        background: var(--surface-2);
        padding: 10px 16px;
        border-radius: 10px;
        border: 1px solid var(--border);
        font-size: 0.88rem;
    }
    .score-glow-pill {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(16, 185, 129, 0.08) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34d399;
        padding: 6px 16px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.9rem;
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.2);
    }
    .score-glow-pill-amber {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.18) 0%, rgba(245, 158, 11, 0.08) 100%);
        border: 1px solid rgba(245, 158, 11, 0.4);
        color: #fbbf24;
        padding: 6px 16px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.9rem;
        box-shadow: 0 0 16px rgba(245, 158, 11, 0.2);
    }
    .score-glow-pill-red {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.18) 0%, rgba(239, 68, 68, 0.08) 100%);
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #f87171;
        padding: 6px 16px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.9rem;
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.2);
    }
    .quick-chip-container {
        display: flex;
        gap: 8px;
        margin-bottom: 14px;
        flex-wrap: wrap;
    }
    </style>
    """
