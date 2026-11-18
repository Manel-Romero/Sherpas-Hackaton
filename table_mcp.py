"""MCP server that lets an AI read and modify the table (stdio transport)."""
from mcp.server.fastmcp import FastMCP

import table_store as ts

mcp = FastMCP("monthly-table")

@mcp.tool()
def get_table() -> dict:
    """Return the full table: {'columns': [...], 'rows': [{'date': 'YYYY-MM', <col>: number}, ...]}."""
    return ts.load()

@mcp.tool()
def set_cell(date: str, column: str, value: float) -> dict:
    """Set one cell. Creates the month row if it doesn't exist (other cells = 0)."""
    return set_cells([{"date": date, "column": column, "value": value}])


@mcp.tool()
def set_cells(updates: list[dict]) -> dict:
    """Set many cells at once. Each update: {'date': 'YYYY-MM', 'column': str, 'value': number}.
    Missing months are created; the column must already exist."""
    data = ts.load()
    rows = {r["date"]: r for r in data["rows"]}
    for u in updates:
        d = ts.normalize_date(u["date"])
        if u["column"] not in data["columns"]:
            raise ValueError(f"Unknown column '{u['column']}'. Existing: {data['columns']}")
        row = rows.setdefault(d, {"date": d, **{c: 0.0 for c in data["columns"]}})
        row[u["column"]] = ts.to_number(u["value"])
    data["rows"] = list(rows.values())
    return ts.save(data)


@mcp.tool()
def set_row(date: str, values: dict[str, float]) -> dict:
    """Create or update a month row. `values` maps column name -> number."""
    return set_cells([{"date": date, "column": c, "value": v} for c, v in values.items()])


@mcp.tool()
def delete_row(date: str) -> dict:
    """Delete a month row."""
    data = ts.load()
    d = ts.normalize_date(date)
    data["rows"] = [r for r in data["rows"] if r["date"] != d]
    return ts.save(data)

@mcp.tool()
def add_column(name: str, default: float = 0.0, formula: str | None = None) -> dict:
    """Add a numeric column, filled with `default` or calculated with an Excel-like formula."""
    return ts.add_column(name, default, formula)

@mcp.tool()
def apply_column_formula(
    column: str,
    formula: str,
    start_date: str | None = None,
    initial_value: float | None = None
) -> dict:
    """Apply an Excel-like formula to a column across months (e.g. 'prev * 1.10', 'Ingresos * 0.15')."""
    return ts.apply_column_formula(column, formula, start_date, initial_value)

@mcp.tool()
def set_cell_formula(date: str, column: str, formula: str) -> dict:
    """Evaluate and set an Excel-like formula on a specific cell (e.g. '=prev * 1.10', '=Ingresos - Gastos_Fijos')."""
    return ts.set_cell_formula(date, column, formula)

@mcp.tool()
def evaluate_formula(expression: str, variables: dict | None = None) -> float:
    """Evaluate an open financial or mathematical formula (e.g. '15000 * (1.10 ** 12)')."""
    ctx = variables or {}
    return ts.evaluate_formula(expression, ctx)

@mcp.tool()
def spreadsheet_aggregate(
    column: str,
    operation: str = "sum",
    start_date: str | None = None,
    end_date: str | None = None
) -> float:
    """Calculate Excel aggregation (sum, average, min, max, growth_rate) over a column."""
    return ts.spreadsheet_aggregate(column, operation, start_date, end_date)

@mcp.tool()
def delete_column(name: str) -> dict:
    """Delete a column."""
    data = ts.load()
    if name not in data["columns"]:
        raise ValueError(f"Unknown column '{name}'.")
    data["columns"].remove(name)
    for r in data["rows"]:
        r.pop(name, None)
    return ts.save(data)

import kanban_store as ks

@mcp.tool()
def get_kanban() -> dict:
    """Return the board: {'statuses': [...], 'cards': [{'id','title','content','status'}, ...]}.
    Cards are listed in column order. Use the ids from here for the other tools."""
    return {"statuses": list(ks.STATUSES), **ks.load()}

@mcp.tool()
def add_card(title: str, content: str = "", status: str = "todo") -> dict:
    """Add a card. status: 'todo', 'in_process' or 'done'. Returns the board (new card is last)."""
    return ks.add_card(title, content, status)

@mcp.tool()
def update_card(card_id: str, title: str | None = None, content: str | None = None) -> dict:
    """Change a card's title and/or content."""
    return ks.update_card(card_id, title, content)

@mcp.tool()
def move_card(card_id: str, status: str) -> dict:
    """Move a card to 'todo', 'in_process' or 'done' (it goes to the bottom of that column)."""
    return ks.move_card(card_id, status)

@mcp.tool()
def delete_card(card_id: str) -> dict:
    """Delete a card."""
    return ks.delete_card(card_id)

if __name__ == "__main__":
    mcp.run()