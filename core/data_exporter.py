"""
data_exporter.py
-----------------

This module provides helper functions to convert scraped data into
tabular formats and export them to JSON or CSV. It leverages Pandas
to perform conversions with minimal boilerplate. The exported files
can be consumed by downstream analysis tools or loaded into databases.
"""

from __future__ import annotations

from typing import Iterable, List, Dict
import json
import os

import pandas as pd  # type: ignore


def to_dataframe(items: Iterable[Dict[str, str]]) -> pd.DataFrame:
    """
    Convert a sequence of dictionaries to a pandas DataFrame. Each key
    becomes a column and missing keys are filled with NaN.

    Parameters
    ----------
    items : Iterable[Dict[str, str]]
        Sequence of dictionaries representing structured data.

    Returns
    -------
    pandas.DataFrame
        DataFrame representation of the data.
    """
    return pd.DataFrame(list(items))


def export_to_json(df: pd.DataFrame, file_path: str) -> None:
    """
    Export the given DataFrame to a JSON file. The JSON will contain
    an array of objects where each object corresponds to a row in the
    DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to export.
    file_path : str
        Destination path for the JSON file. Existing files will be
        overwritten.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)


def export_to_csv(df: pd.DataFrame, file_path: str) -> None:
    """
    Export the given DataFrame to a CSV file using UTF-8 encoding.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to export.
    file_path : str
        Destination path for the CSV file. Existing files will be
        overwritten.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False, encoding="utf-8")