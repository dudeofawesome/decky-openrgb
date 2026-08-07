import { useSyncExternalStore } from "react";

import { controller, ViewState } from "./model";

export const useOpenRgb = (): ViewState =>
  useSyncExternalStore(controller.subscribe, controller.getSnapshot);
