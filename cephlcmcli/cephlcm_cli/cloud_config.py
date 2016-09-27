#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This module has cloud-config command implementation."""


from __future__ import absolute_import
from __future__ import unicode_literals

import click

from cephlcm_cli import main
from cephlcmlib import cloud_config


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
"""Context settings for the Click."""


@main.cli.command(name="cloud-config")
@click.option(
    "--user", "-u",
    default="ansible",
    help="User to use with Ansible. Default is 'ansible'."
)
@click.option(
    "--group", "-g",
    default=None,
    help="Group of user to use with Ansible. Default is username."
)
@click.option(
    "--base64", "-b",
    is_flag=True,
    help="Encode to base64."
)
@click.argument("public_key_filename", type=click.File(lazy=False))
@click.argument("server_discovery_token", type=click.UUID)
@click.pass_context
def cli(ctx, public_key_filename, server_discovery_token, user, group, base64):
    """Generates config for cloud-init.

    This command generates cloud-init user-data config to setup CephLCM
    hosts. This config creates required user, put your provided public
    key to the authorized_keys and register server to CephLCM with
    required parameters.

    These settings are possible to setup using commandline parameter,
    but if you want, you can set environment variables:

    URL is full URL to /v1/server endpoint.
    SERVER_DISCOVERY_TOKEN is a token set in configuration file of
    CephLCM

    \b
        - CEPHLCM_TIMEOUT  - this environment variable sets timeout.
        - CEPHLCM_DEBUG    - this environment variable sets debug mode.
    """

    url = ctx.obj["client"]._make_url("/v1/server/")
    public_key = public_key_filename.read().strip()
    server_discovery_token = str(server_discovery_token)

    config = cloud_config.generate_cloud_config(
        url=ctx.obj["client"]._make_url("/v1/server/"),
        server_discovery_token=server_discovery_token,
        public_key=public_key_filename.read().strip(),
        username=user,
        usergroup=group,
        timeout=ctx.obj["timeout"],
        debug=ctx.obj["debug"],
        to_base64=base64
    )

    click.echo(config.rstrip())