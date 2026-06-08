-- 1. Membuat Tabel Dimensi Sungai
CREATE TABLE Dim_Sungai (
    id_sungai SERIAL PRIMARY KEY,
    nama_sungai VARCHAR(100) NOT NULL,
    id_titik_sampel VARCHAR(20) NOT NULL,
    nama_titik_sampel VARCHAR(150),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    wilayah_admin VARCHAR(50)
);

-- 2. Membuat Tabel Dimensi Parameter
CREATE TABLE Dim_Parameter (
    id_parameter SERIAL PRIMARY KEY,
    nama_parameter VARCHAR(100) NOT NULL,
    jenis_parameter VARCHAR(20),
    satuan VARCHAR(30),
    baku_mutu_min NUMERIC(12,4),
    baku_mutu_max NUMERIC(12,4),
    keterangan TEXT
);

-- 3. Membuat Tabel Dimensi Waktu
CREATE TABLE Dim_Waktu (
    id_waktu SERIAL PRIMARY KEY,
    periode_pemantauan VARCHAR(20) NOT NULL,
    tahun_data INTEGER NOT NULL,
    urutan_periode INTEGER,
    label_periode VARCHAR(50)
);

-- 4. Membuat Tabel Dimensi Status
CREATE TABLE Dim_Status (
    id_status SERIAL PRIMARY KEY,
    kode_status VARCHAR(20) NOT NULL,
    label_status VARCHAR(50),
    warna_indikator VARCHAR(10),
    deskripsi TEXT
);

-- 5. Membuat Tabel Fakta Pengukuran (Bergantung pada semua dimensi)
CREATE TABLE Fact_Pengukuran (
    id_pengukuran SERIAL PRIMARY KEY,
    id_sungai INTEGER REFERENCES Dim_Sungai(id_sungai),
    id_parameter INTEGER REFERENCES Dim_Parameter(id_parameter),
    id_waktu INTEGER REFERENCES Dim_Waktu(id_waktu),
    id_status INTEGER REFERENCES Dim_Status(id_status),
    hasil_pengukuran NUMERIC(12,4),
    status_exceed BOOLEAN,
    rasio_terhadap_bm NUMERIC(10,4),
    is_valid BOOLEAN DEFAULT TRUE
);