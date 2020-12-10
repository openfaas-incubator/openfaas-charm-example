## OpenFaaS Charm example

* See openfaas operator: [openfaas](openfaas/)
* See NATS operator: [nats-operator](nats-operator/)

Usage:

```bash


(
    export N=14
    juju add-model d$N
    cd nats-operator
    charmcraft build && juju deploy ./nats.charm
    cd ..

    cd openfaas
    charmcraft build && juju deploy ./openfaas.charm 
    cd ..
    
    juju relate openfaas nats
)

juju status
juju debug-log









```