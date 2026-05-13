from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast
from urllib.parse import quote

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account


class GoogleCalendarError(RuntimeError):
    """Raised when Google Calendar cannot create a usable event."""


@dataclass(frozen=True, slots=True)
class CalendarEvent:
    """Google Calendar event created by the bot."""

    event_id: str
    summary: str
    start_at: datetime
    end_at: datetime
    time_zone: str
    html_link: str


@dataclass(frozen=True, slots=True)
class GoogleCalendarClient:
    """Minimal async client for Google Calendar event creation."""

    service_account_info: dict[str, str]
    calendar_id: str
    time_zone: str
    base_url: str = "https://www.googleapis.com/calendar/v3"

    async def create_event(
        self,
        summary: str,
        start_at: datetime,
        end_at: datetime,
        description: str | None = None,
    ) -> CalendarEvent:
        """Create a timed event in Google Calendar."""
        if self.calendar_id == "primary":
            msg = (
                "GOOGLE_CALENDAR_ID=primary points to the service account calendar. "
                "Use a calendar ID shared with the service account instead."
            )
            raise GoogleCalendarError(msg)

        access_token = await asyncio.to_thread(self._get_access_token)
        event: dict[str, Any] = {
            "summary": summary,
            "start": {
                "dateTime": start_at.isoformat(),
                "timeZone": self.time_zone,
            },
            "end": {
                "dateTime": end_at.isoformat(),
                "timeZone": self.time_zone,
            },
        }
        if description:
            event["description"] = description

        calendar_id = quote(self.calendar_id, safe="")
        url = f"{self.base_url}/calendars/{calendar_id}/events"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=event, headers=headers)

        if response.status_code >= 400:
            msg = (
                f"Google Calendar request failed with status {response.status_code}: "
                f"{response.text[:500]}"
            )
            raise GoogleCalendarError(msg)

        return self._parse_event(response.json(), start_at, end_at)

    def _get_access_token(self) -> str:
        scopes = ["https://www.googleapis.com/auth/calendar"]
        credentials = service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
            self.service_account_info,
            scopes=scopes,
        )
        credentials.refresh(Request())
        if not credentials.token:
            raise GoogleCalendarError("Google service account did not return token.")
        return cast(str, credentials.token)

    def _parse_event(
        self,
        data: dict[str, Any],
        start_at: datetime,
        end_at: datetime,
    ) -> CalendarEvent:
        event_id = data.get("id")
        summary = data.get("summary")
        html_link = data.get("htmlLink")
        if not isinstance(event_id, str):
            raise GoogleCalendarError("Google Calendar event id is missing.")
        if not isinstance(summary, str):
            raise GoogleCalendarError("Google Calendar event summary is missing.")
        if not isinstance(html_link, str) or not html_link:
            raise GoogleCalendarError("Google Calendar event link is missing.")

        return CalendarEvent(
            event_id=event_id,
            summary=summary,
            start_at=start_at,
            end_at=end_at,
            time_zone=self.time_zone,
            html_link=html_link,
        )
