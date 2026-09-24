"""
WSGI entry point, with the piece that makes a path prefix actually work.

FORCE_SCRIPT_NAME tells Django which prefix to PUT INTO the URLs it
generates. It does not remove that prefix from incoming requests: PATH_INFO
still arrives as /alpha/healthz, so the URLconf looks for a route called
"alpha/healthz" and returns 404 - while logging the confusing doubled path
/alpha/alpha/healthz, because request.path is SCRIPT_NAME + PATH_INFO.

Splitting the path is the server's job, not Django's. This middleware does
it: SCRIPT_NAME gets the prefix, PATH_INFO gets the rest.

The prefix comes from the X-Script-Name header the proxy sets, falling back
to DJANGO_SCRIPT_NAME so that direct requests - container healthchecks, a
curl from inside the network - behave the same way as proxied ones.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


class ScriptNamePrefix:
    def __init__(self, app, fallback=""):
        self.app = app
        self.fallback = fallback.rstrip("/")

    def __call__(self, environ, start_response):
        prefix = (environ.get("HTTP_X_SCRIPT_NAME") or self.fallback).rstrip("/")
        if prefix:
            path = environ.get("PATH_INFO", "")
            if path.startswith(prefix):
                environ["SCRIPT_NAME"] = prefix
                environ["PATH_INFO"] = path[len(prefix):] or "/"
        return self.app(environ, start_response)


application = ScriptNamePrefix(
    get_wsgi_application(),
    fallback=os.environ.get("DJANGO_SCRIPT_NAME", ""),
)
