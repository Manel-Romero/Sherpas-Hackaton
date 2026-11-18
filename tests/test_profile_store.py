"""Ficha de datos (profile_store): se crea desde el caso, coincide con la tabla y los cambios la mantienen al día."""
import json
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CASES = ["timothy-melanie-weah", "michael-carter", "samantha-lewis", "daniel-emily-johnson"]


@pytest.fixture
def stores(tmp_path, monkeypatch):
    import project_paths, table_store as ts, profile_store as ps
    monkeypatch.setattr(project_paths, "DATA_CASES_DIR", tmp_path)
    monkeypatch.setattr(ts, "BASE_DATA_DIR", tmp_path)
    return ts, ps


def _case(cid):
    d = ROOT / "cases" / cid
    fh = json.loads((d / "financial-health.json").read_text(encoding="utf-8"))
    ia_f = d / "investment-analysis.json"
    ia = json.loads(ia_f.read_text(encoding="utf-8")) if ia_f.exists() else {}
    return fh, ia, (d / "persona.md").read_text(encoding="utf-8")


def _new(stores, cid):
    ts, ps = stores
    ts.initialize_default_table(cid, 9000, 6000, 30000, 100000)        # como el plan: estimaciones del modelo
    return ps.create(cid, *_case(cid))


@pytest.mark.parametrize("cid", CASES)
def test_profile_matches_report_and_table(stores, cid):
    ts, ps = stores
    p = _new(stores, cid)
    t = ps.totals(p)
    fh = _case(cid)[0]
    cf = fh["key_metrics"]["cashflowStatement"]
    out = {i["name"]: i["total"] for i in cf["outflows"]["items"]}
    # ingresos netos y gastos coinciden con el estado de flujos del informe
    assert abs(t["income"] - (cf["inflows"]["total"] - out.get("Taxes", 0)) / 12) < 1
    assert abs(t["spend"] - sum(v for k, v in out.items() if k not in ("Taxes", "Savings")) / 12) < 25
    date, row = ps.table_today(cid)
    assert date == datetime.now().strftime("%Y-%m")
    assert row["Ingresos"] == t["income"] and row["Gastos_Fijos"] == t["spend"]
    assert row["Deuda_Pendiente"] == t["debt"] and row["Patrimonio"] == t["net_worth"]
    rows = ts.load(cid)["rows"]
    i = [r["date"] for r in rows].index(date)
    assert rows[i + 1]["Patrimonio"] == round(t["net_worth"] + max(0, t["income"] - t["spend"]), 2)  # proyección desde hoy


def test_timothy_figures(stores):
    _, ps = stores
    t = ps.totals(_new(stores, "timothy-melanie-weah"))
    assert round(t["net_worth"]) == 695500 and round(t["debt"]) == 93000
    assert round(t["income"]) == 16436 and round(t["spend"]) == 9398


def test_paying_debt_from_cash_keeps_everything_in_sync(stores):
    ts, ps = stores
    cid = "timothy-melanie-weah"
    _new(stores, cid)
    nw0 = ps.totals(ps.load(cid))["net_worth"]
    msg = ps.update(cid, "debt", "Chase CC", balance=18000 - 6800)
    assert "Deuda total: $93,000 -> $86,200" in msg
    ps.update(cid, "account", "Cash account", balance=150000 - 6800)
    p = ps.load(cid)
    t = ps.totals(p)
    assert t["debt"] == 86200 and t["net_worth"] == nw0                  # pagar con ahorros no cambia el patrimonio
    _, row = ps.table_today(cid)
    assert row["Deuda_Pendiente"] == 86200 and row["Patrimonio"] == nw0
    assert len(p["history"]) == 2
    assert "AVISO" not in ps.prompt_context(cid, p)["today_text"]


def test_paid_off_debt_drops_its_payment_and_future_debt_follows(stores):
    ts, ps = stores
    cid = "timothy-melanie-weah"
    _new(stores, cid)
    before = ps.totals(ps.load(cid))
    ps.update(cid, "debt", "chase", balance=0)                           # nombre parcial
    t = ps.totals(ps.load(cid))
    assert t["debt_payments"] == before["debt_payments"] - 300 and t["spend"] == before["spend"] - 300
    rows = ts.load(cid)["rows"]
    i = [r["date"] for r in rows].index(datetime.now().strftime("%Y-%m"))
    fut = [r["Deuda_Pendiente"] for r in rows[i:]]
    assert fut == sorted(fut, reverse=True) and fut[0] == t["debt"]      # la deuda baja mes a mes desde hoy
    assert rows[i + 1]["Gastos_Fijos"] == t["spend"]


def test_raise_and_new_expense_move_today_and_future_only(stores):
    ts, ps = stores
    cid = "michael-carter"
    _new(stores, cid)
    rows0 = ts.load(cid)["rows"]
    ps.update(cid, "income", "Client's income salary", yearly=192000)
    ps.update(cid, "expense", "Gimnasio", monthly=60)
    rows = ts.load(cid)["rows"]
    i = [r["date"] for r in rows].index(datetime.now().strftime("%Y-%m"))
    t = ps.totals(ps.load(cid))
    assert rows[i]["Ingresos"] == t["income"] and rows[-1]["Ingresos"] == t["income"]
    assert rows[i]["Gastos_Fijos"] == t["spend"]
    assert rows[0]["Ingresos"] == rows0[0]["Ingresos"]                   # el pasado no se toca


def test_manual_table_edit_is_flagged(stores):
    ts, ps = stores
    cid = "samantha-lewis"
    p = _new(stores, cid)
    date, _ = ps.table_today(cid)
    ts.set_cell(date, "Patrimonio", 1.0, case_id=cid)
    assert "AVISO" in ps.prompt_context(cid, p)["today_text"]


def test_errors_are_explained(stores):
    _, ps = stores
    cid = "michael-carter"
    assert "genera el plan" in ps.update(cid, "debt", "x", balance=1)
    _new(stores, cid)
    assert "No encuentro" in ps.update(cid, "debt", "No existe", action="remove")
    assert "indica 'monthly'" in ps.update(cid, "expense", "Algo")
    assert "no válido" in ps.update(cid, "car", "x")


def test_table_projection_anchor_keeps_history(stores):
    ts, _ = stores
    cid = "anchor-test"
    ts.initialize_default_table(cid, 10000, 6000, 0, 50000)
    rows = ts.load(cid)["rows"]
    i = [r["date"] for r in rows].index(datetime.now().strftime("%Y-%m"))
    past = rows[0]["Patrimonio"]
    ts.set_cell(rows[i]["date"], "Patrimonio", 80000, case_id=cid)
    rows = ts.load(cid)["rows"]
    assert rows[i]["Patrimonio"] == 80000 and rows[0]["Patrimonio"] == past     # hoy se respeta, el pasado no cambia
    assert rows[i + 1]["Patrimonio"] == 84000                                   # y el futuro se proyecta desde hoy
