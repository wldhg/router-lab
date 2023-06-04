import { atom } from "recoil";

interface WorldInformation {
  id: string;
  subnet: string;
  mtu: number;
  node_ips: string[];
  topo: boolean[][];
  bit_corrupt_rate: number;
  node_down_rate: number;
  initialized_at: number;
}

const worldInformation = atom<WorldInformation>({
  key: "world:worldInformation",
  default: {
    id: "",
    subnet: "",
    mtu: 0,
    node_ips: [],
    topo: [],
    bit_corrupt_rate: 0,
    node_down_rate: 0,
    initialized_at: 0,
  },
});

type WorldState = "initialized" | "configured" | "running" | "stopped";

interface WorldStatistics {
  state: WorldState;
  started_at: number;
  transmissions: (string | number)[][];
  nodes_updown: {
    [key: string]: boolean;
  };
  world_1hop_latency: number;
  world_1hop_throughput: number;
  world_stats: number[];
  custom_stats: {
    [key: string]: number[];
  };
}

const worldStats = atom<WorldStatistics>({
  key: "world:worldStats",
  default: {
    state: "initialized",
    started_at: 0,
    transmissions: [],
    nodes_updown: {},
    world_1hop_latency: 0,
    world_1hop_throughput: 0,
    world_stats: [],
    custom_stats: {},
  },
});

const worldLogsPointer = atom<number>({
  key: "world:worldLogsPointer",
  default: 0,
});

const worldLogs = atom<string[]>({
  key: "world:worldLogs",
  default: [],
});

export type { WorldInformation, WorldState, WorldStatistics };
export {
  worldInformation as worldInformation_,
  worldStats as worldStats_,
  worldLogs as worldLogs_,
  worldLogsPointer as worldLogsPointer_,
};
