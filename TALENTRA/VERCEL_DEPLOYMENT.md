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
| `DATABASE_URL` | **Secret** | Production, Preview | Neon Pooled connection string (`postgresql+asyncpg://...`) |
| `REPOSITORY_BACKEND` | Non-Secret | Production, Preview | `postgres` |
| `JWT_SECRET_KEY` | **Secret** | Production, Preview | Kunci rahasia minimal 32 karakter untuk enkripsi token sesi |
| `IDENTIFIER_LOOKUP_PEPPER` | **Secret** | Production, Preview | Pepper HMAC untuk anonimisasi NISN / NIP di database |
| `CV_VERIFICATION_TOKEN_PEPPER` | **Secret** | Production, Preview | Pepper rahasia untuk hash token verifikasi publik QR |
| `COOKIE_SECURE` | Non-Secret | Production, Preview | `true` (enforce HTTPS cookie) |
| `ENABLE_DEMO_AUTH` | Non-Secret | Production, Preview | `false` (wajib nonaktif di produksi) |
| `PUBLIC_APP_URL` | Non-Secret | Production | URL domain Vercel Anda, misal `https://talentra.vercel.app` |
| `OBJECT_STORAGE_PROVIDER` | Non-Secret | Production, Preview | `vercel_blob` |
| `BLOB_READ_WRITE_TOKEN` | **Secret** | Production, Preview | Dibuat otomatis saat menautkan Vercel Blob Store |
| `FREE_TIER_MODE` | Non-Secret | Production, Preview | `true` (mengaktifkan kuota proteksi kapasitas gratis) |
| `STORAGE_SOFT_LIMIT_BYTES` | Non-Secret | Production, Preview | Batas lunak kuota penyimpanan (default: `209715200` = 200MB) |

---

## 3. Langkah Demi Langkah Penerapan (Step-by-Step)

### Langkah 1: Push Repositori ke GitHub
Inisialisasi atau hubungkan git remote ke akun GitHub Anda:
```bash
git remote add origin https://github.com/<username-anda>/talentra-id.git
git branch -M main
git push -u origin main
```

### Langkah 2: Buat Database Neon PostgreSQL Gratis
1. Buka [neon.tech](https://neon.tech) dan masuk dengan akun GitHub Anda.
2. Buat proyek baru (misal: `talentra-db`).
3. Pilih region terdekat (misal: `ap-southeast-1` Singapura).
4. Salin string koneksi **Pooled Connection** (contoh: `postgres://...pooler...`).
5. Ganti awalan skema URL dari `postgres://` atau `postgresql://` menjadi `postgresql+asyncpg://` untuk driver asinkron Python.

### Langkah 3: Jalankan Migrasi Database ke Neon
Sebelum aplikasi pertama kali menerima lalu lintas pengguna, terapkan skema tabel menggunakan Alembic secara langsung dari terminal lokal Anda ke database Neon:
```bash
# Di terminal komputer Anda:
cd backend
python -m pip install -r requirements.txt

# Jalankan migrasi ke Neon DB:
DATABASE_URL="postgresql+asyncpg://neondb_owner:<password>@ep-cool-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require" alembic upgrade head
```
*Tidak perlu menginstal PostgreSQL daemon di komputer lokal; Alembic akan bermigrasi melalui koneksi cloud.*

### Langkah 4: Impor Proyek ke Vercel
1. Masuk ke [vercel.com](https://vercel.com) menggunakan akun GitHub.
2. Klik **Add New... > Project**.
3. Pilih repositori GitHub `talentra-id`.
4. Vercel akan otomatis mengenali framework **Next.js**.
5. Jangan ubah Build Settings (Next.js default).
6. Buka bagian **Environment Variables** dan tambahkan variabel sesuai tabel pada Bagian 2 di atas.
7. Klik **Deploy**.

### Langkah 5: Buat dan Hubungkan Vercel Blob (Private Storage)
1. Di Dashboard Vercel proyek Anda, buka tab **Storage**.
2. Klik **Create Database > Blob**.
3. Beri nama store (misal: `talentra-evidence`).
4. **Penting**: Pastikan pengaturan akses bersifat privat (`access: private`).
5. Vercel secara otomatis menyuntikkan variabel `BLOB_READ_WRITE_TOKEN` ke dalam Environment Variables proyek Anda.

### Langkah 6: Verifikasi & Uji Asap (Smoke Test)
Setelah deployment selesai:
1. Buka URL produksi Vercel Anda: `https://<nama-proyek>.vercel.app`.
2. Akses probe kesehatan:
   - `https://<nama-proyek>.vercel.app/api/v1/health/live` -> harus menghasilkan `{"status": "live", ...}`.
   - `https://<nama-proyek>.vercel.app/api/v1/health/ready` -> harus menghasilkan `{"status": "ready", "dependencies": {"database": "ok", "storage": "ok"}}`.
3. Buka halaman `/login` dan uji alur otentikasi.

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
