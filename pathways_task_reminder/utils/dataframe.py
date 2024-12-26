import pandas as pd
from tabulate import tabulate


def to_table(df: pd.DataFrame, format: str = "html"):
    """Convert a pandas dataframe into a table representation.

    * Handles <NA>.
    * Top left cell is df.columns.name or df.index.name or None
    """
    if format != "html":
        raise NotImplementedError("only html tables implemented right now")

    display_df = df.where(pd.notna(df), None)

    first_header = df.columns.name or df.index.name or ""
    header_row = [first_header, *display_df.columns.tolist()]
    rows = [[index] + row.tolist() for index, row in display_df.iterrows()]

    tabulate_data = tabulate(
        rows,
        headers=header_row,
        tablefmt="html",
    )
    return tabulate_data
