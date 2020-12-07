#!/usr/bin/env python3
# Copyright 2020 alex
# See LICENSE file for licensing details.

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)

class OpenfaasCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, _=None):
        pod_spec = self._build_pod_spec()
        self.model.pod.set_spec(pod_spec)
        self.unit.status = ActiveStatus("OpenFaaS pod ready.")

    def _build_pod_spec(self):
        spec = {
            "containers": [
                {
                    "name": self.app.name,
                    "imageDetails": {"imagePath": "openfaas/gateway:0.20.2"},
                    "ports": [{"containerPort": 8080, "protocol": "TCP"}],
                    "files": [],
                    "config": {},  # used to store hashes of config file text
                    "envConfig": {
                        "functions_provider_url": "192.168.0.15:8081",
                        "direct_functions": "false",
                        "basic_auth": "false",
                        "faas_prometheus_host": "192.168.0.35",
                        "faas_prometheus_port": "9090"
                    }
                }
            ]
        }

        return spec


if __name__ == "__main__":
    main(OpenfaasCharm)
