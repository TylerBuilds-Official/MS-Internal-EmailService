import requests

from utils.auth import Auth
from _errors.email_send_error import EmailSendError

GRAPH_BASE_URL  = 'https://graph.microsoft.com/v1.0'
REQUEST_TIMEOUT = 30


def send_email(payload: dict, auth: Auth | None = None) -> requests.Response:
    """Send a composed message via Microsoft Graph, raising EmailSendError on failure."""

    auth    = auth or Auth()
    req_url = f"{GRAPH_BASE_URL}/users/{auth.service_user_id}/sendMail"

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
            "Microsoft Graph rejected the sendMail request.",
            status_code=resp.status_code,
            response_text=resp.text )

    return resp
