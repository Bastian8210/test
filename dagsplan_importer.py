"""Command line utility to OCR a dagsplan, analyze it heuristically, and export to calendar formats."""
import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python <3.9 not supported in this project
    ZoneInfo = None  # type: ignore

try:
    from pdf2image import convert_from_path
except ImportError:  # pragma: no cover - optional dependency
    convert_from_path = None  # type: ignore

import pytesseract
from PIL import Image


SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"}


@dataclass
class CalendarEvent:
    """Representation of a calendar event."""

    title: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    description: Optional[str] = None

@dataclass
class AnalyzerResult:
    """Structured result produced by :class:`DagsplanAnalyzer`."""

    events: List[CalendarEvent]
    notes: List[str]


class DagsplanAnalyzer:
    """Extract calendar events from OCRed dagsplan text without external APIs."""

    TIME_RANGE_RE = re.compile(
        r"(?P<start>\d{1,2}[:.]\d{2})\s*(?:-|–|—|til|to)\s*(?P<end>\d{1,2}[:.]\d{2})",
        re.IGNORECASE,
    )
    SINGLE_TIME_RE = re.compile(r"^(?P<time>\d{1,2}[:.]\d{2})\s*(?:-|:)?\s*(?P<title>.+)$")
    DATE_RE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})(?:[./-](\d{2,4}))?\b")
    MONTH_NAMES = {
        "januar": 1,
        "februar": 2,
        "mars": 3,
        "april": 4,
        "mai": 5,
        "juni": 6,
        "juli": 7,
        "august": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "desember": 12,
    }
    MONTH_NAME_RE = re.compile(
        r"(\d{1,2})\s+(januar|februar|mars|april|mai|juni|juli|august|september|oktober|november|desember)(?:\s+(\d{4}))?",
        re.IGNORECASE,
    )

    def __init__(self, timezone_name: str, fallback_date: Optional[str] = None):
        self.timezone_name = timezone_name
        self.tzinfo = self._load_timezone(timezone_name)
        self.fallback_date = self._parse_fallback_date(fallback_date)
        self.default_duration = timedelta(hours=1)

    @staticmethod
    def _load_timezone(timezone_name: str) -> Optional[ZoneInfo]:
        if ZoneInfo is None:  # pragma: no cover - Python <3.9 safeguard
            return None
        try:
            return ZoneInfo(timezone_name)
        except Exception:  # pragma: no cover - runtime guard
            return None

    @staticmethod
    def _parse_fallback_date(raw: Optional[str]) -> Optional[date]:
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError as exc:  # pragma: no cover - runtime guard
            raise ValueError("--date must be provided as YYYY-MM-DD") from exc

    def analyze(self, extracted_text: str) -> AnalyzerResult:
        """Parse dagsplan text into events using lightweight heuristics."""

        target_date = self._detect_date(extracted_text)
        events: List[CalendarEvent] = []
        notes: List[str] = []

        for line in extracted_text.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue

            match = self.TIME_RANGE_RE.search(cleaned)
            if match:
                start_time = self._parse_time(match.group("start"))
                end_time = self._parse_time(match.group("end"))

                start_dt = datetime.combine(target_date, start_time)
                end_dt = datetime.combine(target_date, end_time)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

                description = cleaned[match.end() :].strip(" -:\t")
                title = description or "Aktivitet"
            else:
                single = self.SINGLE_TIME_RE.match(cleaned)
                if not single:
                    notes.append(cleaned)
                    continue

                start_time = self._parse_time(single.group("time"))
                start_dt = datetime.combine(target_date, start_time)
                end_dt = start_dt + self.default_duration
                title = single.group("title").strip() or "Aktivitet"

            if self.tzinfo is not None:
                start_dt = start_dt.replace(tzinfo=self.tzinfo)
                end_dt = end_dt.replace(tzinfo=self.tzinfo)

            events.append(
                CalendarEvent(
                    title=title,
                    start=start_dt,
                    end=end_dt,
                )
            )

        return AnalyzerResult(events=events, notes=notes)

    def _detect_date(self, text: str) -> date:
        # Numeric formats like 12.03.2024 or 12/03/24
        for match in self.DATE_RE.finditer(text):
            day, month, year = match.groups()
            day_i = int(day)
            month_i = int(month)
            year_i = self._normalize_year(year)
            try:
                return date(year_i, month_i, day_i)
            except ValueError:
                continue

        # Formats like 12 mars 2024
        for match in self.MONTH_NAME_RE.finditer(text):
            day, month_name, year = match.groups()
            month_i = self.MONTH_NAMES[month_name.lower()]
            day_i = int(day)
            year_i = self._normalize_year(year)
            try:
                return date(year_i, month_i, day_i)
            except ValueError:
                continue

        if self.fallback_date:
            return self.fallback_date

        today = date.today()
        return today

    @staticmethod
    def _normalize_year(year: Optional[str]) -> int:
        if not year:
            return date.today().year
        year_i = int(year)
        if year_i < 100:
            return 2000 + year_i
        return year_i

    @staticmethod
    def _parse_time(value: str) -> time:
        normalized = value.replace(".", ":")
        hour_str, minute_str = normalized.split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
        return time(hour=hour, minute=minute)


