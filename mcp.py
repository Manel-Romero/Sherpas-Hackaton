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

"""MCP tools for the boxes. In mcp_server.py add:

    import boxes_tools
    boxes_tools.register(mcp)
"""
import boxes_store as bs

# ---------------- Boxes ----------------
def _find(boxes: list[dict], title: str) -> int:
    for i, b in enumerate(boxes):
        if b["title"] == title:
            return i
    raise ValueError(f"No box titled '{title}'. Existing: {[b['title'] for b in boxes]}")

@mcp.tool()
def get_boxes() -> dict:
    """Return all boxes in order: {'boxes': [{'title': str, 'content': str}, ...]}."""
    return bs.load()

@mcp.tool()
def add_box(title: str, content: str, position: int | None = None) -> dict:
    """Add a NEW box. `position` is 1-based (1 = first); omit to append at the end.
    Fails if a box with that title already exists."""
    data = bs.load()
    if any(b["title"] == title.strip() for b in data["boxes"]):
        raise ValueError(f"A box titled '{title}' already exists. Use update_box.")
    box = {"title": title, "content": content}
    if position is None:
        data["boxes"].append(box)
    else:
        data["boxes"].insert(max(position - 1, 0), box)
    return bs.save(data)

@mcp.tool()
def delete_box(title: str) -> dict:
    """Delete a box by title."""
    data = bs.load()
    del data["boxes"][_find(data["boxes"], title)]
    return bs.save(data)

@mcp.tool()
def reorder_boxes(titles: list[str]) -> dict:
    """Put the boxes in a new order. `titles` must contain every existing title exactly once."""
    data = bs.load()
    by_title = {b["title"]: b for b in data["boxes"]}
    if sorted(titles) != sorted(by_title):
        raise ValueError(f"titles must be exactly these, in any order: {list(by_title)}")
    return bs.save({"boxes": [by_title[t] for t in titles]})

@mcp.tool()
def set_boxes(boxes: list[dict]) -> dict:
    """Replace ALL boxes at once. Each item: {'title': str, 'content': str}. Titles must be unique."""
    return bs.save({"boxes": boxes})

if __name__ == "__main__":
    mcp.run()