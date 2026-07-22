import os
import shutil
from datetime import datetime

db_path = 'instance/kasir.db'
import os
import shutil
from datetime import datetime

db_path = 'instance/kasir.db'
backup_dir = 'backup'

# ini tambahin biar bikin folder backup otomatis
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'kasir_backup_{timestamp}.db'

shutil.copy2(db_path, os.path.join(backup_dir, backup_file))
print(f'Backup saved: {backup_file}')