def read_image(path: Path) -> Iterable[Image.Image]:
    """Read an image or PDF and yield PIL Image objects for OCR."""

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        if convert_from_path is None:
            raise RuntimeError(
                "Reading PDF dagsplan files requires the 'pdf2image' package. Install it and ensure poppler is available."
            )
        for page in convert_from_path(str(path)):
            yield page
    elif suffix in SUPPORTED_IMAGE_SUFFIXES:
        yield Image.open(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def extract_text(source: Path, lang: str = "nor") -> str:
    """Use Tesseract OCR to extract text from all pages/images."""

    texts: List[str] = []
    for image in read_image(source):
        texts.append(pytesseract.image_to_string(image, lang=lang))
    return "\n".join(texts)


def export_to_ics(events: Iterable[CalendarEvent], output: Path) -> None:
    """Write the parsed events to an ICS calendar file."""

    lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//Dagsplan Importer//EN",
        "VERSION:2.0",
    ]

    for event in events:
        uid = f"{abs(hash((event.title, event.start, event.end)))}@dagsplan"
        start_dt = event.start
        end_dt = event.end
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        start_utc = start_dt.astimezone(timezone.utc)
        end_utc = end_dt.astimezone(timezone.utc)

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}",
                f"DTEND:{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
                f"SUMMARY:{event.title}",
            ]
        )
        if event.location:
            lines.append(f"LOCATION:{event.location}")
        if event.description:
            lines.append(f"DESCRIPTION:{event.description}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    output.write_text("\n".join(lines), encoding="utf-8")


def create_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the dagsplan image or PDF")
    parser.add_argument("--tesseract-lang", default="nor", help="Language code for Tesseract OCR (default: nor)")
    parser.add_argument(
        "--timezone",
        default="Europe/Oslo",
        help="Timezone to apply when events are missing timezone information",
    )
    parser.add_argument(
        "--date",
        help="Fallback date to use (YYYY-MM-DD) if the dagsplan text does not contain a date",
    )
    parser.add_argument(
        "--calendar",
        choices=["ics", "google", "outlook"],
        default="ics",
        help="Calendar destination. Google and Outlook export an ICS file that can be imported.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dagsplan.ics"),
        help="Output file for the generated calendar (default: dagsplan.ics)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = create_arg_parser()
    args = parser.parse_args(argv)

    text = extract_text(args.source, lang=args.tesseract_lang)
    analyzer = DagsplanAnalyzer(timezone_name=args.timezone, fallback_date=args.date)
    result = analyzer.analyze(text)
    events = result.events

    if args.calendar in {"ics", "google", "outlook"}:
        export_to_ics(events, args.output)
        print(f"Wrote {len(events)} events to {args.output}.")
        if args.calendar in {"google", "outlook"}:
            print(
                "Import the ICS file into your calendar provider manually."
                " Google Calendar: Settings and Import. Outlook: File > Open & Export > Import/Export."
            )
    else:  # pragma: no cover - future extension point
        raise ValueError(f"Unsupported calendar type: {args.calendar}")

    if result.notes:
        print("Additional notes from dagsplan:\n" + "\n".join(result.notes))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
