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

class OpenfaasQueueWorkerCharm(CharmBase):
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

        logger.info("queue-worker - nats says: {}".format(ip))
        self._on_config_changed()

    def _on_nats_relation_joined(self, event):
        ip = event.relation.data[event.unit].get("ip")

        if ip == None:
            return
        self._stored.nats_ip = ip

        logger.info("queue-worker - nats says: {}".format(ip))
        self._on_config_changed()

    def _on_config_changed(self, _=None): 
        logger.info("queue-worker config_change")
        # if not self.unit.is_leader():
        #     self.unit.status = ActiveStatus()
        #     return

        nats_ip = self._stored.nats_ip

        if nats_ip == "":
            self.unit.status = BlockedStatus("queue-worker needs a NATS relation")
            return

        self.unit.status = MaintenanceStatus('Setting pod spec.')

        logger.info("queue-worker building pod spec with nats_ip {}".format(nats_ip))

        pod_spec = self._build_pod_spec()
        self.model.pod.set_spec(pod_spec)
        self.unit.status = ActiveStatus("queue-worker pod ready.")

    def _build_pod_spec(self):
        namespace = self._stored.namespace

        vol_config = [
            {
            "name": "auth", 
            "mountPath": "/var/secrets", 
            "secret": {"name": "basic-auth"}
            },
        ]

        # env:
        # - name: faas_nats_address
        #   value: "nats.openfaas.svc.cluster.local"
        # - name: faas_nats_channel
        #   value: "faas-request"
        # - name: faas_nats_queue_group
        #   value: "faas"
        # - name: faas_gateway_address
        #   value: "gateway.openfaas.svc.cluster.local"
        # - name: "gateway_invoke"
        #   value: "true"
        # - name: faas_function_suffix
        #   value: ".openfaas-fn.svc.cluster.local"
        # - name: max_inflight
        #   value: "1"
        # - name: ack_wait    # Max duration of any async task / request
        #   value: 60s
        # - name: secret_mount_path
        #   value: "/var/secrets"
        # - name: basic_auth
        #   value: "true"

        spec = {
            "version": 3,
            "omitServiceFrontend": True,
            "containers": [
                {
                    "name": self.app.name,
                    "imageDetails": {"imagePath": "openfaas/queue-worker:0.11.2"},
                    "envConfig": {
                        "basic_auth": "true",
                        "secret_mount_path": "/var/secrets",
                        "port": "8083",
                        "faas_nats_address": "nats",
                        "faas_nats_channel": "faas-request",
                        "faas_nats_queue_group": "faas",
                        "faas_gateway_address": "gateway",
                        "gateway_invoke": "true",
                        "faas_function_suffix": "openfaas-fn",
                        "max_inflight": "1",
                        "ack_wait": "60s",
                    },
                    "volumeConfig": vol_config,
                },
            ]
        }

        return spec

if __name__ == "__main__":
    main(OpenfaasQueueWorkerCharm)
