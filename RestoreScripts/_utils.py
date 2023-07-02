import os
import shutil
from pathlib import Path
from zipfile import ZipFile

import pendulum
from yaml import safe_load


def loadConfig():
    own_path = Path(__file__)
    config_path = own_path.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        config = safe_load(f)

    # Post-processing
    config['tz'] = config['tz'].strip()

    # Sanity checks
    assert config['use'] in ['utc', 'tz'], '"use" must be either "utc" or "tz" in config.yaml.'
    if config['use'] == 'tz':
        assert config['tz'] in pendulum.timezones, '\n'.join([
            f'Invalid timezone: {config["tz"]}.',
            f'Valid timezones:',
            f'{pendulum.timezones}',
        ])

    server_path = own_path.parent / config['server_folder']
    backups_path = server_path / 'backups'
    if not server_path.exists():
        raise RuntimeError(f'No server folder at path: {server_path.absolute()}')
    if not backups_path.exists():
        raise RuntimeError(f'No backups at path {backups_path.absolute()}')
    
    return config


def getBackupPath():
    config = loadConfig()

    server_root = Path(__file__).parent / config['server_folder']
    backup_path = server_root / 'backups'
    horizons_name = config['horizons_name']

    timezone = input('Enter Pendulum timezone to convert backup dates to (eg US/Pacific): ')
    if config['use'] == 'utc':
        timezone = config['utc-offset']
    elif config['use'] == 'tz':
        timezone = config['tz']

    last_5 = sorted(os.listdir(backup_path))
    print('Select backup:')
    for idx, time_str in enumerate(last_5):
        print('   ', idx+1, time_str, f'({serverTimestampToTZ(time_str, timezone)})')

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


def serverTimestampToTZ(utc_str, tz):
    # I don't understand why this is UTC+1 when both Helsinki and Falkenstein
    #   are UTC+2, but it works...
    utc_str += '-+0100'
    backup_date = pendulum.from_format(utc_str, 'YYYY-MM-DD-HH-mm-ss-ZZ')

    converted = backup_date.in_tz(tz=tz).format('YYYY-MM-DD HH:mm')

    return converted


def standardUnzip(server_root, backup_zip_path, unzipped_backup_path, horizons_name):
    config = loadConfig()

    if unzipped_backup_path.exists():
        print('Backup already extracted! Using cached version.')
    else:
        print('Extracting backup ZIP...')
        with ZipFile(backup_zip_path, 'r') as f:
            f.extractall(backup_zip_path.parent)

    horizons_backup_path = server_root / f'{horizons_name}.bak'
    if horizons_backup_path.exists():
        if config['autodelete_old_bak_folder']:
            shutil.rmtree(horizons_backup_path)
        else:
            yn = input(f'Delete old {horizons_name}.bak folder from previous backup restore? [y/n] ')
            if yn in ['y', 'Y']:
                shutil.rmtree(horizons_backup_path) 
            else:
                raise RuntimeError('Please fix accordingly and start over.')

