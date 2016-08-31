# -*- coding: utf-8 -*-
"""Playbook plugin to deploy Ceph cluster."""


import base64
import os
import os.path
import posixpath
import struct
import time

import netaddr

from cephlcm.common import log
from cephlcm.common import playbook_plugin


DESCRIPTION = """\
Ceph cluster deployment playbook.

This plugin deploys Ceph cluster into a set of servers. After sucessful
deployment, cluster model will be updated.
""".strip()
"""Plugin description."""

LOG = log.getLogger(__name__)
"""Logger."""


class DeployCluster(playbook_plugin.Playbook):

    NAME = "Deploy Ceph cluster"
    DESCRIPTION = DESCRIPTION
    PUBLIC = True
    REQUIRED_SERVER_LIST = True

    PLAYBOOK_FILENAME = os.path.join("playbooks", "site.yml")

    def make_playbook_configuration(self, cluster, servers):
        if cluster.configuration.state or cluster.server_list:
            # TODO(Sergey Arkhipov): Raise proper exception here
            # We deploy only empty cluster without configuration.
            raise Exception

        global_vars = self.make_global_vars(cluster, servers)
        inventory = self.make_inventory(cluster, servers)

        return global_vars, inventory

    def make_global_vars(self, cluster, servers):
        result = {
            "ceph_{0}".format(self.config["install"]["source"]): True,
            "journal_collocation": self.config["journal"]["collocation"],
            "journal_size": self.config["journal"]["size"],
            "cluster_network": self.config["networks"]["cluster"],
            "public_network": self.config["networks"]["public"],
            "os_tuning_params": [],
            "fsid": cluster.model_id,
            "cluster": cluster.model_id
        }
        if self.config["install"]["source"] == "stable":
            result["ceph_stable_release"] = self.config["install"]["release"]

        for family, values in self.config["os"].items():
            for param, value in values.items():
                parameter = {
                    "name": ".".join([family, param]),
                    "value": value
                }
                result["os_tuning_params"].append(parameter)

        return result

    def make_inventory(self, cluster, servers):
        groups = self.get_inventory_groups(servers)
        inventory = {"_meta": {"hostvars": {}}}
        secret = self.generate_monitor_secret()

        for name, group_servers in groups.items():
            inventory[name] = [srv.ip for srv in group_servers]
        for srv in servers:
            hostvars = inventory["_meta"]["hostvars"].setdefault(srv.ip, {})
            hostvars["monitor_interface"] = self.get_ifname(srv)
            hostvars["devices"] = self.get_devices(srv)
            hostvars["ansible_user"] = srv.username
            hostvars["monitor_secret"] = secret

        return inventory

    def get_inventory_groups(self, servers):
        # TODO(Sergey Arkhipov): Well, create proper configuration.
        # This enough for demo.

        result = {
            "mons": [servers[0]],
            "osds": servers[1:],
            "rgws": [],
            "mdss": [],
            "nfss": [],
            "rbd_mirrors": [],
            "clients": [],
            "iscsi_gw": []
        }
        if self.config["rest_api"]:
            result["restapis"] = result["mons"]

        return result

    def get_ifname(self, srv):
        cluster_network = netaddr.IPNetwork(self.config["networks"]["cluster"])

        for name in srv.facts["ansible_interfaces"]:
            interface = srv.facts["ansible_{0}".format(name)]
            addr = interface.get("ipv4", {}).get("address")
            if not addr:
                continue
            try:
                addr = netaddr.IPAddress(addr)
            except Exception as exc:
                LOG.warning("Cannot convert %s to ip address: %s", addr, exc)
            else:
                if addr in cluster_network:
                    return interface["device"]

        raise ValueError("Cannot find suitable interface for server %s",
                         srv.model_id)

    def get_devices(self, srv):
        mounts = {mount["device"] for mount in srv.facts["ansible_mounts"]}
        mounts = {posixpath.basename(mount) for mount in mounts}

        devices = []
        for name, data in srv.facts["ansible_devices"].items():
            partitions = set(data["partitions"])
            if not partitions or not (partitions & mounts):
                devices.append(posixpath.join("/", "dev", name))

        return devices

    def generate_monitor_secret(self):
        key = os.urandom(16)
        header = struct.pack("<hiih", 1, int(time.time()), 0, len(key))
        secret = base64.b64encode(header + key)

        return secret
