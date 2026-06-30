import os
import msal
import requests
from dotenv import load_dotenv

from src._errors.configuration_error import ConfigurationError
from src._errors.authentication_error import AuthenticationError
from src._errors.graph_api_error import GraphApiError

GRAPH_BASE_URL  = 'https://graph.microsoft.com/v1.0'
GRAPH_SCOPE     = ['https://graph.microsoft.com/.default']
REQUEST_TIMEOUT = 30


class Auth:
    """Handles Microsoft Entra ID auth and directory lookups for the email service."""

    def __init__(self):
        self.client_id       = None
        self.tenant_id       = None
        self.client_secret   = None
        self.service_user_id = None

        self._load_env_vars()

        self.app = self._create_conf_client_app()


    def _load_env_vars(self) -> None:
        """Load required credentials from the environment, failing clearly if any are missing."""

        load_dotenv()

        self.client_id       = os.getenv('CLIENT_ID')
        self.tenant_id       = os.getenv('TENANT_ID')
        self.client_secret   = os.getenv('CLIENT_SECRET')
        self.service_user_id = os.getenv('SERVICE_USER_ID')

        missing = [name for name, value in {
            'CLIENT_ID':       self.client_id,
            'TENANT_ID':       self.tenant_id,
            'CLIENT_SECRET':   self.client_secret,
            'SERVICE_USER_ID': self.service_user_id,
        }.items() if not value]

        if missing:
            raise ConfigurationError(f"Missing required environment variable(s): {', '.join(missing)}")


    def _create_conf_client_app(self) -> msal.ConfidentialClientApplication:
        return msal.ConfidentialClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret )


    def get_token(self) -> dict:
        """Acquire an app-only Graph access token, raising AuthenticationError on failure."""

        result = self.app.acquire_token_for_client(scopes=GRAPH_SCOPE)

        if 'access_token' not in result:
            error       = result.get('error', 'unknown_error')
            description = result.get('error_description', 'No error description returned.')
            raise AuthenticationError(f"Could not acquire access token ({error}): {description}")

        return result


    def _auth_headers(self) -> dict:
        return {'Authorization': f'Bearer {self.get_token()["access_token"]}'}


    def get_service_account(self) -> dict:
        """Fetch the configured service account's directory record from Microsoft Graph."""

        req_url = f"{GRAPH_BASE_URL}/users/{self.service_user_id}"

        try:
            resp = requests.get(req_url, headers=self._auth_headers(), timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:
            raise GraphApiError(f"Request to Microsoft Graph failed: {e}") from e

        if not resp.ok:
            raise GraphApiError(
                f"Could not fetch service account '{self.service_user_id}'.",
                status_code=resp.status_code,
                response_text=resp.text )

        return resp.json()


    def get_valid_recipients(self) -> list:
        """Return the lowercased mail addresses of every directory user that has a mailbox."""

        headers    = self._auth_headers()
        recipients = []
        req_url    = f"{GRAPH_BASE_URL}/users?$select=mail&$top=999"

        while req_url:
            try:
                resp = requests.get(req_url, headers=headers, timeout=REQUEST_TIMEOUT)
            except requests.RequestException as e:
                raise GraphApiError(f"Request to Microsoft Graph failed: {e}") from e

            if not resp.ok:
                raise GraphApiError(
                    "Could not fetch directory users.",
                    status_code=resp.status_code,
                    response_text=resp.text )

            data = resp.json()
            for user in data.get('value', []):
                mail = user.get('mail')
                if mail is not None:
                    recipients.append(mail.lower())

            req_url = data.get('@odata.nextLink')

        return recipients
