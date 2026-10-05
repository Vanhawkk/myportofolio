# Personal Portfolio

Website portofolio pribadi berbasis Django yang menampilkan profil, pendidikan, pengalaman, dan proyek. Project ini dikembangkan secara bertahap untuk tugas individu mata kuliah Pemrograman Berbasis Platform.

- Nama: Muhammad Eshan Bobby Bhaskara
- NPM: 2506546333
- Kelas: PBP C

## Fitur

- Halaman Profile, Education, Experience, dan Projects yang dapat dibaca publik.
- CRUD Experience dan Project dengan pembatasan hak akses di sisi server.
- Registrasi, login, logout, session, dan cookie `last_login`.
- Role Editor melalui Django Group dan permission bawaan Django.
- Fitur star/unstar Project dan Experience untuk pengguna yang sudah login.
- Halaman Project dan Experience menggunakan AJAX untuk menampilkan data, mencari tanpa memuat ulang halaman, dan menambahkan data melalui modal.
- Endpoint JSON publik dengan allowlist field untuk mencegah kebocoran data user.
- Test otomatis untuk model, autentikasi, CRUD, JSON, dan matriks authorization.

## Setup Lokal

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Website dapat dibuka melalui `http://127.0.0.1:8000/`. Django Admin tersedia di `http://127.0.0.1:8000/admin/`.

Untuk menjalankan pemeriksaan dan seluruh test:

```bash
python manage.py check
python manage.py test
```

## Star Project

Model `Project` memiliki relasi many-to-many `starred_by` dengan model `User`. Toggle star hanya menerima request POST dan form-nya menggunakan CSRF token. Relasi many-to-many memastikan satu user tidak dapat menghasilkan lebih dari satu relasi star untuk Project yang sama.

Guest hanya melihat tautan **Login to star**. User biasa, Editor, dan superuser dapat memberi atau membatalkan star. Halaman Project menampilkan jumlah star dan status `Star` atau `Unstar` untuk user aktif.

## AI Disclosure

Selama mengerjakan project ini saya menggunakan Claude dan Codex. Saya memakai AI untuk berdiskusi, memahami tugas, membantu bagian kode yang berulang, dan mencari penyebab error. Hasil AI tidak langsung dimasukkan seluruhnya; saya membaca diff, menyesuaikan implementasi dengan struktur project, menjalankan test, dan menentukan sendiri hasil akhir yang masuk repository.

Yang saya lakukan sendiri:

- Menentukan isi, deskripsi, dan pengalaman pribadi yang ditampilkan.
- Menentukan susunan halaman Profile, Projects, Experience, dan Education.
- Memilih warna navy, blue, dan white yang dipakai pada website.
- Menentukan bahwa role Editor menggunakan Django Group dengan permission `change_experience` dan `change_project`.
- Membaca perubahan kode, memeriksa matriks hak akses, dan meninjau hasil test sebelum commit.

Yang dibantu AI:

- Claude membantu diskusi awal mengenai pilihan warna dan tampilan website.
- AI membantu struktur awal CSS Grid, timeline, dan efek hover pada card.
- AI membantu membaca spesifikasi Tugas 3 dan Tugas 4, membandingkannya dengan kondisi repository, serta membagi implementasi menjadi langkah kecil.
- AI membantu menyusun helper authorization, view update Project, kondisi permission pada template, dan test matriks role.
- AI membantu menemukan bahwa serializer Project ikut mengirim username dari relasi `starred_by`, lalu membantu menggantinya dengan daftar field publik yang dipilih secara eksplisit.
- AI membantu menjelaskan JSON, CSRF, permission Django, HTTP 403, serta merapikan pesan commit.
- AI digunakan untuk membantu memahami alur implementasi AJAX, pencarian dengan debounce, dan integrasi endpoint JSON pada fitur Experience.
- AI digunakan sebagai bantuan untuk mengecek potensi XSS, terutama saat data dari user dirender kembali menggunakan JavaScript.
- AI membantu memberi masukan terkait validasi form, URL thumbnail, serta penambahan rentang tanggal Experience.
- Seluruh implementasi, pengujian, dan penyesuaian kode tetap ditinjau kembali agar sesuai dengan kebutuhan project.

Strategi prompting yang saya gunakan adalah memberikan dokumen tugas dan source code yang sudah ada, meminta AI menjelaskan gap implementasi, lalu membantu saya mengerjakan step by step tasknya. Setiap langkah dibatasi ke scope tertentu dan diminta menjalankan targeted test serta full test sebelum commit.

