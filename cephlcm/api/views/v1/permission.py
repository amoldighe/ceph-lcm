# -*- coding: utf-8 -*-
"""Small API to list permissions available in application."""


from cephlcm.api import auth
from cephlcm.api.views import generic
from cephlcm.common.models import role


class PermissionView(generic.ModelView):

    decorators = [
        auth.require_authorization("api", "view_role"),
        auth.require_authentication
    ]

    NAME = "permission"
    ENDPOINT = "/permission/"

    def get(self):
        permissions = role.PermissionSet(role.PermissionSet.KNOWN_PERMISSIONS)
        permissions = permissions.make_api_structure()
        permissions = [
            {"name": k, "permissions": v} for k, v in permissions.items()]

        return {"items": permissions}
