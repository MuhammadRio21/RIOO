import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

# --- KONFIGURASI LOGGER ---
# Mengatur format agar menampilkan Waktu, Level, dan Pesan
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
# Membuat objek logger global
logger = logging.getLogger("SistemRegistrasi")

# --- DATA MODEL ---
@dataclass
class Mahasiswa:

    nama: str
    sks_diambil: int
    mata_kuliah_lulus: list[str]
    status_bayar: str = "belum_lunas"

# --- 1. ABSTRAKSI (Solusi DIP & OCP) ---
class IValidator(ABC):
    """
    Interface (Kontrak) dasar untuk semua jenis validator.
    Menerapkan prinsip Open-Closed Principle (OCP) dan Dependency Inversion (DIP).
    """
    
    @abstractmethod
    def validate(self, mhs: Mahasiswa, requirement: any) -> bool:
        """
        Melakukan validasi terhadap data mahasiswa.

        Args:
            mhs (Mahasiswa): Objek data mahasiswa yang akan divalidasi.
            requirement (any): Syarat yang harus dipenuhi (bisa int, str, dll).

        Returns:
            bool: True jika validasi sukses, False jika gagal.
        """
        pass

# --- 2. IMPLEMENTASI LOGIC (Solusi OCP) ---
class SksValidator(IValidator):
    """Validator khusus untuk mengecek batas SKS.
    
    Args:
        mhs (Mahasiswa): Objek data mahasiswa.
        max_sks (int): Batas maksimal SKS yang boleh diambil.
    
    Returns:
        bool: True jika validasi sukses, False jika gagal.
    """
    
    def validate(self, mhs: Mahasiswa, max_sks: int) -> bool:
        if mhs.sks_diambil > max_sks:
            # Gunakan warning untuk validasi yang gagal (bukan error sistem)
            logger.warning(f"VALIDASI SKS: Gagal. SKS ({mhs.sks_diambil}) melebihi batas {max_sks}.")
            return False
        logger.info("VALIDASI SKS: Aman.")
        return True

class PrerequisiteValidator(IValidator):
    """Validator khusus untuk mengecek prasyarat mata kuliah."""
    
    def validate(self, mhs: Mahasiswa, matkul_syarat: str) -> bool:
        if matkul_syarat not in mhs.mata_kuliah_lulus:
            logger.warning(f"VALIDASI PRASYARAT: Gagal. Belum lulus {matkul_syarat}.")
            return False
        logger.info(f"VALIDASI PRASYARAT: Mata kuliah {matkul_syarat} terpenuhi.")
        return True

# --- 3. PEMISAHAN LOGGING (Solusi SRP) ---
class ValidationLogger:
    """
    Class wrapper untuk logging. 
    Menerapkan Single Responsibility Principle (SRP) dengan memisahkan 
    logika pencatatan dari logika bisnis.
    """
    
    def log_success(self, mhs_name: str, val_type: str):
        """Mencatat log kesuksesan proses validasi."""
        logger.info(f"[HASIL AKHIR]: Validasi '{val_type}' BERHASIL untuk {mhs_name}.")
    
    def log_failure(self, mhs_name: str, val_type: str):
        """Mencatat log kegagalan proses validasi."""
        logger.error(f"[HASIL AKHIR]: Validasi '{val_type}' GAGAL untuk {mhs_name}.")

# --- 4. MANAGER / SERVICE (Penerapan DIP) ---
class RegistrationService:
    """
    Service utama yang mengkoordinasikan proses registrasi.
    Bergantung pada abstraksi IValidator, bukan implementasi konkret.
    """

    def __init__(self, validator: IValidator, logger_service: ValidationLogger):
        """
        Inisialisasi service dengan Dependency Injection.

        Args:
            validator (IValidator): Objek validator (bisa SKS, Prasyarat, dll).
            logger_service (ValidationLogger): Service untuk pencatatan log.
        """
        self.validator = validator
        self.logger_service = logger_service

    def process_validation(self, mhs: Mahasiswa, requirement: any):
        """
        Menjalankan proses validasi dan mencatat hasilnya.
        
        Args:
            mhs (Mahasiswa): Data mahasiswa.
            requirement (any): Syarat validasi.
        """
        print("-" * 50) # Pemisah visual di console
        logger.info(f"Memulai proses validasi untuk {mhs.nama}...")
        
        is_valid = self.validator.validate(mhs, requirement)
        
        # Delegasi ke Logger (SRP)
        validator_name = self.validator.__class__.__name__
        if is_valid:
            self.logger_service.log_success(mhs.nama, validator_name)
        else:
            self.logger_service.log_failure(mhs.nama, validator_name)

#Program utama file

# Setup Data Dummy
mhs_andi = Mahasiswa("Andi", 24, ["Algoritma"], "lunas") # Kasus: SKS berlebih
mhs_budi = Mahasiswa("Budi", 20, ["Algoritma"], "belum_lunas") 
val_logger = ValidationLogger()

print("\n=== SKENARIO 1: Validasi SKS & Prasyarat (Fitur Dasar) ===")

# 1. Cek SKS Andi (Batas 22)
sks_validator = SksValidator()
service_sks = RegistrationService(sks_validator, val_logger)
service_sks.process_validation(mhs_andi, 22)

# 2. Cek Prasyarat Budi (Harus lulus Algoritma)
prereq_validator = PrerequisiteValidator()
service_prereq = RegistrationService(prereq_validator, val_logger)
service_prereq.process_validation(mhs_budi, "Algoritma")


print("\n=== SKENARIO 2: Challenge Pembuktian OCP (Fitur Baru) ===")
# Soal: Tambahkan validasi Pembayaran TANPA mengedit class RegistrationService!

class PaymentValidator(IValidator):
    """Validator khusus untuk mengecek status pembayaran."""
    def validate(self, mhs: Mahasiswa, required_status: str) -> bool:
        if mhs.status_bayar != required_status:
            logger.warning(f"VALIDASI PEMBAYARAN: Gagal. Status '{mhs.status_bayar}', harus '{required_status}'.")
            return False
        logger.info("VALIDASI PEMBAYARAN: Lunas.")
        return True

# Inject validator baru ke Service lama
payment_validator = PaymentValidator()
service_payment = RegistrationService(payment_validator, val_logger)

# Jalankan validasi pembayaran untuk Budi
service_payment.process_validation(mhs_budi, "lunas")