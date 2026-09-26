# TALENTRA.ID — Panduan Penerapan Vercel Free-Tier
## GitHub + Vercel Hobby + Neon PostgreSQL + Vercel Blob (Private)

Dokumen ini adalah panduan otoritatif untuk menerapkan TALENTRA.ID secara mandiri ke infrastruktur gratis:
- **Source Control**: GitHub
- **Application Host**: Vercel (Hobby Tier — Next.js + Serverless FastAPI)
- **Database**: Neon Serverless PostgreSQL (Free Tier)
- **Object Storage**: Vercel Blob (Private Storage)

Tidak memerlukan server VPS, daemon Docker, MongoDB, MinIO, ataupun kartu kredit untuk pengujian awal skala sekolah/kompetisi.

---

## 1. Arsitektur Penerapan

```text
                    GitHub Repository
                           │
                           ▼
                    Vercel Project
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
     Next.js                           FastAPI Function
  (Frontend App)                        (`api/index.py`)
        │                                     │
        ├──────────────────┬──────────────────┤
        │                  │                  │
        ▼                  ▼                  ▼
   Vercel Blob        Neon PostgreSQL     Session & RBAC
 (Private Bukti &   (Seluruh Data Siswa,  (Server-Enforced
     File CV)         Portofolio & CV)     di PostgreSQL)
```

---

## 2. Variabel Lingkungan Vercel (Environment Variables)

Konfigurasikan variabel berikut pada menu **Project Settings > Environment Variables** di Dashboard Vercel:

### A. Rahasia Aplikasi (App Secrets — Enkripsi Ketat)
| Variabel | Lingkungan | Tujuan / Keterangan |
| :--- | :--- | :--- |
| `DATABASE_URL` | Production, Preview | Neon Pooled connection string (`postgresql+asyncpg://...pooler...`) |
| `JWT_SECRET_KEY` | Production, Preview | Kunci rahasia minimal 32 karakter untuk enkripsi token sesi & HMAC internal |
| `IDENTIFIER_LOOKUP_PEPPER` | Production, Preview | Pepper HMAC untuk anonimisasi NISN / NIP di database |
| `CV_VERIFICATION_TOKEN_PEPPER` | Production, Preview | Pepper rahasia untuk hash token verifikasi publik QR |

### B. Konfigurasi Aplikasi (App Config)
| Variabel | Nilai Contoh | Lingkungan | Keterangan |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | `production` | Production, Preview | Mode lingkungan |
| `REPOSITORY_BACKEND` | `postgres` | Production, Preview | Menggunakan PostgreSQL Neon |
| `OBJECT_STORAGE_PROVIDER` | `vercel_blob` | Production, Preview | Provider storage |
| `FREE_TIER_MODE` | `true` | Production, Preview | Mengaktifkan proteksi kuota free-tier |
| `STORAGE_SOFT_LIMIT_BYTES` | `209715200` | Production, Preview | Soft limit storage (200 MB) |
| `CV_PDF_MAX_BYTES` | `4194304` | Production, Preview | Batas aman payload CV PDF (4 MB) |
| `DB_POOL_CLASS` | `queue` | Production, Preview | `queue` (pool_size=2) atau `nullpool` |
| `COOKIE_SECURE` | `true` | Production, Preview | Enforce HTTPS cookie |
| `ENABLE_DEMO_AUTH` | `false` | Production, Preview | Wajib false di produksi |
| `PUBLIC_APP_URL` | `https://talentra.vercel.app` | Production | URL domain produksi utama |
| `ALLOWED_ORIGINS` | `https://talentra.vercel.app` | Production | Origin CORS yang diizinkan |

### C. Identitas Blob Terkelola Vercel (Vercel-Managed Blob Identity)
*Jangan menyalin atau menempel token OIDC secara manual ke pengaturan Vercel; variabel ini disuntikkan secara otomatis dan dirotasi oleh platform Vercel saat Anda menautkan Blob Store:*
- `VERCEL_OIDC_TOKEN` (Otomatis)
- `BLOB_STORE_ID` (Otomatis)

*Fallback Opsional (Hanya untuk pengujian offline/lokal jika OIDC tidak tersedia):*
- `BLOB_READ_WRITE_TOKEN`: Opsional untuk pengembangan lokal.

---

## 3. Prosedur Penerapan dan Migrasi Kanonikal (9 Langkah)

Ikuti urutan langkah produksi berikut secara disiplin:

```text
1. Repositori GitHub sudah terhubung (https://github.com/IAmYoursRey/Talentra.git)
2. Buat / Impor Proyek ke Vercel (Framework: Next.js)
3. Buat Proyek Database Neon PostgreSQL Gratis (Ambil Pooled URL)
4. Buat dan Hubungkan PRIVATE Vercel Blob Store
5. Konfigurasikan seluruh App Secrets dan App Config di Vercel
6. Jalankan Migrasi Alembic (`alembic upgrade head`) ke Neon DB
7. Terapkan ke Vercel Preview Deployment
8. Lakukan Smoke Test pada Preview Deployment
9. Promosikan / Terapkan ke Production Deployment
```

### Langkah 1: Repositori GitHub
Repositori TALENTRA.ID telah tersedia di branch `main` pada `https://github.com/IAmYoursRey/Talentra.git`.

