# Grafana Jetson Monitor

Docker stack for monitoring NVIDIA Jetson hardware and Docker containers with Grafana, Prometheus, cAdvisor, and a `jetson-stats` collector.

## Security Notes

- `jetson_collector/collector.py` exposes the Jetson serial number and hardware details through the `jetson_info_hardware_info` metric.
- Grafana has anonymous access enabled (`[auth.anonymous] enabled = true`) and every service uses host networking. Do not expose these ports to the internet; restrict access with a firewall or place the stack behind an authenticated reverse proxy.
- No active passwords, API keys, tokens, or `.env` files are stored in this repository. Sensitive values in `grafana.ini` are commented examples only.
- cAdvisor runs in privileged mode and reads the host filesystem to collect container metrics. Run it only on trusted hosts.

## Prerequisites

- An NVIDIA Jetson device with JetPack and the `jtop` service available.
- Docker Engine and the Docker Compose plugin installed on the Jetson device.
- Ports `3000`, `3030`, `8080`, and `9090` available on the host.

## Installation

```bash
git clone <REPOSITORY_URL> grafana-jetson
cd grafana-jetson
docker compose up -d --build
```

Verify that all containers are running:

```bash
docker compose ps
```

## Service URLs

| Service | URL |
| --- | --- |
| Grafana | `http://<JETSON_IP>:3000` |
| Prometheus | `http://<JETSON_IP>:9090` |
| cAdvisor | `http://<JETSON_IP>:8080` |
| Jetson collector | `http://<JETSON_IP>:3030/metrics` |

Grafana is accessible without login because anonymous access is enabled. If an administrator login is needed, a fresh Grafana installation uses the default credentials `admin` / `admin`; change them immediately and disable anonymous access before using the stack on a shared network.

## Grafana Setup

1. Open Grafana and add a **Prometheus** data source with URL `http://localhost:9090`.
2. Save the data source and note its UID from the data source page URL.
3. Import `templates/nvidia-jetson-jtop.json` and `templates/jetson-cadvisor.json` through **Dashboards > New > Import**.
4. Select the new Prometheus data source in each dashboard. If queries do not return data, replace every `cfx7ds3p9q03kb` value in the JSON files with the new data source UID, then import them again.

The Jetson dashboard shows board information, CPU, GPU, RAM, disk, fan, temperature, uptime, and power usage. The cAdvisor dashboard shows Docker CPU, memory, network, disk I/O, and container status metrics.

## Operations

```bash
# Follow logs from all services
docker compose logs -f

# Stop the stack without deleting Prometheus data
docker compose down

# Stop the stack and delete Grafana volumes and Prometheus data
docker compose down -v
rm -rf prometheus-data
```

Prometheus data is stored in `prometheus-data/`, which is ignored by Git. Grafana data is stored in the Docker volume `grafana-storage`.

## Troubleshooting

- `jetson_collector` fails to start: confirm that `/run/jtop.sock` exists and `jtop` is running on the Jetson host.
- The `3030/metrics` endpoint does not respond: check `docker compose logs jetson_collector`.
- Prometheus targets are not `UP`: open `http://<JETSON_IP>:9090/targets` and check the collector and cAdvisor ports.
- A dashboard is empty: confirm that the Prometheus data source URL is `http://localhost:9090` and its UID matches the dashboard JSON.
