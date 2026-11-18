"""Compatibilidad entre versiones de Streamlit: `use_container_width=True` (antiguo) o
`width="stretch"` (nuevo). Se detecta por la firma de cada función, así funciona en ambas."""
import inspect


def stretch(fn) -> dict:
    return {"width": "stretch"} if "width" in inspect.signature(fn).parameters else {"use_container_width": True}
