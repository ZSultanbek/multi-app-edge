"""
A long-running process that holds a database connection open between requests
will eventually find that connection dead - the server restarted, a firewall
dropped an idle socket, the connection simply aged out. The symptom is an
InterfaceError hours after everything looked fine.

Django's own request cycle handles this, but a worker or bot process that
touches the ORM outside a request does not get that for free. This middleware
makes the behaviour explicit at the boundary.
"""

from django.db import close_old_connections


class CloseStaleConnectionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        close_old_connections()
        response = self.get_response(request)
        close_old_connections()
        return response
