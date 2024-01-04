from __future__ import annotations

import datetime
from html import unescape
from typing import Optional

from .types import NoteDataDict


class Note(str):
    """Stores information about a note"""

    _note_data: NoteDataDict

    def __new__(cls, note_data: NoteDataDict) -> Note:
        # I'm not sure I understand why this is double-encoded, but it is?
        self = super().__new__(cls, unescape(unescape(note_data["body"])))  # type: ignore
        self._note_data = note_data
        return self

    @property
    def type(self) -> Optional[str]:
        """Type"""
        return self._note_data.get("type", None)

    @property
    def date(self) -> Optional[datetime.date]:
        """Date"""
        date_str = self._note_data.get("date")

        if not date_str:
            return None

        return datetime.datetime.strptime(
            date_str,
            "%Y-%m-%d",
        ).date()

    def as_dict(self):
        """Returns data as a dictionary."""
        return self._note_data
