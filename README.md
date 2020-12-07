# With local microk8s

```
juju add-model dev1
charmcraft build && juju deploy ./openfaas.charm
microk8s.kubectl logs  pod/openfaas-operator-0 -n dev1 -f
```

# With multipass

## Requires additional memory, RAM and adequate CPU
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