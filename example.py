import asyncio
from datetime import timedelta
import logging
from logging import getLogger, StreamHandler
import sys

from tqdm import tqdm

from mmkv_abi.drive_info.drive_state import DriveState
from mmkv_abi.mmkv import MakeMKV
from mmkv_abi.app_string import AppString

async def main():
    makemkv = MakeMKV(setup_logger(logging.INFO))
    await makemkv.init()

    print(f'MakeMKV version: {await makemkv.get_app_string(AppString.Version)}')
    print(f'MakeMKV platform: {await makemkv.get_app_string(AppString.Platform)}')
    print(f'MakeMKV build: {await makemkv.get_app_string(AppString.Build)}')
    print(f'Interface language: {await makemkv.get_app_string(AppString.InterfaceLanguage)}')

    await makemkv.set_output_folder('/home/dex/Videos')
    await makemkv.update_avalible_drives()

    print('Waiting for disc...')
    await wait_for_disc_inserted(makemkv)

    print('Waiting for titles...')
    await wait_for_titles_populated(makemkv)

    lower_bound = timedelta(minutes=20)
    upper_bound = timedelta(minutes=50)

    for title in makemkv.titles:
        duration = await title.get_duration()
        await title.set_enabled(duration > lower_bound and duration < upper_bound)

    print('\n\nTitle Tree:')
    await makemkv.titles.print()

    print('\n\nSaving selected titles...')
    await makemkv.save_all_selected_to_mkv()

    with tqdm(total=65536) as pbar:
        while makemkv.job_mode:
            if pbar.n > makemkv.total_bar:
                pbar.reset()
                pbar.update(makemkv.total_bar)
            else:
                pbar.update(makemkv.total_bar - pbar.n)

            pbar.set_description(makemkv.current_info[4])
            pbar.set_postfix_str(makemkv.current_info[3])

            await makemkv.idle()
            await asyncio.sleep(0.25)

def setup_logger(log_level):
    logger = getLogger(__name__)
    logger.setLevel(log_level)

    handler = StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    logger.addHandler(handler)
    return logger

async def wait_for_disc_inserted(makemkv):
    while True:
        drives = [v for v in makemkv.drives.values() if v.drive_state is DriveState.Inserted]
        if len(drives) > 0:
            drive = drives[0]
            await makemkv.open_cd_disk(drive.drive_id)
            break

        await makemkv.idle()
        await asyncio.sleep(0.25)

async def wait_for_titles_populated(makemkv):
    while makemkv.titles is None:
        await makemkv.idle()
        await asyncio.sleep(0.25)

if __name__ == '__main__':
    asyncio.run(main())
