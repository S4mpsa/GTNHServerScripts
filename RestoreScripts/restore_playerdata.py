import shutil

from _utils import getBackupPath, standardUnzip


backup_paths = getBackupPath()
server_root, backup_zip_path, unzipped_backup_path, horizons_name = backup_paths

standardUnzip(*backup_paths)

# Want to just overwrite the playerdata file for a specific player
UUID = input('Please enter full UUID of player.\nYou can look up full UUID here: mcuuid.net\n')
old_UUID_path = unzipped_backup_path / f'playerdata/{UUID}.dat'
corrupted_UUID_path = server_root / f'Horizons/playerdata/{UUID}.dat'

if old_UUID_path.exists():
    shutil.move(old_UUID_path, corrupted_UUID_path)
else:
    print('Could not find playerdata file matching that UUID in backup! You probably mistyped it.')


