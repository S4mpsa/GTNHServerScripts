import shutil

from _utils import getBackupPath, standardUnzip


backup_paths = getBackupPath()
server_root, backup_zip_path, unzipped_backup_path, horizons_name = backup_paths

standardUnzip(*backup_paths)

# Perform actual server backup restore
horizons_main_path = server_root / horizons_name
horizons_backup_path = server_root / f'{horizons_name}.bak'

shutil.move(horizons_main_path, horizons_backup_path)
shutil.move(unzipped_backup_path, horizons_main_path)

print('Backup restore complete! You may now restart the server.')