Keterbatasan AI yang saya temukan adalah saran awal tetap perlu diperiksa terhadap struktur project dan perilaku Django yang sebenarnya. Contohnya, menyembunyikan tombol saja tidak cukup tanpa server-side check, serializer otomatis dapat ikut mengirim relasi user, dan test endpoint perlu memastikan request yang ditolak benar-benar tidak mengubah database. Karena itu, hasil AI diverifikasi dengan `python manage.py check`, targeted test, full test suite, serta pengujian matriks role melalui Django test client.

## Refleksi

### Tugas 1

1. Penggunaan Elemen Semantik HTML5

Saya pakai `<section>` untuk misahin profile, projects, experience, dan education, masing masing juga punya `id` sendiri agar bisa jadi target anchor link di navbar. Selain itu section juga bikin styling & spacing tiap bagian lebih gampang diatur lewat CSS dibanding kalau semuanya numpuk jadi `<div>` doang.

Untuk project card dan education card saya pakai `<article>`, karena isinya masing-masing bisa berdiri sendiri. Menurut saya ini bikin struktur kode lebih jelas fungsinya, dan browser/screen reader juga lebih ngerti hierarki kontennya.

`<aside>` belum saya pakai karena memang belum ada konten sampingan (sidebar, catatan tambahan, dll) di website ini.

2. Tantangan dalam Menerapkan Responsive Design

Saat mengatur grid projects biar seimbang di berbagai ukuran layar. Awalnya pakai `repeat(auto-fit, minmax(...))`, tapi 3 card-nya jadi nggak ngisi container full, nyisa ruang kosong di kanan. Karena jumlah card di baris pertama sudah pasti 3, saya ganti ke `grid-template-columns: repeat(3, 1fr)` biar rata. Di layar di bawah `600px`, grid-nya jadi 1 kolom aja.

Selain itu ada juga masalah untuk menjaga rasio gambar project tetap 16:9 tanpa gepeng atau distorsi. Solusinya pakai `aspect-ratio: 16 / 9` di container gambar plus `object-fit: cover` di elemen `<img>`-nya.

3. Batasan Static Web dan Rencana Pengembangan Fitur Dinamis

Kontennya sekarang masih full statis, semua data data yang ada ditulis langsung di HTML. Jadi saat ingin nambah project baru, saya harus membuka template, copy struktur card yang ada, terus edit manual satu satu. Card yang coming soon juga masih placeholder, belum kesambung ke data apapun.

Ke depannya saya ingin manfaatin sisi dinamis Django biar kontennya bisa diedit langsung dari browser tanpa buka kode. Selain itu pengen nambahin form kontak dan status project otomatis, jadi placeholder coming soon di project bisa berubah sendiri begitu ada project baru yang dipublish.

### Tugas 2

1. Alur projek dan peran urls.py proyek, urls.py aplikasi, view, model, dan template.

Jadi di browser membuka proyek lalu di balik layar browser akan request URL projects dan akan diterima urls.py proyek. Kemudian dari situ urls.py aplikasi akan memilih view dari request URL tersebut, dalam hal ini adalah "show_projects". Kemudian view akan mengambil data dari model yang terhubung langsung dengan database. Lalu view akan mengirim data melalui context, dan data data tersebut akan diloop oleh template. Setelah itu html akan dikirimkan langsung ke browser untuk ditampilkan ke user.

2. Karena jika suatu waktu bagian tersebut ingin dihapus, diubah, diupdate, atau ditambah, akan sangat sulit untuk men-trace kembali satu persatu baris kodenya apalagi jika project sudah terlalu banyak. Maka dari itu, diperlukan sebuah sistem baru yang tidak perlu hard-coded untuk menambahkan/mengedit section di dalamnya. Dengan sistem ini juga tampilan semua kartu akan tetap konsisten karena sudah diloop. Data data dari section tersebut juga bisa dikelola melalui django admin sehingga akan lebih mudah.

3. Makemigrations dijalankan ketika ada perubahan pada struktur data atau model. Ini dilakukan untuk memberikan instruksi perubahan database kepada django sehingga data akan sinkron dengan tampilan. Migrate berfungsi untuk menerapkan hasil instruksi yang dihasilkan makemigration ke dalam database agar database tersebut aktif dan bisa secara real-time update. Contoh: Ketika menambahkan model Project, makemigrations menghasilkan 0002_project.py. Setelah itu, migrate membuat tabel Project di database.

