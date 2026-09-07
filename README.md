# Grafana Jetson Monitor

Stack Docker untuk memantau NVIDIA Jetson dan container Docker melalui Grafana, Prometheus, cAdvisor, dan collector berbasis `jetson-stats`.

## Perhatian keamanan

- `jetson_collector/collector.py` mengekspos nomor seri Jetson serta informasi perangkat keras melalui metrik `jetson_info_hardware_info`.
- Grafana mengaktifkan akses anonim (`[auth.anonymous] enabled = true`) dan seluruh layanan memakai host network. Jangan ekspos port ke internet; batasi dengan firewall atau letakkan di belakang reverse proxy yang memakai autentikasi.
- Tidak ditemukan password, API key, token, atau file `.env` aktif dalam repositori. Nilai sensitif pada `grafana.ini` hanya contoh yang dikomentari.
- cAdvisor berjalan dalam mode `privileged` dan membaca filesystem host untuk mengumpulkan metrik container. Jalankan hanya pada host yang tepercaya.

## Prasyarat

- NVIDIA Jetson dengan JetPack dan layanan `jtop` tersedia.
- Docker Engine dan Docker Compose plugin pada Jetson.
- Port `3000`, `3030`, `8080`, dan `9090` belum dipakai.

## Instalasi

```bash
git clone <URL_REPOSITORI> grafana-jetson
cd grafana-jetson
docker compose up -d --build
```

Pastikan semua container berjalan:

```bash
docker compose ps
```

## Akses layanan

| Layanan | URL |
| --- | --- |
| Grafana | `http://<IP-JETSON>:3000` |
| Prometheus | `http://<IP-JETSON>:9090` |
| cAdvisor | `http://<IP-JETSON>:8080` |
| Jetson collector | `http://<IP-JETSON>:3030/metrics` |

Grafana dapat dibuka tanpa login karena akses anonim diaktifkan. Jika login admin diperlukan, kredensial default Grafana pada instalasi baru adalah `admin` / `admin`; segera ubah dan nonaktifkan akses anonim sebelum dipakai di jaringan bersama.

## Konfigurasi Grafana

1. Buka Grafana, lalu tambahkan datasource **Prometheus** dengan URL `http://localhost:9090`.
2. Simpan datasource dan catat UID-nya dari URL halaman datasource.
3. Impor `templates/nvidia-jetson-jtop.json` dan `templates/jetson-cadvisor.json` melalui **Dashboards > New > Import**.
4. Pada setiap dashboard, pilih datasource Prometheus yang baru dibuat. Bila kueri tidak memuat data, ganti seluruh nilai `cfx7ds3p9q03kb` di berkas JSON dengan UID datasource Anda, lalu impor ulang.

Dashboard Jetson menampilkan informasi board, CPU, GPU, RAM, disk, fan, suhu, uptime, dan konsumsi daya. Dashboard cAdvisor menampilkan CPU, memori, jaringan, disk I/O, dan status container Docker.

## Operasional

```bash
# Lihat log seluruh layanan
docker compose logs -f

# Hentikan stack tanpa menghapus data Prometheus
docker compose down

# Hentikan dan hapus volume Grafana serta data Prometheus
docker compose down -v
rm -rf prometheus-data
```

Data Prometheus tersimpan pada direktori `prometheus-data/`, yang tidak dilacak Git. Data Grafana tersimpan pada volume Docker `grafana-storage`.

## Troubleshooting

- `jetson_collector` gagal start: pastikan socket `/run/jtop.sock` ada dan `jtop` berjalan pada host Jetson.
- Endpoint `3030/metrics` tidak merespons: periksa `docker compose logs jetson_collector`.
- Prometheus tidak menampilkan target `UP`: buka `http://<IP-JETSON>:9090/targets` dan periksa port collector atau cAdvisor.
- Dashboard kosong: pastikan datasource Prometheus mengarah ke `http://localhost:9090` dan UID datasource pada dashboard sudah sesuai.
