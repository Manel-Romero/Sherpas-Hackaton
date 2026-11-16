"""Editable monthly table.

In app.py:
    import table_ui
    ...
    table_ui.refresh()          # state block, AFTER the user's file paths are set
    ...
    with table:
        table_ui.render()
    ...
    table_ui.changed()          # used by the watcher
"""
import streamlit as st

import table_store as ts


def refresh():
    """Reload the table the editor starts from, but only when the file changed from OUTSIDE
    (the AI, or adding a column). The editor needs a base table that stays the same while
    you type, and a new key (editor_gen) to reset itself when that base is replaced."""
    ss = st.session_state
    if "table_version" not in ss or ts.version() != ss.table_version:
        ss.table_version = ts.version()
        ss.df = ts.to_df(ts.load())
        ss.editor_gen = ss.get("editor_gen", 0) + 1   # new key -> editor resets


def changed() -> bool:
    """True if the file was changed by someone else since this session last looked."""
    return ts.version() != st.session_state.table_version


def _add_column():
    with st.popover("➕ Add column"):
        with st.form("add_col", clear_on_submit=True):
            name = st.text_input("Column name")
            default = st.number_input("Default value", value=0.0)
            if st.form_submit_button("Add") and name.strip():
                try:
                    table = ts.load()
                    table["columns"].append(name.strip())
                    for r in table["rows"]:
                        r[name.strip()] = default
                    ts.save(table)
                    st.rerun()      # table_version is now stale -> refresh() reloads the table
                except ValueError as e:
                    st.error(str(e))


def render():
    ss = st.session_state
    _add_column()

    columns = list(ss.df.columns[1:])
    config = {"date": st.column_config.TextColumn(
        "Month (YYYY-MM)",
        required=True,
        default=ts.default_month(ts.load()),    # new rows start with the next month
    )}
    for c in columns:
        config[c] = st.column_config.NumberColumn(c)

    edited = st.data_editor(
        ss.df,                                  # the same base until an external change
        key=f"editor-{ss.editor_gen}",
        num_rows="dynamic",
        column_config=config,
        hide_index=True,
    )

    try:
        new = ts.from_df(edited, columns)
        current = ts.load()
        if new != current:
            row_added = len(new["rows"]) > len(current["rows"])
            ts.save(new)
            ss.table_version = ts.version()     # our own save: don't treat it as an outside change
            if row_added:
                # Rebuild the base and reset the editor, so the NEXT new row
                # gets the next month instead of repeating this one
                ss.df = ts.to_df(new)
                ss.editor_gen += 1
                st.rerun()
    except ValueError as e:
        st.error(str(e))