### Tugas 3

1. Saya menggunakan `ModelForm` karena formnya bisa langsung mengikuti field yang ada di model. Contohnya, `ExperienceForm` mengambil field `title`, `description`, `category`, dan `thumbnail` dari model `Experience`. Saya jadi tidak perlu menulis input dan aturan pengecekannya satu per satu secara manual. Django juga bisa langsung mengecek isi form dengan `form.is_valid()` dan menyimpan datanya dengan `form.save()`. Kalau membuat form HTML biasa, saya harus mengambil setiap input sendiri, mengecek datanya sendiri, lalu menyimpannya ke model secara manual.

`{% csrf_token %}` digunakan untuk memastikan bahwa request POST berasal dari form website kita. Django akan memberikan token pada form dan mengeceknya kembali saat form dikirim. Jika tokennya tidak ada atau tidak sesuai, request akan ditolak. Hal ini mencegah website lain mengirim request tambah, ubah, atau hapus data tanpa izin melalui browser pengguna. Namun, CSRF bukan login, jadi orang lain masih bisa membuka form saya selama belum ada fitur autentikasi.

2. JSON lebih sering digunakan pada website modern karena penulisannya lebih singkat dan lebih mudah dibaca dibandingkan XML. JSON juga mudah dipakai oleh JavaScript karena bentuknya mirip dengan object dan array. Sementara itu, XML memakai tag pembuka dan penutup sehingga isinya menjadi lebih panjang. Karena itu JSON lebih praktis untuk mengirim data dari backend ke frontend. XML masih bisa digunakan, tetapi biasanya ditemukan pada sistem lama atau sistem yang memang membutuhkan format XML.

3. Saat `/api/experiences/` dibuka, URL tersebut akan menjalankan fungsi `get_experiences_json`. Fungsi ini akan mengambil data Experience dari database menggunakan `Experience.objects.order_by(...)`. Hasilnya masih berbentuk QuerySet dan berisi object model Django. Setelah itu `serializers.serialize("json", experiences)` mengubah data tersebut menjadi teks JSON. Teks JSON kemudian dikirim sebagai response menggunakan `HttpResponse` dengan tipe `application/json`.

Proses serialization diperlukan karena object model Django tidak bisa langsung dikirim melalui HTTP dan dibaca oleh browser sebagai JSON. Object tersebut harus diubah dulu menjadi format teks yang berisi model, id, dan fields. Pada halaman Experience, JSON itu diubah kembali menggunakan `serializers.deserialize`, lalu object hasilnya dikirim ke template melalui context. Pada tugas ini proses tersebut memang terasa berulang, tetapi tujuannya untuk memahami proses pengiriman data antara server dan client.

### Tugas 5

1. Debouncing adalah teknik untuk menunda eksekusi fungsi sampai user berhenti melakukan input dalam waktu tertentu. Pada pencarian AJAX, debouncing penting agar aplikasi tidak mengirim request ke server pada setiap huruf yang diketik. Di project ini, pencarian Experience baru dijalankan setelah user berhenti mengetik selama 300 ms, sehingga request lebih hemat dan hasil pencarian lebih stabil.

2. `await` digunakan untuk menunggu Promise dari `fetch()` selesai sebelum kode melanjutkan ke proses berikutnya. Contohnya, `await fetch()` memastikan response dari server sudah diterima, lalu `await response.json()` memastikan data JSON sudah selesai dibaca. Jika `await` tidak digunakan, variabel tersebut masih berupa Promise sehingga data belum bisa dipakai secara langsung dan dapat menyebabkan error atau urutan proses yang tidak sesuai.

3. XSS (Cross-Site Scripting) adalah celah keamanan ketika input user berisi kode HTML atau JavaScript berbahaya yang kemudian dirender oleh website. Risiko ini lebih besar pada AJAX/JavaScript karena data sering dimasukkan ke halaman menggunakan `innerHTML`, yang dapat menganggap input tersebut sebagai HTML aktif. Sementara itu, Django template secara default melakukan escaping terhadap karakter berbahaya. Untuk mengurangi risiko XSS, input Experience dibersihkan di server menggunakan `strip_tags`, URL thumbnail divalidasi, dan teks yang dirender melalui JavaScript di-escape terlebih dahulu.