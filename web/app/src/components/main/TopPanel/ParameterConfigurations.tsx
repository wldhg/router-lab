import {
  globalConfigurationParameters_,
  globalSocket_,
  globalState_,
  worldLogsPointer_,
  worldLogs_,
  worldStats_,
} from "@/recoil";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Slider from "@mui/material/Slider";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { createPortal } from "react-dom";
import { useRecoilState, useRecoilValue, useSetRecoilState } from "recoil";

interface ParameterConfigurationSliderProps {
  label: string;
  description: string;
  marks: {
    [key: number]: string;
  };
  value: number | number[];
  step: number;
  value_min: number;
  value_max: number;
  onChange: (value: number | number[]) => void;
  disabled: boolean;
  useInput: boolean;
  useWideInput?: boolean;
}

const ParameterConfigurationSlider = (
  props: ParameterConfigurationSliderProps
) => {
  const {
    label,
    step,
    description,
    marks,
    value,
    value_min,
    value_max,
    useInput,
    useWideInput,
    disabled,
    onChange,
  } = props;

  const marksArray = Object.entries(marks).map(([key, value]) => ({
    value: Number(key),
    label: value,
  }));

  const onSliderChange = (
    event: Event,
    value: number | number[],
    activeThumb: number
  ) => {
    onChange(value);
  };

  const onInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange(Number(event.target.value));
  };

  const isError =
    (typeof value === "number" && (value < value_min || value > value_max)) ||
    (Array.isArray(value) && (value[0] < value_min || value[1] > value_max));

  return (
    <Box
      sx={{
        display: "inline-block",
        width: "300px",
        height: "120px",
        mr: 8,
        mb: 2,
      }}
    >
      <Stack
        sx={{
          flexDirection: "column",
          gap: 1,
        }}
      >
        <Stack>
          <Typography variant="body1" sx={{ fontWeight: 700 }}>
            {label}
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.5 }}>
            {description}
          </Typography>
        </Stack>
        <Stack sx={{ flexDirection: "row", gap: 2 }}>
          <Slider
            sx={{
              mx: 1,
              width: useInput ? (useWideInput ? "160px" : "200px") : "280px",
            }}
            value={value}
            min={value_min}
            max={value_max}
            onChange={onSliderChange}
            step={step}
            disabled={disabled}
            valueLabelDisplay={useInput ? "off" : "auto"}
            marks={marksArray}
          />
          {useInput && (
            <TextField
              value={value}
              size="small"
              onChange={onInputChange}
              disabled={disabled}
              error={isError}
              inputProps={{
                step: 1,
                min: value_min,
                max: value_max,
                type: "number",
                "aria-labelledby": "input-slider",
              }}
              sx={{
                width: useWideInput ? "120px" : "80px",
                mx: 1,
                "& input": {
                  fontSize: "0.875rem",
                },
              }}
            />
          )}
        </Stack>
        {isError && (
          <Typography variant="body2" sx={{ color: "error.main" }}>
            Value should be between {value_min} and {value_max}.
          </Typography>
        )}
      </Stack>
    </Box>
  );
};

ParameterConfigurationSlider.defaultProps = {
  useWideInput: false,
};

