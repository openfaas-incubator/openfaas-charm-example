# An example Charm for OpenFaaS

Challenges:

* The OpenFaaS helm chart templated is a 2200 YAML file
* There are ~ 12 objects, each appears to need its own Charm
* Some Pods have more than one container per Pod i.e. sidecar/Pod model
* Secrets are required and need to be shared with each container for basic auth
* A pre-packaged version of Prometheus is used with a specific scrape configuration
* A pre-packaged version of AlertManager is used with a specific configuration
* Services speak to each other over HTTP using a stable service name
* Complex RBAC rules

The above challenges of the above present a considerable amount of effort and research to adapt to the Charm framework.

Examples or documentation of each of these places where the OpenFaaS application goes outside of the "happy path" of [just running a single Grafana Pod](https://github.com/jlounder/training-operator) are critical to a timely and successful PoC.

A default install includes:

```
NAME                READY   UP-TO-DATE   AVAILABLE   AGE
nats                1/1     1            1           10h
queue-worker        1/1     1            1           10h
alertmanager        1/1     1            1           10h
prometheus          1/1     1            1           10h
basic-auth-plugin   1/1     1            1           10h
gateway             1/1     1            1           10h
faas-idler          1/1     1            1           10h
```

Relationships

```
prometheus ->
nats ->
basic-auth-plugin -> basic-auth-secret

gateway -> basic-auth-secret
gateway -> basic-auth-plugin
gateway -> prometheus
gateway -> nats

queue-worker -> gateway
queue-worker -> nats

alertmanager -> basic-auth-secret
alertmanager -> prometheus

faas-idler -> basic-auth-secret
faas-idler -> prometheus
faas-idler -> gateway

```

A minimum version could:

* Turn NATS off for no async messaging - one less dependency. And the queue worker can be held back.
* Turn auth off, but then it shouldn't be used on a public network, this will mean less secret sharing between the dependent microservices like the gateway and Kubernetes provider and the basic-auth plugin could be held back.
* Use defaults from the process instead of supplying all the environment-variables the chart does today.
* Prometheus cannot be disabled, the relationship model looks tricky, perhaps it could be hosted on an external machine for the initial version and hard-coded as an env-var
* The idler could be disabled

* [OpenFaaS chart](https://github.com/openfaas/faas-netes/tree/master/chart/openfaas)

Conceptual diagram, some elements are missing.

![Overview](https://github.com/openfaas/faas/blob/master/docs/of-workflow.png?raw=true)

## Reference examples

https://git.launchpad.net/charm-k8s-postgresql/tree/src/charm.py#n116
https://github.com/camille-rodriguez/metallb-bundle/blob/master/charms/metallb-speaker/src/charm.py#L223

# With local microk8s

```
juju add-model dev1
charmcraft build && juju deploy ./openfaas.charm

# Check results:
microk8s.kubectl logs  pod/openfaas-operator-0 -n dev1 -f

juju status

juju debug-log
```

# With multipass

## Requires additional memory, RAM and adequate CPU

```
multipass launch -m 8G -c 2 -n juju -d 80G
multipass exec juju /bin/bash

sudo snap install microk8s --classic && \
  sudo usermod -a -G microk8s $USER && \
  sudo su $USER

microk8s status --wait-ready && \
 microk8s.enable dns storage && \
 sudo snap install juju --classic && \
 su do snap install charmcraft --beta && \
  juju bootstrap microk8s micro

# Check with
kubectl get pod -A

# Test with
juju add-model dev

# Get IP with
multipass info juju

## Development

charmcraft build

juju deploy ./name.charm
```