# Kubernetes Grafana dashboards

These are the official Kubernetes Views dashboards imported into the local Grafana instance:

| File | Dashboard | Grafana ID | Imported UID |
| --- | --- | ---: | --- |
| `global.json` | Kubernetes / Views / Global | 15757 | `k8s_views_global` |
| `namespaces.json` | Kubernetes / Views / Namespaces | 15758 | `k8s_views_ns` |
| `nodes.json` | Kubernetes / Views / Nodes | 15759 | `k8s_views_nodes` |
| `pods.json` | Kubernetes / Views / Pods | 15760 | `k8s_views_pods` |

The dashboards use the Prometheus datasource placeholder from the upstream files. During import it was mapped to the local Mimir datasource with UID `prom`.

Open them from Grafana:

- `http://grafana.localhost/d/k8s_views_global/kubernetes-views-global`
- `http://grafana.localhost/d/k8s_views_ns/kubernetes-views-namespaces`
- `http://grafana.localhost/d/k8s_views_nodes/kubernetes-views-nodes`
- `http://grafana.localhost/d/k8s_views_pods/kubernetes-views-pods`

Sources:

- https://grafana.com/grafana/dashboards/15757-kubernetes-views-global/
- https://grafana.com/grafana/dashboards/15758-kubernetes-views-namespaces/
- https://grafana.com/grafana/dashboards/15759-kubernetes-views-nodes/
- https://grafana.com/grafana/dashboards/15760-kubernetes-views-pods/
