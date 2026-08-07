import os

# The decky plugin module is located at decky-loader/plugin
# For easy intellisense checkout the decky-loader code repo
# and add the `decky-loader/plugin/imports` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky

from py_modules import OpenRGBBackend, SettingsStore


class Plugin:
    async def _main(self):
        store = SettingsStore(
            os.path.join(decky.DECKY_PLUGIN_SETTINGS_DIR, "settings.json"),
            decky.logger,
        )
        self.backend = OpenRGBBackend(
            store,
            decky.DECKY_USER_HOME,
            decky.logger,
        )
        await self.backend.start()
        decky.logger.info("Decky OpenRGB backend initialized")

    async def _unload(self):
        await self.backend.unload()
        decky.logger.info("Decky OpenRGB backend unloaded")

    async def _uninstall(self):
        decky.logger.info("Decky OpenRGB plugin uninstalled")

    async def get_state(self):
        return await self.backend.get_state()

    async def refresh_profiles(self):
        return await self.backend.refresh_profiles()

    async def set_selected_profile(self, identifier=None):
        return await self.backend.set_selected_profile(identifier)

    async def set_automatic_apply(self, enabled):
        return await self.backend.set_automatic_apply(enabled)

    async def save_advanced_settings(self, draft):
        return await self.backend.save_advanced_settings(draft)

    async def apply_selected(self, trigger):
        return await self.backend.apply_selected(trigger)