const ParameterConfigurations = () => {
  const [globalConfigurationParameters, setGlobalConfigurationParameters] =
    useRecoilState(globalConfigurationParameters_);
  const globalSocket = useRecoilValue(globalSocket_);
  const [globalState, setGlobalState] = useRecoilState(globalState_);
  const setWorldStats = useSetRecoilState(worldStats_);
  const setWorldLogs = useSetRecoilState(worldLogs_);
  const setWorldLogsPointer = useSetRecoilState(worldLogsPointer_);

  const isError = Object.entries(globalConfigurationParameters).some(
    ([key, value]) => {
      if (key === "kbps_min" || key === "kbps_max") {
        return value < 0.01 || value > 10.0;
      } else if (key === "node_num") {
        return value < 5 || value > 160;
      } else if (key === "link_sparsity") {
        return value < 0 || value > 4;
      } else if (key === "kbps_std_max") {
        return value < 0 || value > 0.01;
      } else if (key === "bit_corrupt_rate") {
        return value < 0 || value > 0.001;
      } else if (key === "node_down_rate") {
        return value < 0 || value > 0.05;
      } else if (key === "node_enqueue_rate") {
        return value < 0 || value > 1.0;
      }
      return false;
    }
  );

  const configureWorld = () => {
    if (globalSocket === null) {
      return;
    }
    setGlobalState("configuring");
    globalSocket.once("world_configure", (answer) => {
      if (answer["status"] === 200) {
        globalSocket.off("subscribe_world_stats");
        globalSocket.once("subscribe_world_stats", (data) => {
          if (data["status"] === 200) {
            setWorldStats(data["data"]);
            globalSocket.on("subscribe_world_stats", (data) => {
              if (data["status"] !== 200) return;
              setWorldStats(data["data"]);
            });
            globalSocket.off("subscribe_world_logs");
            globalSocket.once("subscribe_world_logs", (data) => {
              if (data["status"] === 200) {
                setWorldLogs(
                  data["data"].slice(Math.max(data["data"].length - 2048, 0))
                );
                setWorldLogsPointer(data["data"].length);
                globalSocket.on("subscribe_world_logs", (data) => {
                  if (data["status"] !== 200) return;
                  setWorldLogsPointer((oldPointer) => {
                    const newPointer = oldPointer + data["data"].length;
                    return newPointer;
                  });
                  setWorldLogs((oldLogs) => {
                    const newLogs = [...oldLogs, ...data["data"]];
                    return newLogs.slice(Math.max(newLogs.length - 2048, 0));
                  });
                });
                setGlobalState("configured");
              } else {
                globalSocket.off("subscribe_world_stats");
                setGlobalState("connected");
              }
            });
            globalSocket.emit("subscribe_world_logs");
          } else {
            setGlobalState("connected");
          }
        });
        globalSocket.emit("subscribe_world_stats");
      } else {
        setGlobalState("connected");
      }
    });
    globalSocket.emit("world_configure", globalConfigurationParameters);
  };

  return (
    <>
      <Stack sx={{ flexDirection: "column", gap: 2 }}>
        <Typography variant="h5" gutterBottom>
          World Configuration Parameters
        </Typography>
        <Box
          sx={{
            width: "100%",
            flexGrow: 1,
            maxHeight: "280px",
            overflowY: "auto",
          }}
        >
          <ParameterConfigurationSlider
            label="Number of Nodes"
            description="The number of nodes in the network."
            marks={{
              5: "5",
              160: "160",
            }}
            value={globalConfigurationParameters.node_num}
            value_min={5}
            value_max={160}
            disabled={globalState === "configuring"}
            step={1}
            onChange={(value: number | number[]) => {
              setGlobalConfigurationParameters({
                ...globalConfigurationParameters,
                node_num: value as number,
              });
            }}
            useInput
          />
          <ParameterConfigurationSlider
            label="Link Sparsity"
            description="Higher value means more sparse network."
            marks={{
              0: "0",
              1: "1",
              2: "2",
              3: "3",
              4: "4",
            }}
            value={globalConfigurationParameters.link_sparsity}
            value_min={0}
            value_max={4}
            disabled={globalState === "configuring"}
            step={1}
            onChange={(value: number | number[]) => {
              setGlobalConfigurationParameters({
                ...globalConfigurationParameters,
                link_sparsity: value as number,
              });
            }}
            useInput
          />
          <ParameterConfigurationSlider
            label="Link Speed (kbps)"
            description="Range of link speed in kbps."
            marks={{
              0.01: "0.01",
              2.0: "2.0",
              4.0: "4.0",
              6.0: "6.0",
              8.0: "8.0",
              10.0: "10.0",
            }}
            value={[
              globalConfigurationParameters.kbps_min,
              globalConfigurationParameters.kbps_max,
            ]}
            disabled={globalState === "configuring"}
            value_min={0.01}
            value_max={10.0}
            step={0.001}
            onChange={(value: number | number[]) => {
              setGlobalConfigurationParameters({
                ...globalConfigurationParameters,
                kbps_min: (value as number[])[0],
                kbps_max: (value as number[])[1],
              });
            }}
            useInput={false}
          />
          <ParameterConfigurationSlider
            label="Link Speed Variance (kbps)"
            description="Variance of link speed in kbps."
            marks={{
              0: "0",
              0.005: "0.005",
              0.01: "0.01",
            }}
            value={globalConfigurationParameters.kbps_std_max}
            value_min={0}
            value_max={0.01}
            step={0.001}
            disabled={globalState === "configuring"}
            onChange={(value: number | number[]) => {
              setGlobalConfigurationParameters({
                ...globalConfigurationParameters,
                kbps_std_max: value as number,
              });
            }}
            useInput
          />
          <ParameterConfigurationSlider
            label="Bit Corruption Rate"
            description="The binomial probability of bit corruption."
            marks={{
              0: "0",
              0.0005: "0.0005",
              0.001: "0.001",
            }}
            value={globalConfigurationParameters.bit_corrupt_rate}
            value_min={0}
            value_max={0.001}
            step={0.00001}
            disabled={globalState === "configuring"}
            onChange={(value: number | number[]) => {
              setGlobalConfigurationParameters({
                ...globalConfigurationParameters,
                bit_corrupt_rate: value as number,
              });
            }}
            useInput
            useWideInput
          />
          <ParameterConfigurationSlider
            label="Node Failure Rate"
            description="The binomial probability of node failure."
            marks={{
              0: "0",
              0.01: "0.01",
              0.03: "0.03",
              0.05: "0.05",
            }}
            value={globalConfigurationParameters.node_down_rate}
            value_min={0}
            value_max={0.05}
            disabled={globalState === "configuring"}
            step={0.0005}
            onChange={(value: number | number[]) => {
              setGlobalConfigurationParameters({
                ...globalConfigurationParameters,
                node_down_rate: value as number,
              });
            }}
            useInput
            useWideInput
          />
          <ParameterConfigurationSlider
            label="Node Packet Enqueue Rate"
            description="The probability of packet enqueue from applications, for every seconds."
            marks={{
              0.0: "0",
              0.2: "0.2",
              0.4: "0.4",
              0.6: "0.6",
              0.8: "0.8",
              1.0: "1",
            }}
            value={globalConfigurationParameters.node_enqueue_rate}
            value_min={0}
            value_max={1.0}
            disabled={globalState === "configuring"}
            step={0.01}
            onChange={(value: number | number[]) => {
              setGlobalConfigurationParameters({
                ...globalConfigurationParameters,
                node_enqueue_rate: value as number,
              });
            }}
            useInput
          />
        </Box>
      </Stack>
      {document.getElementById("ts_x1") &&
        createPortal(
          <>
            <Button
              variant="contained"
              disabled={isError || globalState === "configuring"}
              onClick={configureWorld}
            >
              Configure World
            </Button>
            <Typography variant="body2" sx={{ color: "error.main" }}>
              {isError && "Please fix the errors below."}
            </Typography>
            {globalState === "configuring" && (
              <CircularProgress size={20} sx={{ ml: -2 }} />
            )}
          </>,
          document.getElementById("ts_x1") as HTMLDivElement
        )}
    </>
  );
};

export default ParameterConfigurations;
