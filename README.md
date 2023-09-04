# Chairiot 🪑

<p align="center">
  <img src='./img/chairiotLogo.png'width=300>
</p>

## 📖 Overview

- **Chairiot** adalah kursi pintar yang dikembangkan oleh tim 24 Hyperion dalam bootcamp SIC Batch 4 yang diadakan oleh samsung dan skilvul. **Chairiot** dapat memonitor kebiasaan duduk pengguna, memberikan peringatan, dan Weekly report.
- **Chairiot** dibuat dengan tujuan untuk mengurangi masalah yang disebabkan oleh kesalahan dalam posisi duduk.

## ❓ What Can Chairiot Do?

- Mendeteksi kesalahan duduk pengguna dan memberikan peringatan dari buzzer.
- Memberi reminder ketika pengguna terlalu lama duduk.
- Weekly report berupa laporan seberapa lama pengguna duduk, ringkasan kebiasaan duduk selama seminggu terakhir dan perkembangan kebiasaan duduk dari minggu yang lalu yang dikirim melalui telegram.
- Memiliki 3 Mode yaitu Peaceful, Normal, dan Agressive.
- Dashboard Ubidots untuk menambahkan bot Chairiot dan ID telegram dan monitor posisi duduk.

## ⚡️ Wiring & Components

Chairiot menggunakan komponen sebagai berikut:
1. 1x Raspberry PI 4B
2. 6x Resistor 220Ω
3. 2x Resistor 1kΩ
4. 1x Buzzer
5. 2x LED(merah & hijau)
6. 1x PCB lubang
7. 11x female/female jumper cable
8. 4x male/female jumper cable
9. 1x Fan 5v

<p align="center">
  <img src='./img/chairiot_bb.png'width=400>
</p>
<p align="center">
  <img src='./img/pcbAtas.jpeg'width=400>
</p>
<p align="center">
  <img src='./img/pcbBawah.jpeg'width=400>
</p>

## 🔧 Perakitan

## 📚 Software & Library

- Ubidots
- SQLite
- gpiozero
- requests
- schedule
- python 3
