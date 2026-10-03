# LinkedIn Caption (Casual & Storytelling Edition)
## Proyek Portofolio: Household Intelligence — Jabodetabek Rental Engine

---

Halo teman-teman di LinkedIn! 👋

Beberapa bulan terakhir ini saya memutuskan buat nyemplung dan belajar lebih dalam tentang dunia data analytics. 

Jujur, dorongan awalnya sederhana banget: berangkat dari keseharian saya sendiri sebagai seorang **Quality Control (QC)** di industri manufaktur. Tiap hari kerjaan saya nggak jauh-jauh dari ngeliatin angka, ngitung persentase reject barang masuk dan keluar, sampai mantau stabilitas proses produksi. 

Nah, dari pengalaman di lapangan plus ilmu baru yang saya dapet pas ikut bootcamp data analytics kemarin, ada satu hal yang makin saya sadari: di era yang serba digital dan serba AI kayak sekarang, melek data itu bukan lagi sekadar skill tambahan, tapi udah jadi **skillset mandatory** banget. 

Supaya ilmu yang dipelajari gak cuma ngendap di kepala atau mentok di dataset latihan yang serba rapi, saya memberanikan diri bikin proyek kecil-kecilan: **menganalisa sebaran harga sewa apartemen di Jabodetabek**. 

Untuk ngumpulin datanya, saya coba scraping listing yang bertebaran di website properti publik (tentunya dengan bantuan tools dan sedikit sentuhan AI biar prosesnya lebih efisien).

Dari data mentah itu, muncul rasa penasaran:
> *"Bisa gak sih kita menerjemahkan harga sewa yang beda-beda tipis tapi lokasinya mencar ke mana-mana ini jadi satu formula objektif penentuan harga wajar sebuah properti?"*

Ternyata pas saya ulik dan riset literatur, jawabannya ada! Namanya **Hedonic Pricing Model**. Intinya model ini memecah harga properti jadi gabungan nilai dari berbagai atribut: mulai dari luas ruangan, jarak ke pusat kota (CBD), jarak ke stasiun MRT/KRL, sampai kelengkapan fasilitas dan perabot (*furnishing*).

Dari formula itu, akhirnya saya coba rancang pipeline data lengkapnya:
1. **Cleaning data mentah:** nyaring iklan jual yang nyasar ke sewa, normalisasi harga, dan ekstrak fasilitas pakai NLP sederhana.
2. **Database rapi:** bikin struktur Star Schema (SQL) biar gampang ditarik ke dashboard analitik.
3. **Machine Learning & Deal Radar:** ngitung estimasi harga wajar pasaran dan ngedeteksi unit yang "salah harga" alias jauh lebih murah dari pasarannya (bargain deals).
4. **Bikin web app mandiri:** saya kemas jadi web interaktif yang saya beri nama **Household Intelligence** (menggunakan FastAPI di backend dan tampilan modern Linear theme).

---

### 🙏 Butuh Banget Feedback & Masukan Teman-Teman!

Namanya juga proyek belajar dan bikinan pemula, saya sadar banget proyek kecil-kecilan ini **masih banyak banget kekurangan, kesalahan, dan butuh banyak perbaikan**. Misalnya dari penamaan wilayah yang masih sering rancu dari pihak broker, ataupun variabel penentu harga yang masih bisa diperdalam lagi.

Makanya, saya sangat mengharapkan masukan, kritik santai, maupun saran dari teman-teman, para senior, dan rekan-rekan praktisi data:
* Menurut teman-teman, apa aja variabel penting lain yang harusnya dimasukin buat nentuin harga sewa apartemen di Jabodetabek?
* Kira-kira dari sisi pipeline data atau analisa machine learning-nya, bagian mana yang paling perlu saya poles lagi?

Bagi teman-teman yang mau intip kode, struktur database SQL, atau sekadar coba jalanin aplikasinya secara lokal, semuanya sudah saya taruh rapi dan transparan di GitHub:
🔗 **Link GitHub:** https://github.com/Lottoenergon/Household-Intelligence

Setiap feedback dari kalian bakal berharga banget buat proses belajar saya ke depan. Terima kasih banyak ya! Yuk ngobrol santai di kolom komentar. 🙏🚀

---
#DataAnalytics #BelajarData #QualityControl #CareerTransition #PropTech #Python #MachineLearning #SQL #FastAPI #LearningInPublic #OpenToFeedback