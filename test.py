import asyncio
import task_management
from datetime import datetime

# ==========================================
# Simulasi / Entry Point
# ==========================================
async def main():
    """
    Fungsi utama (Entry Point) untuk mensimulasikan penggunaan sistem penjadwalan 
    dari penyiapan User, pembuatan Task, hingga simulasi eksekusi secara Asynchronous.
    """
    # 1. Setup User Manager
    user_manager = task_management.UserManager()
    user_manager.add_user('alice', quota=3)
    user_manager.add_user('bob', quota=5)

    # 2. Setup Scheduler
    scheduler = task_management.Scheduler(user_manager)

    # 3. Setup Tasks dengan parameter dinamis
    # Kita menggunakan waktu saat ini agar saat dijalankan, logic-nya langsung ter-trigger
    now = datetime.now().strftime('%H:%M')
    
    tasks_data = [
        {'user': 'alice', 'time': now, 'action': 'sync', 'params': {'target': '/data/x'}},
        {'user': 'bob', 'time': now, 'action': 'backup', 'params': {'target': '/srv/y'}},
        {'user': 'alice', 'time': now, 'action': 'delete', 'params': {'target': '/tmp/z'}},
        
        # Tambahan simulasi: user alice punya lebih banyak task di waktu bersamaan
        {'user': 'alice', 'time': now, 'action': 'sync', 'params': {'target': '/data/a'}}, 
        
        # Task ke-4 Alice ini harusnya gagal/skip karena kuota hanya 3
        {'user': 'alice', 'time': now, 'action': 'backup', 'params': {'target': '/data/b'}},
    ]

    for data in tasks_data:
        task = task_management.Task(data['user'], data['time'], data['action'], data['params'])
        scheduler.add_task(task)

    # 4. Jalankan penjadwalan
    await scheduler.run(now)

if __name__ == '__main__':
    # Mulai async event loop
    asyncio.run(main())
