"""Pruebas del frontend que no necesitan claves: voz (con un proxy simulado), tutorial personalizado
y resumen guardado en data/."""
import json
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "frontend"))   # al final: no debe tapar table_store de la raíz con el reexport

import personalize  # noqa: E402
import voice  # noqa: E402
import workspaces  # noqa: E402


# ---------------------------------------------------------------- voz
@pytest.fixture
def proxy(tmp_path, monkeypatch):
    """Proxy falso con TEAM_KEY, caché en una carpeta temporal y un contador de peticiones."""
    monkeypatch.setenv("TEAM_KEY", "sk-test")
    monkeypatch.setenv("LLM_PROXY_URL", "https://proxy.test/v1")
    monkeypatch.setattr(voice, "CACHE_DIR", tmp_path / "audio")
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        assert req.headers["authorization"] == "Bearer sk-test"
        if req.url.path.endswith("/audio/speech"):
            body = json.loads(req.content)
            assert body["model"] == "eleven-flash-v2.5" and body["input"]
            return httpx.Response(200, content=b"ID3-fake-mp3", headers={"content-type": "audio/mpeg"})
        if req.url.path.endswith("/audio/transcriptions"):
            assert b"scribe-v2" in req.content
            return httpx.Response(200, json={"text": " Quiero ahorrar más "})
        return httpx.Response(404)

    monkeypatch.setattr(voice, "_TRANSPORT", httpx.MockTransport(handler))
    return calls


def test_clean_for_speech_removes_markdown():
    t = "## Título\n\n- **Hola** [enlace](http://x.com) 🎯\n\n`code` https://a.b/c fin"
    assert voice.clean_for_speech(t) == "Título. Hola enlace. code fin"


def test_prepare_truncates_at_sentence():
    text = "Frase uno. " * 300
    spoken, cut = voice.prepare(text, 100)
    assert cut and len(spoken) <= 100 and spoken.endswith(".")


def test_speak_caches_to_disk(proxy):
    audio, err = voice.speak("Hola, **mundo**.")
    assert err is None and audio == b"ID3-fake-mp3"
    assert voice.is_cached("Hola, mundo.")          # el texto limpio es la clave
    audio2, _ = voice.speak("Hola, **mundo**.")
    assert audio2 == audio and len(proxy) == 1       # la segunda vez no llama al proxy


def test_speak_without_key(monkeypatch, tmp_path):
    monkeypatch.setenv("TEAM_KEY", "your-team-key-here")
    monkeypatch.setattr(voice, "CACHE_DIR", tmp_path)
    audio, err = voice.speak("Hola")
    assert audio is None and "TEAM_KEY" in err and not voice.enabled()


@pytest.mark.parametrize("status,needle", [(429, "Demasiadas"), (402, "presupuesto"), (401, "TEAM_KEY")])
def test_speak_http_errors(proxy, monkeypatch, status, needle):
    monkeypatch.setattr(voice, "_TRANSPORT", httpx.MockTransport(lambda r: httpx.Response(status, text="x")))
    audio, err = voice.speak("Otro texto distinto " + str(status))
    assert audio is None and needle in err
    assert not voice.is_cached("Otro texto distinto " + str(status))     # un error no deja caché


def test_transcribe(proxy):
    text, err = voice.transcribe(b"RIFFwav")
    assert err is None and text == "Quiero ahorrar más"
    assert voice.transcribe(b"")[0] is None


# ---------------------------------------------------------------- persona y tutorial
CASES = [c.name for c in sorted((ROOT / "cases").iterdir()) if (c / "persona.md").exists()]


@pytest.mark.parametrize("case", CASES)
def test_parse_persona_all_cases(case):
    p = personalize.parse_persona((ROOT / "cases" / case / "persona.md").read_text(encoding="utf-8"))
    assert p["D5"] in personalize.STYLE_TEXT and p["D6"] in personalize.ANCHOR_TEXT
    assert {"D0", "D1", "D2", "D3"} <= set(p)


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(workspaces, "DATA_DIR", tmp_path)
    personalize._load_case.cache_clear()
    return tmp_path


def test_steps_without_plan_use_report_and_persona(data_dir):
    steps = personalize.steps("timothy-melanie-weah")
    text = "\n".join(s["title"] + s["body"] for s in steps)
    assert "Timothy" in text and "60/100" in text and "protección" in text and "Melanie" in text
    assert "Cargar plan" in text


def test_steps_use_saved_summary(data_dir):
    workspaces.save_plan_summary("michael-carter", {
        "executive_summary": "Primer párrafo del resumen.\n\n" + ("Texto largo. " * 200),
        "master_plan": {"headline": "Tu titular", "immediate_action": {"title": "Subir seguro", "reason": "Porque sí"},
                        "tasks": [{"title": "Tarea A", "impact": {"value": "+5 pts"}}]}})
    steps = personalize.steps("michael-carter")
    titles = [s["title"] for s in steps]
    assert "Tu resumen" in titles
    summ = next(s for s in steps if s["title"] == "Tu resumen")
    assert summ["body"].startswith("Primer párrafo") and summ["more"] and len(summ["body"]) < len(summ["more"])
    plan = next(s for s in steps if s["title"] == "Tu plan de acción")
    assert "Subir seguro" in plan["body"] and "Tarea A" in plan["body"] and "+5 pts" in plan["body"]
    assert "Tu titular" in steps[0]["body"]
    assert any("Subir seguro" in q for _, q in personalize.suggestions("michael-carter"))


def test_copy_user_inherits_summary_and_addressed_by_name(data_dir):
    (data_dir / "timothy-melanie-weah").mkdir()
    workspaces.save_plan_summary("timothy-melanie-weah", {"executive_summary": "Resumen del hogar.", "master_plan": {}})
    (data_dir / "timothy-melanie-weah" / "table.json").write_text('{"columns": [], "rows": []}')
    new_id = workspaces.create_user("Melanie", "timothy-melanie-weah")
    assert workspaces.load_plan_summary(new_id)["executive_summary"] == "Resumen del hogar."
    steps = personalize.steps(new_id)
    assert "Melanie" in steps[0]["title"]                                  # no «Timothy»
    assert "Tu propia copia" in [s["title"] for s in steps]


def test_backup_before_overwrite(data_dir):
    (data_dir / "u").mkdir()
    (data_dir / "u" / "table.json").write_text("{}")
    dest = workspaces.backup_plan_files("u")
    assert dest and (dest / "table.json").exists()
    assert workspaces.backup_plan_files("nadie") is None


def test_backend_reads_saved_summary(data_dir, monkeypatch):
    import importlib
    copilot_graph = importlib.import_module("backend.app.graphs.copilot_graph")
    d = ROOT / "data" / "cases" / "__test_summary__"
    d.mkdir(parents=True, exist_ok=True)
    try:
        (d / "summary.json").write_text(json.dumps({"executive_summary": "  Resumen persistido  "}))
        assert copilot_graph._saved_summary("__test_summary__") == "Resumen persistido"
        assert copilot_graph._saved_summary("no-existe") == ""
    finally:
        (d / "summary.json").unlink()
        d.rmdir()
