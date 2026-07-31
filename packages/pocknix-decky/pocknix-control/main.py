import asyncio

from pocknix_control.config import build_config
from pocknix_control.lighting import (
    set_stick_led_color,
    set_stick_led_flash_color,
    set_stick_led_mode,
    set_stick_led_param,
    set_stick_led_screen_link,
)
from pocknix_control.modes import set_fan_mode, set_lavd_mode
from pocknix_control.sdcard import detect_sdcard, format_sdcard
from pocknix_control.snapshots import reboot_system, snapshot_status, start_rollback
from pocknix_control.tweaks import save_tweaks
from pocknix_control.updates import check_updates, start_update, update_status


class Plugin:
    # Offload blocking work to a thread so a slow call can't stall Decky's asyncio loop.
    async def get_config(self):
        return await asyncio.to_thread(build_config)

    async def detect_sdcard(self):
        return await asyncio.to_thread(detect_sdcard)

    async def format_sdcard(self, label):
        return await asyncio.to_thread(format_sdcard, label)

    async def set_fan_mode(self, mode):
        await asyncio.to_thread(set_fan_mode, mode)
        return await self.get_config()

    async def set_lavd_mode(self, mode):
        await asyncio.to_thread(set_lavd_mode, mode)
        return await self.get_config()

    async def save_tweaks(self, data):
        await asyncio.to_thread(save_tweaks, data)
        return await self.get_config()

    async def check_updates(self):
        return await asyncio.to_thread(check_updates)

    async def start_update(self):
        return await asyncio.to_thread(start_update)

    async def update_status(self):
        return await asyncio.to_thread(update_status)

    async def snapshot_status(self):
        return await asyncio.to_thread(snapshot_status)

    async def start_rollback(self, snapshot_id):
        return await asyncio.to_thread(start_rollback, snapshot_id)

    async def reboot_system(self):
        return await asyncio.to_thread(reboot_system)

    async def set_stick_led_color(self, value):
        return await asyncio.to_thread(set_stick_led_color, value)

    async def set_stick_led_mode(self, mode):
        return await asyncio.to_thread(set_stick_led_mode, mode)

    async def set_stick_led_screen_link(self, enabled):
        return await asyncio.to_thread(set_stick_led_screen_link, enabled)

    async def set_stick_led_param(self, param, mode, value):
        return await asyncio.to_thread(set_stick_led_param, param, mode, value)

    async def set_stick_led_flash_color(self, button, value):
        return await asyncio.to_thread(set_stick_led_flash_color, button, value)
