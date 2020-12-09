# nats

```bash
(
    export N=7
    juju add-model d$N ;charmcraft build && juju deploy ./nats.charm
    cd ../openfaas-charm/example/
    charmcraft build && juju deploy ./openfaas.charm 

    juju relate openfaas nats
)
```

