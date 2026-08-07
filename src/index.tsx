import { definePlugin, routerHook } from "@decky/api";
import { staticClasses } from "@decky/ui";
import { FaLightbulb } from "react-icons/fa";

import { QuickAccess, SETTINGS_ROUTE, SettingsPage } from "./components";
import { controller } from "./model";

export default definePlugin(() => {
  routerHook.addRoute(SETTINGS_ROUTE, SettingsPage, { exact: true });
  const resumeRegistration = SteamClient.System.RegisterForOnResumeFromSuspend(
    () => void controller.resume(),
  );
  void controller.initialize();

  return {
    name: "OpenRGB",
    titleView: <div className={staticClasses.Title}>OpenRGB</div>,
    content: <QuickAccess />,
    icon: <FaLightbulb />,
    onDismount() {
      controller.shutdown();
      resumeRegistration.unregister();
      routerHook.removeRoute(SETTINGS_ROUTE);
    },
  };
});
