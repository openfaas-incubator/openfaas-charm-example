#!/usr/bin/env python3
# Copyright 2020 alex
# See LICENSE file for licensing details.

import logging


from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus
import os
from base64 import b64encode

from pathlib import Path
import yaml
import json

logger = logging.getLogger(__name__)

class OpenfaasCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(namespace=os.environ["JUJU_MODEL_NAME"])
        self._stored.set_default(nats_ip="")
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on["nats-address"].relation_joined, self._on_nats_relation_joined)
        self.framework.observe(self.on["nats-address"].relation_changed, self._on_nats_relation_changed)

    def _on_nats_relation_changed(self, event):
        ip = event.relation.data[event.unit].get("ip")

        if ip == None:
            return
        self._stored.nats_ip = ip

        logger.info("OF - nats says: {}".format(ip))
        self._on_config_changed()

    def _on_nats_relation_joined(self, event):
        ip = event.relation.data[event.unit].get("ip")

        if ip == None:
            return
        self._stored.nats_ip = ip

        logger.info("OF - nats says: {}".format(ip))
        self._on_config_changed()

    def _on_config_changed(self, _=None): 
        logger.info("OpenFaaS config_change")
        # if not self.unit.is_leader():
        #     self.unit.status = ActiveStatus()
        #     return

        nats_ip = self._stored.nats_ip

        if nats_ip == "":
            self.unit.status = BlockedStatus("OpenFaaS needs a NATS relation")
            return

        self.unit.status = MaintenanceStatus('Setting pod spec.')

        logger.info("OpenFaaS building pod spec with nats_ip {}".format(nats_ip))

        pod_spec = self._build_pod_spec()
        self.model.pod.set_spec(pod_spec)
        self.unit.status = ActiveStatus("OpenFaaS pod ready.")

    def _build_pod_spec(self):
        namespace = self._stored.namespace

        # function_crd = {}
        # profiles_crd = {}

        rules = []
        try:
            rules = yaml.load(open(Path('files/rbac_rules.yaml'),"r"), Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print("Error in configuration file:", exc)

        # try:
        #     function_crd = yaml.load(open(Path('files/function_crd.yaml'),"r"), Loader=yaml.FullLoader)
        # except yaml.YAMLError as exc:
        #     print("Error in configuration file:", exc)

        # try:
        #     profiles_crd = yaml.load(open(Path('files/profiles_crd.yaml'),"r"), Loader=yaml.FullLoader)
        # except yaml.YAMLError as exc:
        #     print("Error in configuration file:", exc)

        # logger.debug(json.dumps(function_crd["spec"]))

        username = self.model.config["admin_username"]
        password = self.model.config["admin_password"]

        vol_config = [
            {
            "name": "auth", 
            "mountPath": "/var/secrets", 
            "secret": {"name": "basic-auth"}
            },
        ]

# "functions_provider_url": "http://192.168.0.35:8080",
        spec = {
            "version": 3,
            "kubernetesResources": {
                # "customResourceDefinitions": [
                #     {
                #         "name": function_crd["metadata"]["name"],
                #         "labels": {
                #             "juju-global-resource-lifecycle": "model",
                #         },
                #         "spec": function_crd["spec"],
                #     },
                #     {
                #         "name": profiles_crd["metadata"]["name"],
                #         "labels": {
                #             "juju-global-resource-lifecycle": "model",
                #         },
                #         "spec": profiles_crd["spec"],
                #     },
                # ],
                'secrets': [{
                    'name': 'basic-auth',
                    'type': 'Opaque',
                    'data': {
                        'basic-auth-user': b64encode(username.encode('utf-8')).decode('utf-8'),
                        'basic-auth-password': b64encode(password.encode('utf-8')).decode('utf-8'),
                    }
                }],
            },
            'serviceAccount': {
                'roles': [{
                    'global': True,
                    'rules': rules["rules"],
                }],
            },
            "containers": [
                {
                    "name": self.app.name+"-gateway",
                    "imageDetails": {"imagePath": "openfaas/gateway:0.20.2"},
                    "ports": [{"containerPort": 8080, "protocol": "TCP","name":"gateway"}],
                    "envConfig": {
                        "faas_nats_address": self._stored.nats_ip,
                        "faas_nats_port": "4222",
                        "functions_provider_url": "http://127.0.0.1:8081/",
                        "direct_functions": "false",
                        "basic_auth": "true",
                        "faas_nats_channel": "faas-request",
                        "secret_mount_path": "/var/secrets",
                        "faas_prometheus_host": "192.168.0.35",
                        "faas_prometheus_port": "9090",
                        "auth_pass_body": "false",
                        "auth_proxy_url": "http://127.0.0.1:8083/validate",
                        "scale_from_zero": "false",
                        "direct_functions": "false",
                    },
                    "volumeConfig": vol_config,
                },
                {
                    "name": self.app.name+"-auth-plugin",
                    "imageDetails": {"imagePath": "openfaas/basic-auth-plugin:0.20.2"},
                    "ports": [{"containerPort": 8083, "protocol": "TCP","name":"auth"}],
                    "envConfig": {
                        "basic_auth": "true",
                        "secret_mount_path": "/var/secrets",
                        "port": "8083",
                    },
                    "volumeConfig": vol_config,
                },
                {
                    "name": self.app.name+"-provider",
                    "imageDetails": {"imagePath": "ghcr.io/openfaas/faas-netes:0.12.9"},
                    "ports": [{"containerPort": 8081, "protocol": "TCP","name":"provider"}],
                    "command": ["./faas-netes","-operator=true"],
                    "envConfig": {
                        "port": "8081",
                        "operator": "true",
                        "basic_auth": "true",
                        "function_namespace": namespace,
                        "cluster_role": "true",
                        "profiles_namespace": namespace,
                    },
                    "volumeConfig": vol_config,
                }
            ]
        }

        return spec


if __name__ == "__main__":
    main(OpenfaasCharm)
