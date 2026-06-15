import asyncio
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Any

# ==========================================
# Konfigurasi Logging
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# 1. Action Strategies (OOP Design)
# ==========================================
class ActionStrategy(ABC):
    """Abstract base class untuk semua strategi task (Blueprint OOP)."""
    @abstractmethod
    async def execute(self, target: str, user: str) -> None:
        """
        Fungsi abstrak yang harus diimplementasikan oleh setiap subclass untuk menjalankan task.
        :param target: String path/target yang akan dieksekusi.
        :param user: String username pengguna yang mengeksekusi task.
        """
        pass

class SyncStrategy(ActionStrategy):
    async def execute(self, target: str, user: str) -> None:
        """
        Mengeksekusi task sinkronisasi (sync).
        :param target: Lokasi direktori atau file sumber/tujuan yang akan disinkronisasikan.
        :param user: Nama pengguna yang menjalankan perintah sinkronisasi.
        """
        logger.info(f"User '{user}' executing SYNC on target: {target}")
        await asyncio.sleep(1) # Simulasi proses I/O / Network (Async)
        logger.info(f"User '{user}' SYNC completed.")

class BackupStrategy(ActionStrategy):
    async def execute(self, target: str, user: str) -> None:
        """
        Mengeksekusi task pencadangan (backup).
        :param target: Lokasi file atau folder yang akan dicadangkan (misal: direktori database atau server).
        :param user: Nama pengguna yang menjalankan backup.
        """
        logger.info(f"User '{user}' executing BACKUP on target: {target}")
        await asyncio.sleep(2)
        logger.info(f"User '{user}' BACKUP completed.")

class DeleteStrategy(ActionStrategy):
    async def execute(self, target: str, user: str) -> None:
        """
        Mengeksekusi task penghapusan (delete).
        :param target: Path file atau direktori yang akan dihapus secara permanen/sementara.
        :param user: Nama pengguna yang melakukan penghapusan.
        """
        logger.info(f"User '{user}' executing DELETE on target: {target}")
        await asyncio.sleep(0.5)
        logger.info(f"User '{user}' DELETE completed.")

class ActionFactory:
    """Factory pattern untuk mengambil instance dari class strategi berdasarkan string."""
    @staticmethod
    def get_strategy(action_name: str) -> ActionStrategy:
        """
        Mengembalikan objek ActionStrategy (Sync, Backup, atau Delete) sesuai input.
        :param action_name: Nama aksi (contoh: 'sync', 'backup').
        :return: Instance dari ActionStrategy.
        """
        strategies = {
            'sync': SyncStrategy(),
            'backup': BackupStrategy(),
            'delete': DeleteStrategy()
        }
        return strategies.get(action_name.lower())


# ==========================================
# 2. User Management & Quota Control
# ==========================================
class User:
    def __init__(self, username: str, quota: int):
        """
        Inisialisasi data pengguna beserta batas kuota hariannya.
        :param username: Nama pengguna (unik).
        :param quota: Batas maksimum task yang boleh dijalankan pengguna.
        """
        self.username = username
        self.quota = quota
        self.executed = 0

    def can_execute(self) -> bool:
        """
        Mengecek apakah pengguna masih memiliki sisa kuota.
        :return: True jika task yang sudah dieksekusi masih kurang dari batas kuota.
        """
        return self.executed < self.quota

    def increment_execution(self) -> None:
        """
        Menambahkan jumlah task yang sudah dieksekusi sebanyak 1.
        """
        self.executed += 1

class UserManager:
    def __init__(self):
        """
        Mengelola seluruh daftar pengguna dalam bentuk dictionary (Memory storage sederhana).
        """
        self.users: Dict[str, User] = {}

    def add_user(self, username: str, quota: int) -> None:
        """
        Menambahkan pengguna baru ke dalam sistem jika belum terdaftar.
        :param username: Nama pengguna baru.
        :param quota: Kuota yang diberikan.
        """
        if username not in self.users:
            self.users[username] = User(username, quota)

    def get_user(self, username: str) -> User:
        """
        Mencari dan mengembalikan objek User berdasarkan nama pengguna.
        :param username: Nama pengguna yang ingin dicari.
        :return: Objek User atau None jika tidak ditemukan.
        """
        return self.users.get(username)


# ==========================================
# 3. Task Data Model
# ==========================================
class Task:
    def __init__(self, user_id: str, time_str: str, action: str, params: Dict[str, Any]):
        """
        Membentuk model data untuk 1 buah jadwal/tugas.
        :param user_id: ID pengguna yang memiliki task.
        :param time_str: Waktu eksekusi dalam format string 'HH:MM'.
        :param action: Jenis aksi (misal: 'sync', 'backup').
        :param params: Parameter tambahan dinamis (misalnya target path).
        """
        self.user_id = user_id
        self.time = time_str
        self.action = action
        self.params = params

    def is_time_to_run(self, current_time: str) -> bool:
        """
        Memeriksa apakah waktu sekarang sesuai dengan jadwal task ini.
        :param current_time: Waktu saat ini (contoh: '12:00').
        :return: True jika cocok, False jika berbeda.
        """
        return self.time == current_time


# ==========================================
# 4. Scheduling System & Task Executor
# ==========================================
class Scheduler:
    def __init__(self, user_manager: UserManager):
        """
        Menyimpan daftar seluruh task dan objek manager pengguna.
        :param user_manager: Instance dari UserManager.
        """
        self.tasks: List[Task] = []
        self.user_manager = user_manager

    def add_task(self, task: Task) -> None:
        """
        Menambahkan task baru ke dalam antrean penjadwalan.
        :param task: Objek Task yang akan ditambahkan.
        """
        self.tasks.append(task)

    async def execute_task(self, task: Task) -> None:
        """
        Proses inti mengeksekusi satu tugas, mengecek kuota pengguna, 
        mencari strategi, lalu menjalankannya.
        :param task: Objek Task yang harus dieksekusi.
        """
        user = self.user_manager.get_user(task.user_id)
        if not user:
            logger.error(f"User '{task.user_id}' not found.")
            return

        if not user.can_execute():
            logger.warning(f"User '{user.username}' has exceeded quota (limit: {user.quota}). Task '{task.action}' skipped.")
            return

        strategy = ActionFactory.get_strategy(task.action)
        if not strategy:
            logger.error(f"Action strategy '{task.action}' is not supported.")
            return

        # Increment di awal agar terhindar dari race condition 
        # saat dieksekusi secara asinkron dalam waktu bersamaan
        user.increment_execution()
        
        target = task.params.get('target', 'unknown_target')
        try:
            await strategy.execute(target, user.username)
        except Exception as e:
            logger.error(f"Failed to execute task for {user.username}: {e}")

    async def run(self, current_time: str = None) -> None:
        """
        Menjalankan proses pengecekan jadwal. Jika ada task yang jadwalnya 
        sama dengan current_time, maka task tersebut dieksekusi secara concurrent (bersamaan).
        :param current_time: Waktu spesifik untuk dicek. Jika None, gunakan waktu nyata (sekarang).
        """
        if current_time is None:
            current_time = datetime.now().strftime('%H:%M')
        
        logger.info(f"Checking scheduled tasks for time: {current_time}")
        
        tasks_to_run = [task for task in self.tasks if task.is_time_to_run(current_time)]
        
        if not tasks_to_run:
            logger.info("No tasks scheduled for this time.")
            return

        # Eksekusi semua task di menit ini secara Asynchronous (Concurrent)
        coroutines = [self.execute_task(task) for task in tasks_to_run]
        await asyncio.gather(*coroutines)
