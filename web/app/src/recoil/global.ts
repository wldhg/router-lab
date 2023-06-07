import { atom } from "recoil";
import { Socket } from "socket.io-client";
import { localStorageEffect } from "./utils";

type GlobalState =
  | "connecting"
  | "connected"
  | "configuring"
  | "configured"
  | "starting"
  | "running"
  | "stopping"
  | "stopped";

const globalState = atom<GlobalState>({
  key: "global:globalState",
  default: "connecting",
});

const globalSocket = atom<Socket | null>({
  key: "global:globalSocket",
  default: null,
  dangerouslyAllowMutability: true,
});

const globalAlgorithm = atom<string>({
  key: "global:globalAlgorithm",
  default: "",
});

interface GlobalConfigurationParameters {
  node_num: number;
  link_sparsity: number;
  kbps_min: number;
  kbps_max: number;
  kbps_std_max: number;
  bit_corrupt_rate: number;
  node_down_rate: number;
  node_enqueue_rate: number;
}

const globalConfigurationParameters = atom<GlobalConfigurationParameters>({
  key: "global:globalConfigurationParameters",
  default: {
    node_num: 20,
    link_sparsity: 2,
    kbps_min: 0.8,
    kbps_max: 1.2,
    kbps_std_max: 0.005,
    bit_corrupt_rate: 0.0001,
    node_down_rate: 0.01,
    node_enqueue_rate: 0.1,
  },
});

const globalTheme = atom<"dark" | "light">({
  key: "global:globalTheme",
  default: "dark",
});

const globalResubscriptionRequired = atom<boolean>({
  key: "global:globalResubscriptionRequired",
  default: false,
});

const globalTopPanelPinned = atom<boolean>({
  key: "global:globalTopPanelPinned",
  default: false,
});

const globalUse3DGraph = atom<boolean>({
  key: "global:globalUse3DGraph",
  default: true,
  effects: [localStorageEffect("global:globalUse3DGraph")],
});

export type { GlobalState, GlobalConfigurationParameters };
export {
  globalState as globalState_,
  globalSocket as globalSocket_,
  globalAlgorithm as globalAlgorithm_,
  globalTheme as globalTheme_,
  globalConfigurationParameters as globalConfigurationParameters_,
  globalResubscriptionRequired as globalResubscriptionRequired_,
  globalTopPanelPinned as globalTopPanelPinned_,
  globalUse3DGraph as globalUse3DGraph_,
};
