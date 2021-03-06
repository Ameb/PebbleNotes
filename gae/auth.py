import webapp2
from urllib import urlencode
import json, urllib2

from secret import client_id, client_secret
import config

class AuthRedirector(webapp2.RequestHandler):
    def get(self):
        args = self.request.GET
        args["client_id"] = client_id
        args["redirect_uri"] = config.auth_redir_uri
        url = "https://accounts.google.com/o/oauth2/auth?"+urlencode(args)
        self.response.location = url
        self.response.status_int = 302

def query_json(url, data):
    """
    Query JSON data from Google server using POST request.
    Returns only data and ignores result code.
    """
    if not (data is str):
        data = urlencode(data)
    try:
        return json.loads(urllib2.urlopen(url, data).read())
    except urllib2.HTTPError as e: # exception is a file-like object
        return json.loads(e.read())

def json_compactify(data):
    return json.dumps(data, separators=(',',':')) # compact encoding

class AuthCallback(webapp2.RequestHandler):
    """
    This page is called by Google when user finished auth process.
    It receives state (currently unused), code (if success) or error (if failure).
    Then it queries Google for access and refresh tokens and passes them in urlencode form
    to intermediate static page, which will show status and pass data to js code.
    """
    def get(self):
        state = self.request.get("state")
        code = self.request.get("code")
        error = self.request.get("error")
        q = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": config.auth_redir_uri,
            "grant_type": "authorization_code",
        }
        result = query_json("https://accounts.google.com/o/oauth2/token", q)
        url = (config.auth_success_page if "access_token" in result
               else config.auth_failure_page) + "#" + urlencode(result)
        self.response.location = url
        self.response.status_int = 302
        # return result as redirect to static page

class AuthRefresh(webapp2.RequestHandler):
    """
    This page is used by client to refresh their access tokens.
    An access token has lifetime of 1 hour, after that it becomes invalid and
    needs to be refreshed.
    So we receive refresh_token as a parameter
    and return a new access_token with its lifetime as a json result.
    """
    def get(self):
        refresh_token = self.request.get("refresh_token")
        if not refresh_token:
            self.response.status_int = 400
            return
        q = {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        }
        result = query_json("https://accounts.google.com/o/oauth2/token", q)
        self.response.headers['Content-Type'] = "application/json; charset=UTF-8"
        self.response.write(json_compactify(result))
        # return result as JSON

application = webapp2.WSGIApplication([
    ('/auth', AuthRedirector),
    ('/auth/result', AuthCallback),
    ('/auth/refresh', AuthRefresh),
], debug=True)
