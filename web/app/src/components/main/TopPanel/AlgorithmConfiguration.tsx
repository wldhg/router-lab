import {
  globalAlgorithm_,
  globalResubscriptionRequired_,
  globalSocket_,
  globalState_,
  worldInformation_,
  worldLogsPointer_,
  worldLogs_,
  worldStats_,
} from "@/recoil";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useRecoilState, useRecoilValue, useSetRecoilState } from "recoil";

const AlgorithmConfiguration = () => {
  const [globalAlgorithm, setGlobalAlgorithm] =
    useRecoilState(globalAlgorithm_);
  const [availableAlgorithms, setAvailableAlgorithms] = useState<string[]>([]);
  const globalSocket = useRecoilValue(globalSocket_);
  const [globalState, setGlobalState] = useRecoilState(globalState_);
  const [globalResubscriptionRequired, setGlobalResubscriptionRequired] =
    useRecoilState(globalResubscriptionRequired_);
  const setWorldInformation = useSetRecoilState(worldInformation_);
  const setWorldStats = useSetRecoilState(worldStats_);
  const setWorldLogs = useSetRecoilState(worldLogs_);
  const setWorldLogsPointer = useSetRecoilState(worldLogsPointer_);
  const [isReady1, setIsReady1] = useState(false);
  const [isReady2, setIsReady2] = useState(false);

  useEffect(
    () => {
      if (globalResubscriptionRequired && globalSocket) {
        setGlobalResubscriptionRequired(false);
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
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      /* ONCE ON MOUNT */
    ]
  );

  useEffect(() => {
    if (globalSocket) {
      globalSocket.once("list_impls", (data) => {
        setAvailableAlgorithms(data["data"]);
        setIsReady1(true);
      });
      globalSocket.emit("list_impls");
      globalSocket.once("world_info", (data) => {
        setWorldInformation(data["data"]);
        setIsReady2(true);
      });
      globalSocket.emit("world_info");
    }
  }, [globalSocket, setWorldInformation]);

  const handleStart = () => {
    if (globalSocket) {
      globalSocket.once("world_start", (data) => {
        if (data["status"] === 200) {
          setGlobalState("running");
        } else {
          console.error(data["error"]);
          setGlobalState("configured");
        }
      });
      globalSocket.emit("world_start", {
        algo: globalAlgorithm,
      });
      setGlobalState("starting");
    }
  };

  const handleReset = () => {
    setGlobalState("connected");
  };

  const isReady = isReady1 && isReady2;

  return (
    <>
      <Stack sx={{ flexDirection: "column", gap: 2 }}>
        <Typography variant="h5" gutterBottom>
          Algorithm Selection
        </Typography>
        <Typography variant="body1" gutterBottom>
          Select one of your implementation(s) to use for the experiment.
        </Typography>
        {isReady ? (
          <Box sx={{ width: "100%", height: "240px", overflowY: "auto" }}>
            {availableAlgorithms.map((algo) => {
              return (
                <Card
                  elevation={5}
                  key={algo}
                  sx={{
                    width: "200px",
                    height: "180px",
                    backgroundColor:
                      globalAlgorithm === algo
                        ? "primary.main"
                        : "rgba(140, 140, 140, 0.2)",
                    color:
                      globalAlgorithm === algo
                        ? "primary.contrastText"
                        : "primary.main",
                    mr: 2,
                    display: "inline-block",
                    p: 2,
                    fontFamily: "'Fira Mono', monospace",
                    fontSize: "1.2rem",
                    transition: "all 0.2s ease-in-out",
                    wordBreak: "break-all",
                    cursor: globalState === "starting" ? "default" : "pointer",
                    opacity: globalState === "starting" ? 0.5 : 1,
                    transform: globalState === "starting" ? "scale(0.95)" : "",
                    ":hover": {
                      backgroundColor:
                        globalAlgorithm === algo
                          ? "primary.main"
                          : "rgba(140, 140, 140, 0.4)",
                    },
                    ":active": {
                      backgroundColor: "rgba(140, 140, 140, 0.6)",
                      transform: "scale(0.95)",
                    },
                  }}
                  onClick={() => {
                    if (globalState === "starting") return;
                    setGlobalAlgorithm(algo);
                  }}
                >
                  {algo}
                  {globalAlgorithm === algo && (
                    <Stack
                      sx={{
                        flexDirection: "row",
                        display: "flex",
                        alignItems: "center",
                        mt: 1,
                      }}
                    >
                      <CheckCircleIcon sx={{ mr: 0.5 }} />
                      <Typography
                        variant="body2"
                        sx={{ fontSize: "0.8rem", display: "inline" }}
                      >
                        Selected
                      </Typography>
                    </Stack>
                  )}
                </Card>
              );
            })}
          </Box>
        ) : (
          <Box
            sx={{
              width: "100%",
              height: "240px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <CircularProgress />
          </Box>
        )}
      </Stack>
      {document.getElementById("ts_x1") &&
        createPortal(
          <>
            <Button
              variant="contained"
              disabled={
                globalAlgorithm === "" ||
                !isReady ||
                globalState !== "configured"
              }
              onClick={handleStart}
            >
              Start World
            </Button>
            <Button
              variant="outlined"
              onClick={handleReset}
              color="error"
              disabled={globalState !== "configured"}
            >
              Reset
            </Button>
            {globalState === "starting" && <CircularProgress size={20} />}
          </>,
          document.getElementById("ts_x1") as HTMLDivElement
        )}
    </>
  );
};

export default AlgorithmConfiguration;
