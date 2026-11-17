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
def add_column(name: str, default: float = 0.0) -> dict:
    """Add a numeric column, filled with `default` for every month."""
    data = ts.load()
    data["columns"].append(name)
    for r in data["rows"]:
        r[name] = default
    return ts.save(data)

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

import chat_store as cs

@mcp.tool(description=(
    f"Read earlier messages of the user's chat with you, oldest first. The last {cs.RECENT} messages "
    f"are already in your context, so use offset={cs.RECENT} to go further back (each call returns up to "
    f"{cs.MAX_PAGE}). Pass `search` to find messages containing a keyword instead (any age, offset ignored)."
))
def get_chat_history(limit: int = 20, offset: int = 0, search: str | None = None) -> dict:
    return cs.get_messages(limit, offset, search)

if __name__ == "__main__":
    mcp.run()