### Langkah 2: Impor Proyek ke Vercel
1. Masuk ke [vercel.com](https://vercel.com).
2. Klik **Add New... > Project** dan pilih repositori `Talentra`.
3. Vercel akan otomatis mengenali framework **Next.js**.
4. Biarkan konfigurasi Build & Output default.
5. Vercel secara native akan mengeksekusi `api/index.py` untuk seluruh request `/api/*`.

### Langkah 3: Buat Database Neon PostgreSQL Gratis (Pooled)
1. Buka [neon.tech](https://neon.tech) dan masuk dengan akun GitHub Anda.
2. Buat proyek baru (misal: `talentra-db`).
3. Salin string koneksi **Pooled Connection** (yang memiliki subdomain `-pooler`).
4. Ganti awalan skema URL dari `postgres://` atau `postgresql://` menjadi `postgresql+asyncpg://`.

### Langkah 4: Buat dan Hubungkan Private Vercel Blob Store
1. Di Dashboard Vercel proyek Anda, buka tab **Storage**.
2. Klik **Create Database > Blob**.
3. Beri nama store (misal: `talentra-evidence`).
4. **Wajib**: Pastikan pengaturan akses bersifat privat (`access: private`).
5. Vercel secara otomatis menyuntikkan autentikasi OIDC ke serverless functions proyek Anda.

### Langkah 5: Konfigurasi Variabel Lingkungan di Vercel
Tambahkan seluruh variabel lingkungan dari tabel Bagian 2 (App Secrets & App Config) di menu **Project Settings > Environment Variables**.

### Langkah 6: Jalankan Migrasi Alembic Secara Eksplisit
Jangan pernah mengeksekusi mutasi skema secara otomatis saat cold start fungsi serverless. Jalankan migrasi satu kali dari terminal sebelum menerima traffic:
```bash
# Dari root proyek:
cd backend
python -m pip install -r requirements.txt

# Jalankan migrasi ke Neon DB:
DATABASE_URL="postgresql+asyncpg://neondb_owner:<password>@ep-cool-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require" alembic upgrade head
```

### Langkah 7: Terapkan ke Vercel Preview Deployment
Buat Pull Request atau push ke branch non-main untuk memicu Preview Deployment terisolasi.

### Langkah 8: Uji Asap (Smoke Test) pada Preview
Verifikasi URL preview (`https://<preview-domain>`):
1. Probe kesehatan:
   - `https://<preview-domain>/api/v1/health/live` -> `{"status": "live", ...}`.
   - `https://<preview-domain>/api/v1/health/ready` -> `{"status": "ready", ...}`.
2. Probe verifikasi publik:
   - `https://<preview-domain>/api/v1/public/verify/invalid-token` -> 404 tanpa kebocoran data.
3. Halaman login: `/login`.

### Langkah 9: Promosikan ke Production
Setelah pengujian preview berhasil, merge ke `main` untuk merilis ke domain produksi utama (`https://<project>.vercel.app`).

---

## 4. Manifest Dependensi Python (Python Dependency Manifests)

TALENTRA.ID memisahkan manifest dependensi Python secara terstruktur:

1. **`requirements.txt` (Root Repositori)**:
   - **Otoritatif untuk Runtime Vercel**.
   - Vercel Serverless Function runtime secara otomatis mendeteksi file dependensi di root repositori untuk memaketkan fungsi Python (`api/index.py`).
   - Berisi hanya paket produksi esensial: `fastapi`, `pydantic`, `argon2-cffi`, `pyjwt[crypto]`, `sqlalchemy`, `greenlet`, `asyncpg`, `alembic`, `reportlab`, `qrcode`, `pillow`, `httpx`.
2. **`backend/requirements.txt` (Subdirektori Backend)**:
   - **Otoritatif untuk Pengembangan Lokal & Test Suite Lengkap**.
   - Menyertakan perkakas pengembangan dan pengujian lokal: `uvicorn`, `aiosqlite`, `pytest`, `pytest-asyncio`.

---

## 5. Pengembangan Lokal (Local Development)

Pengembangan lokal tetap cepat dan mandiri tanpa membutuhkan koneksi internet atau cloud:

```bash
# Terminal 1: Frontend Next.js
npm run dev

# Terminal 2: Backend FastAPI (menggunakan SQLite bawaan)
python -m uvicorn app.main:app --reload --port 8000 --app-dir backend
```

Opsi sinkronisasi variabel Vercel ke komputer lokal:
```bash
vercel link
vercel env pull .env.local
```

---

## 5. Batasan & Realitas Free-Tier

Penerapan gratis ini dirancang untuk:
- Pilot demonstrasi sekolah.
- Portofolio pameran kompetisi.
- Penggunaan internal skala kecil hingga menengah.

Kapasitas gratis Neon dan Vercel Blob memiliki kuota kuantitatif:
1. **Neon Free Tier**: ~0.5 GB data relational.
2. **Vercel Blob Free Tier**: ~1 GB penyimpanan dan batas bandwidth transfer bulanan.
3. Fitur `FREE_TIER_MODE=true` melindungi sistem agar menolak unggahan baru dengan kode `STORAGE_QUOTA_REACHED` ketika soft-limit tercapai tanpa merusak karya portofolio yang sudah tersimpan.
4. Jika sekolah membutuhkan skala ribuan siswa aktif dengan berkas video besar, institusi dapat meningkatkan ke paket kuota berbayar tanpa mengubah kode aplikasi.
