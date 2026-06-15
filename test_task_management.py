import unittest
from unittest.mock import AsyncMock, patch
from task_management import User, UserManager, Task, Scheduler, ActionFactory, SyncStrategy, BackupStrategy, DeleteStrategy

class TestUser(unittest.TestCase):
    def test_user_initialization(self):
        """Menguji apakah inisialisasi class User berjalan dengan benar."""
        user = User("alice", 3)
        self.assertEqual(user.username, "alice")
        self.assertEqual(user.quota, 3)
        self.assertEqual(user.executed, 0)

    def test_can_execute_quota(self):
        """Menguji logika batas kuota pengguna."""
        user = User("bob", 2)
        self.assertTrue(user.can_execute())
        user.increment_execution()
        self.assertTrue(user.can_execute())
        user.increment_execution()
        self.assertFalse(user.can_execute())

class TestUserManager(unittest.TestCase):
    def test_add_and_get_user(self):
        """Menguji penambahan dan pencarian pengguna pada UserManager."""
        manager = UserManager()
        manager.add_user("alice", 3)
        user = manager.get_user("alice")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "alice")
        self.assertEqual(user.quota, 3)

        # Menguji jika pengguna tidak ditemukan
        self.assertIsNone(manager.get_user("unknown"))

class TestTask(unittest.TestCase):
    def test_task_is_time_to_run(self):
        """Menguji pencocokan waktu eksekusi task."""
        task = Task("alice", "12:00", "sync", {"target": "/data"})
        self.assertTrue(task.is_time_to_run("12:00"))
        self.assertFalse(task.is_time_to_run("12:01"))

class TestActionFactory(unittest.TestCase):
    def test_get_strategy(self):
        """Menguji apakah ActionFactory mengembalikan strategi aksi yang benar."""
        self.assertIsInstance(ActionFactory.get_strategy("sync"), SyncStrategy)
        self.assertIsInstance(ActionFactory.get_strategy("backup"), BackupStrategy)
        self.assertIsInstance(ActionFactory.get_strategy("delete"), DeleteStrategy)
        self.assertIsNone(ActionFactory.get_strategy("invalid_action"))

class TestScheduler(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Setup sebelum menjalankan test kasus asinkron."""
        self.user_manager = UserManager()
        self.user_manager.add_user("alice", 2)
        self.scheduler = Scheduler(self.user_manager)

    async def test_add_task(self):
        """Menguji penambahan task ke dalam Scheduler."""
        task = Task("alice", "12:00", "sync", {"target": "/data"})
        self.scheduler.add_task(task)
        self.assertEqual(len(self.scheduler.tasks), 1)

    async def test_execute_task_success(self):
        """Menguji eksekusi task yang berhasil dan kuota bertambah."""
        task = Task("alice", "12:00", "sync", {"target": "/data"})
        
        # Menggunakan mock agar test berjalan cepat tanpa sleep nyata
        with patch.object(SyncStrategy, 'execute', new_callable=AsyncMock) as mock_execute:
            await self.scheduler.execute_task(task)
            mock_execute.assert_called_once_with("/data", "alice")
            
        user = self.user_manager.get_user("alice")
        self.assertEqual(user.executed, 1)

    async def test_execute_task_quota_exceeded(self):
        """Menguji bahwa task dilewati/skip jika pengguna melebihi kuota."""
        user = self.user_manager.get_user("alice")
        user.executed = 2 # Set quota penuh
        
        task = Task("alice", "12:00", "sync", {"target": "/data"})
        with patch.object(SyncStrategy, 'execute', new_callable=AsyncMock) as mock_execute:
            await self.scheduler.execute_task(task)
            mock_execute.assert_not_called()
            
        self.assertEqual(user.executed, 2) # Kuota tidak berubah

    async def test_execute_task_user_not_found(self):
        """Menguji penanganan ketika user tidak ditemukan di sistem."""
        task = Task("unknown_user", "12:00", "sync", {"target": "/data"})
        with patch.object(SyncStrategy, 'execute', new_callable=AsyncMock) as mock_execute:
            await self.scheduler.execute_task(task)
            mock_execute.assert_not_called()

    async def test_scheduler_run(self):
        """Menguji jalannya Scheduler.run() untuk memproses task pada waktu tertentu secara bersamaan."""
        task1 = Task("alice", "12:00", "sync", {"target": "/data/1"})
        task2 = Task("alice", "12:00", "backup", {"target": "/data/2"})
        task3 = Task("alice", "12:01", "delete", {"target": "/data/3"}) # Waktu berbeda
        
        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)
        self.scheduler.add_task(task3)

        with patch.object(SyncStrategy, 'execute', new_callable=AsyncMock) as mock_sync, \
             patch.object(BackupStrategy, 'execute', new_callable=AsyncMock) as mock_backup:
            await self.scheduler.run("12:00")
            mock_sync.assert_called_once()
            mock_backup.assert_called_once()

if __name__ == '__main__':
    unittest.main()
