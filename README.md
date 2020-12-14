## OpenFaaS Charm example

## Introduction

This repo is part of a Proof of Concept using the [Canonical Operator framework](https://github.com/canonical/operator)

The charm is not for production use, is not maintained and is not fully functional.

We are not accepting contributions.

## Components

[OpenFaaS](https://github.com/openfaas/faas/) consists of the following components:

* gateway - the REST API and UI, requires NATS and Prometheus
* gateway.provider - a sidecar which provides a Kubernetes operator for creating functions and secrets for functions
* basic-auth-plugin - can be swapped for SSO/OIDC, but by default provides auth for the REST API
* prometheus - used for auto-scaling decisions and metrics in the REST API / UI
* NATS - for async invocations
* queue-worker - to subscribe to NATS and to invoke functions via the gateway

## Charms

Each charm has its own readme and more detailed information.

* See openfaas operator: [openfaas](openfaas/)
* See NATS operator: [nats-operator](nats-operator/)
* See openfaas-queue-worker: [openfaas-queue-worker](openfaas-queue-worker/)

## Limitations and WIP

* The queue-worker cannot be deployed due to issues with the Operator framework expecting TCP ports.
* The Prometheus charm cannot be deployed, so auto-scaling is not working and neither are metrics. There will be errors in the logs for the gateway, but invocations work.

## Trying OpenFaaS with the example

Providing that charmcraft, juju, and microk8s are set up, you can run the following.

* Change `N=1` to `N=2` for each change made, which needs to be redeployed.
* `add-model` corresponds to a Kubernetes namespace

```bash
(
    export N=1
    juju add-model d$N
    cd nats-operator
    charmcraft build && juju deploy ./nats.charm
    cd ..

    cd openfaas
    charmcraft build && juju deploy ./openfaas.charm 
    cd ..

    juju relate openfaas nats
)
```

Check the status of the components:

```bash
watch "juju status"
```

Follow the juju debug log:

```bash
juju debug-log
```

Download [faas-cli](https://github.com/openfaas/faas-cli/releases)

Login to the gateway and deploy a function, setting `OPENFAAS_URL` to the application IP address for "openfaas":

```bash
export OPENFAAS_URL=http://10.0.0.1:8080
```

These values can be overridden in the charm config using "admin_password" and "admin_username", but the defaults are admin/admin. Log in:

```bash
faas-cli login --password admin --username admin
```

Deploy and invoke the function:

```bash
faas-cli store deploy figlet

faas-cli invoke figlet <<< "juju"
```

List functions:

```bash
faas-cli list
```

Open the OpenFaaS UI:

```bash
echo $OPENFAAS_URL
```

## WIP

The openfaas-queue-worker cannot be deployed because the operator framework expects a TCP port to be exposed, and the queue-worker is not a server component, but a pull-based queue subscriber.

```bash
(   
    cd openfaas-queue-worker
    charmcraft build && juju deploy ./openfaas-queue-worker.charm 
    cd ..
    
    juju relate openfaas-queue-worker nats
    )
```