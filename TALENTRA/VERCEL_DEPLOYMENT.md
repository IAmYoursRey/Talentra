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

## 2. Tabel Variabel Lingkungan Vercel

Konfigurasikan variabel berikut pada menu **Project Settings > Environment Variables** di Dashboard Vercel:

| Variabel | Tipe | Lingkungan | Tujuan / Keterangan |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | Non-Secret | Production, Preview | `production` |
| `DATABASE_URL` | **Secret** | Production, Preview | Neon Pooled connection string (`postgresql+asyncpg://...pooler...`) |
| `DB_POOL_CLASS` | Non-Secret | Production, Preview | `queue` (default: pool_size=2) atau `nullpool` (serverless on-demand) |
| `REPOSITORY_BACKEND` | Non-Secret | Production, Preview | `postgres` |
| `JWT_SECRET_KEY` | **Secret** | Production, Preview | Kunci rahasia minimal 32 karakter untuk enkripsi token sesi |
| `IDENTIFIER_LOOKUP_PEPPER` | **Secret** | Production, Preview | Pepper HMAC untuk anonimisasi NISN / NIP di database |
| `CV_VERIFICATION_TOKEN_PEPPER` | **Secret** | Production, Preview | Pepper rahasia untuk hash token verifikasi publik QR |
| `COOKIE_SECURE` | Non-Secret | Production, Preview | `true` (enforce HTTPS cookie) |
| `ENABLE_DEMO_AUTH` | Non-Secret | Production, Preview | `false` (wajib nonaktif di produksi) |
| `PUBLIC_APP_URL` | Non-Secret | Production | URL domain Vercel Anda, misal `https://talentra.vercel.app` |
| `OBJECT_STORAGE_PROVIDER` | Non-Secret | Production, Preview | `vercel_blob` |
| `BLOB_READ_WRITE_TOKEN` | Optional Secret | Local / Manual | Opsional fallback jika OIDC tidak aktif. Di Vercel, OIDC digunakan otomatis |
| `FREE_TIER_MODE` | Non-Secret | Production, Preview | `true` (mengaktifkan kuota proteksi kapasitas gratis) |
| `STORAGE_SOFT_LIMIT_BYTES` | Non-Secret | Production, Preview | Batas lunak kuota penyimpanan (default: `209715200` = 200MB) |

---

## 3. Prosedur Migrasi dan Penerapan Produksi Kanonikal

Ikuti urutan langkah produksi berikut secara disiplin:

```text
1. Buat / Hubungkan Database Neon (Pooled endpoint)
2. Konfigurasi DATABASE_URL di Environment Variables
3. Jalankan `alembic upgrade head` secara eksplisit dari terminal/CI
4. Buat / Hubungkan Vercel Blob Store (Private access)
5. Konfigurasi seluruh production secrets di Vercel
6. Terapkan ke Vercel Preview Deployment
7. Lakukan Smoke Test pada Preview
8. Promosikan / Terapkan ke Production Deployment
```

### Langkah 1: Buat Database Neon PostgreSQL (Pooled)
1. Buka [neon.tech](https://neon.tech) dan masuk dengan akun GitHub Anda.
2. Buat proyek baru (misal: `talentra-db`).
3. Pilih region terdekat (misal: `ap-southeast-1` Singapura).
4. Salin string koneksi **Pooled Connection** (yang memiliki subdomain `-pooler`).
5. Ganti awalan skema URL dari `postgres://` atau `postgresql://` menjadi `postgresql+asyncpg://` untuk driver asinkron Python.

### Langkah 2: Konfigurasi DATABASE_URL
Tetapkan `DATABASE_URL` pada Dashboard Vercel dan di lingkungan eksekusi migrasi lokal.

### Langkah 3: Jalankan Migrasi Alembic Secara Eksplisit
Jangan pernah mengeksekusi mutasi skema secara otomatis saat cold start fungsi serverless. Jalankan migrasi satu kali sebelum menerima traffic:
```bash
# Dari root proyek:
cd backend
python -m pip install -r requirements.txt

# Jalankan upgrade ke head:
DATABASE_URL="postgresql+asyncpg://neondb_owner:<password>@ep-cool-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require" alembic upgrade head
```

### Langkah 4: Buat dan Hubungkan Vercel Blob (Private Storage)
1. Di Dashboard Vercel proyek Anda, buka tab **Storage**.
2. Klik **Create Database > Blob**.
3. Beri nama store (misal: `talentra-evidence`).
4. **Penting**: Pastikan pengaturan akses bersifat privat (`access: private`).
5. Vercel secara otomatis mengaktifkan autentikasi OIDC short-lived (`VERCEL_OIDC_TOKEN`) untuk fungsi yang berjalan di Vercel.

### Langkah 5: Konfigurasi Seluruh Production Secrets di Vercel
Lengkapi seluruh variabel lingkungan dari tabel Bagian 2 di menu **Project Settings > Environment Variables**.

### Langkah 6: Terapkan ke Vercel Preview Deployment
Hubungkan repositori GitHub Anda dan lakukan git push ke branch preview (atau buat Pull Request). Vercel akan membuat Preview Deployment terisolasi.

### Langkah 7: Uji Asap (Smoke Test) pada Preview
Verifikasi URL preview:
1. Akses probe kesehatan:
   - `https://<preview-domain>/api/v1/health/live` -> harus menghasilkan `{"status": "live", ...}`.
   - `https://<preview-domain>/api/v1/health/ready` -> harus menghasilkan `{"status": "ready", "dependencies": {"database": "ok", "storage": "ok"}}`.
2. Uji verifikasi publik dengan token acak:
   - `https://<preview-domain>/api/v1/public/verify/invalid-token` -> harus mengembalikan 404 tanpa kebocoran data.
3. Buka halaman `/login` dan uji tampilan antarmuka.

### Langkah 8: Promosikan / Terapkan ke Production
Setelah verifikasi preview sukses, gabungkan (merge) ke branch `main` untuk merilis ke domain produksi utama.

---

## 4. Pengembangan Lokal (Local Development)

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
