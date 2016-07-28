# -*- coding: ut-8 -*-
"""Library to work with CephLCM API."""


from __future__ import absolute_import
from __future__ import unicode_literals

from cephlcmlib.client import V1Client
from cephlcmlib.modelclient import V1ModelClient


Client = V1Client
"""An actual JSON client."""

ModelClient = V1ModelClient
"""An actual Model client."""
