import json
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

from django.conf import settings

from captcha.constants import DEFAULT_RECAPTCHA_DOMAIN

RECAPTCHA_SUPPORTED_LANUAGES = ("en", "nl", "fr", "de", "pt", "ru", "es", "tr")


class RecaptchaResponse:
    def __init__(self, is_valid, error_codes=None, extra_data=None):
        self.is_valid = is_valid
        self.error_codes = error_codes or []
        self.extra_data = extra_data or {}


def recaptcha_request(params):
    request_object = Request(
        url="https://%s/recaptcha/api/siteverify"
        % getattr(settings, "RECAPTCHA_DOMAIN", DEFAULT_RECAPTCHA_DOMAIN),
        data=params,
        headers={
            "Content-type": "application/x-www-form-urlencoded",
            "User-agent": "reCAPTCHA Django",
        },
    )

    # Add proxy values to opener if needed.
    opener_args = []
    proxies = getattr(settings, "RECAPTCHA_PROXY", {})
    if proxies:
        opener_args = [ProxyHandler(proxies)]
    opener = build_opener(*opener_args)

    # Get response from POST to Google endpoint.
    return opener.open(
        request_object,
        timeout=getattr(settings, "RECAPTCHA_VERIFY_REQUEST_TIMEOUT", 10),
    )


def submit(recaptcha_response, private_key, remoteip):
    """
    Submits a reCAPTCHA request for verification. Returns RecaptchaResponse
    for the request

    recaptcha_response -- The value of reCAPTCHA response from the form
    private_key -- your reCAPTCHA private key
    remoteip -- the user's ip address
    """
    params = urlencode(
        {
            "secret": private_key,
            "response": recaptcha_response,
            "remoteip": remoteip,
        }
    )

    params = params.encode("utf-8")

    response = recaptcha_request(params)
    data = json.loads(response.read().decode("utf-8"))
    response.close()
    return RecaptchaResponse(
        is_valid=data.pop("success"),
        error_codes=data.pop("error-codes", None),
        extra_data=data,
    )


def recaptcha_enterprise_request(params, google_project_id, google_server_api_key):
    # v1beta1 allows auth by API key
    url = f"https://recaptchaenterprise.googleapis.com/v1beta1/projects/{google_project_id}/assessments?key={google_server_api_key}"
    request_object = Request(
        url=url,
        data=params,
        headers={
            "Content-type": "application/json",
            "User-agent": "reCAPTCHA Django",
        },
    )

    # Add proxy values to opener if needed.
    opener_args = []
    proxies = getattr(settings, "RECAPTCHA_PROXY", {})
    if proxies:
        opener_args = [ProxyHandler(proxies)]
    opener = build_opener(*opener_args)

    # Get response from POST to Google endpoint.
    return opener.open(
        request_object,
        timeout=getattr(settings, "RECAPTCHA_VERIFY_REQUEST_TIMEOUT", 10),
    )


def submit_enterprise(recaptcha_response, private_key, google_server_api_key,
                      google_project_id, expected_action):
    recaptcha_payload = json.dumps({
        "event": {
            "token": recaptcha_response,
            # need to let the client pass this along
            "siteKey": private_key,
            "expectedAction": expected_action,
        }
    })
    recaptcha_payload = recaptcha_payload.encode('utf-8')

    response = recaptcha_enterprise_request(recaptcha_payload,
                                            google_server_api_key,
                                            google_project_id)
    data = json.loads(response.read().decode("utf-8"))
    response.close()
    print(data)
    import pdb; pdb.set_trace();
    return RecaptchaResponse(
        is_valid=data.pop("success"),
        error_codes=data.pop("error-codes", None),
        extra_data=data,
    )
