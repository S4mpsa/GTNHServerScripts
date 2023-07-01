import os
import shutil
from pathlib import Path
from zipfile import ZipFile

import pendulum


def getBackupPath():
    server_name = input('Please enter server name (accepted: GDCloud, server, skyblock,ballers). ')
    assert server_name in ['GDCloud', 'server', 'skyblock','ballers']
    server_files_lookup = {
        'GDCloud': 'World',
        'server': 'Horizons',
        'skyblock': 'Skyblock',
        'ballers': 'Gateworld',
    }
    horizons_name = server_files_lookup[server_name]

    server_root = Path(__file__).parent / server_name
    backup_path = server_root / 'backups'

    timezone = input('Enter Pendulum timezone to convert backup dates to (eg US/Pacific): ')

    last_5 = sorted(os.listdir(backup_path))
    print('Select backup:')
    for idx, time_str in enumerate(last_5):
        print('   ', idx+1, time_str, f'({utfToTZ(time_str, timezone)})')

    usr_in = input('Index: ')
    usr_idx = int(usr_in) - 1

    backup_zip_path = backup_path / last_5[usr_idx] / 'backup.zip'
    unzipped_backup_path = backup_zip_path.parent / horizons_name

    return (
        server_root,
        backup_zip_path,
        unzipped_backup_path,
        horizons_name,
    )


def utfToTZ(utc_str, tz):
    utc_str += '-+0100'
    backup_date = pendulum.from_format(utc_str, 'YYYY-MM-DD-HH-mm-ss-ZZ')
    converted = backup_date.in_tz(tz=tz).format('YYYY-MM-DD HH:mm')
    return converted


def standardUnzip(server_root, backup_zip_path, unzipped_backup_path, horizons_name):
    if unzipped_backup_path.exists():
        print('Backup already extracted! Using cached version.')
    else:
        print('Extracting backup ZIP...')
        with ZipFile(backup_zip_path, 'r') as f:
            f.extractall(backup_zip_path.parent)

    horizons_backup_path = server_root / f'{horizons_name}.bak'
    if horizons_backup_path.exists():
        yn = input(f'Delete old {horizons_name}.bak folder from previous backup restore? [y/n] ')
        if yn in ['y', 'Y']:
            shutil.rmtree(horizons_backup_path) 
        else:
            raise RuntimeError('Please fix accordingly and start over.')

