## OpenFaaS Charm example

* See openfaas operator: [openfaas](openfaas/)
* See NATS operator: [nats-operator](nats-operator/)

Usage:

```bash
(
    export N=8
    juju add-model d$N
    cd nats-operator
    charmcraft build && juju deploy ./nats.charm
    cd ..

    cd openfaas
    charmcraft build && juju deploy ./openfaas.charm 

    juju relate openfaas nats
)

juju status
juju debug-log
```
