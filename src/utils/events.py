"""Calendar-event creation via Microsoft Graph (Teams meeting when online).

Requires the app registration to hold APPLICATION `Calendars.ReadWrite`
(admin-consented; ideally constrained to the sender mailbox with an Exchange
ApplicationAccessPolicy). The event lands on the service sender's calendar as
organizer; `isOnlineMeeting` + teamsForBusiness mints the Teams join link.
"""

import os
from datetime import datetime, timedelta

import requests

from utils.auth import Auth
from _errors.email_send_error import EmailSendError

GRAPH_BASE_URL  = 'https://graph.microsoft.com/v1.0'
REQUEST_TIMEOUT = 30

# Windows time zone id for Graph dateTimeTimeZone values (local time, house rule).
EVENT_TIMEZONE = os.getenv('EVENT_TIMEZONE', 'Pacific Standard Time')


def create_event(
        subject: str,
        start_iso: str,
        attendees: list[str],
        body: str = '',
        duration_minutes: int = 30,
        online_meeting: bool = True,
        auth: Auth | None = None ) -> requests.Response:
    """Create a calendar event with invites; raises EmailSendError on failure."""

    auth    = auth or Auth()
    req_url = f"{GRAPH_BASE_URL}/users/{auth.service_user_id}/events"

    start = datetime.fromisoformat(start_iso)
    end   = start + timedelta(minutes=duration_minutes)

    payload = {
        'subject': subject,
        'body':    {'contentType': 'HTML', 'content': body or subject},
        'start':   {'dateTime': start.strftime('%Y-%m-%dT%H:%M:%S'), 'timeZone': EVENT_TIMEZONE},
        'end':     {'dateTime': end.strftime('%Y-%m-%dT%H:%M:%S'),   'timeZone': EVENT_TIMEZONE},
        'attendees': [
            {'emailAddress': {'address': address}, 'type': 'required'}
            for address in attendees
        ],
    }
    if online_meeting:
        payload['isOnlineMeeting']       = True
        payload['onlineMeetingProvider'] = 'teamsForBusiness'

    headers = {
        'Authorization': f'Bearer {auth.get_token()["access_token"]}',
        'Content-Type':  'application/json',
        'Accept':        'application/json',
    }

    try:
        resp = requests.post(req_url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        raise EmailSendError(f"Request to Microsoft Graph failed: {e}") from e

    if not resp.ok:
        raise EmailSendError(
            "Microsoft Graph rejected the event creation.",
            status_code=resp.status_code,
            response_text=resp.text )

    return resp
