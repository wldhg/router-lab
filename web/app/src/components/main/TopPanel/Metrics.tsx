import {
  globalResubscriptionRequired_,
  globalSocket_,
  globalState_,
  worldStats_,
} from "@/recoil";
import Masonry from "@mui/lab/Masonry";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useRecoilState, useRecoilValue, useSetRecoilState } from "recoil";

const CardMaxWidth = 240;

interface MetricCardProps {
  title: string;
  value: string;
  unit?: string;
  sub?: string;
}

const MetricCard = (props: MetricCardProps) => {
  const { title, value, unit, sub } = props;

  return (
    <Card
      sx={{
        borderRadius: 2,
        maxWidth: CardMaxWidth,
      }}
    >
      <CardContent>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            fontWeight: 500,
          }}
          gutterBottom
        >
          {title}
        </Typography>
        <Typography variant="body1" sx={{ fontWeight: 500, fontSize: 24 }}>
          {value} <span style={{ opacity: 0.5 }}>{unit}</span>
        </Typography>
        {sub !== "" &&
          sub?.split("\n").map((subs, idx) => (
            <Typography
              key={`${title}-sub-${idx}`}
              sx={{
                // pre
                whiteSpace: "pre-wrap",
                fontFamily: "'Fira Mono', monospace",
                opacity: 0.5,
              }}
              gutterBottom={false}
            >
              {subs}
            </Typography>
          ))}
      </CardContent>
    </Card>
  );
};

MetricCard.defaultProps = {
  unit: "",
  sub: "",
};

const Metrics = () => {
  const globalSocket = useRecoilValue(globalSocket_);
  const [globalState, setGlobalState] = useRecoilState(globalState_);
  const setGlobalResubscriptionRequired = useSetRecoilState(
    globalResubscriptionRequired_
  );
  const worldStats = useRecoilValue(worldStats_);
  const [timer, setTimer] = useState<Date>(new Date());
  const [masonryColumns, setMasonryColumns] = useState(1);
  const [isWorldActive, setIsWorldActive] = useState(false);
  const [isWorldActivating, setIsWorldActivating] = useState(false);

  const handleStop = () => {
    if (globalSocket) {
      globalSocket.once("world_stop", (data) => {
        if (data["status"] === 200) {
          setGlobalState("stopped");
        } else {
          console.error(data["error"]);
          setGlobalState("running");
        }
      });
      globalSocket.emit("world_stop");
      setGlobalState("stopping");
    }
  };

  const handleReset = () => {
    setGlobalState("connected");
  };

  const handleStart = () => {
    setGlobalResubscriptionRequired(true);
    setGlobalState("configured");
  };

  useEffect(() => {
    if (globalState === "running") {
      const timer = setInterval(() => {
        setTimer(new Date());
      }, 1000);
      return () => {
        setTimer(new Date());
        clearInterval(timer);
      };
    }
    return () => {};
  }, [globalState]);

  const worldStartTime = new Date(worldStats.started_at * 1000);
  let seconds = timer.getSeconds() - worldStartTime.getSeconds();
  const minutes =
    (timer.getHours() - worldStartTime.getHours()) * 60 +
    (timer.getMinutes() - worldStartTime.getMinutes()) -
    (seconds < 0 ? 1 : 0);
  seconds = seconds < 0 ? seconds + 60 : seconds;

  useEffect(() => {
    const resizeHandler = () => {
      const newMasonryColumns = Math.max(
        1,
        Math.floor((window.innerWidth - 40) / CardMaxWidth)
      );
      console.log(newMasonryColumns);
      setMasonryColumns(newMasonryColumns);
    };

    resizeHandler();
    window.addEventListener("resize", resizeHandler);

    return () => {
      window.removeEventListener("resize", resizeHandler);
    };
  }, []);

  const handleActivity = () => {
    if (globalSocket) {
      setIsWorldActivating(true);
      globalSocket.once("world_start_activity", (data) => {
        setIsWorldActivating(false);
        if (data["status"] === 200) {
          setIsWorldActive(true);
        } else {
          console.error(data["error"]);
        }
      });
      globalSocket.emit("world_start_activity");
    }
  };

  return (
    <>
      <Box sx={{ width: "100%", height: "338px", overflowY: "auto" }}>
        <Masonry
          columns={masonryColumns}
          defaultColumns={4}
          sx={{ width: "100%" }}
        >
          <MetricCard
            title="Time"
            value={`${minutes}m ${seconds.toFixed(0).padStart(2, "0")}s`}
            unit=""
            sub="after the world is started"
          />
          <MetricCard
            title="1-hop Latency (Average)"
            value={`${(worldStats.world_1hop_latency * 1000).toFixed(2)}`}
            unit="ms"
          />
          <MetricCard
            title="1-hop Throughput (Average)"
            value={`${worldStats.world_1hop_throughput.toFixed(2)}`}
            unit="byte/s"
          />
          <MetricCard
            title="Total Sent"
            value={`${worldStats.world_stats[0]}`}
            unit="bytes"
            sub={`Total ${worldStats.world_stats[1]} packets`}
          />
          <MetricCard
            title="Total Received"
            value={`${worldStats.world_stats[2]}`}
            unit="bytes"
            sub={`Total ${worldStats.world_stats[3]} packets`}
          />
          <MetricCard
            title="Packet Loss Rate"
            value={`${(
              ((worldStats.world_stats[1] -
                worldStats.world_stats[3] -
                worldStats.transmissions.length) /
                worldStats.world_stats[1]) *
              100
            ).toFixed(2)}`}
            unit="%"
            sub={`${
              worldStats.world_stats[1] -
              worldStats.world_stats[3] -
              worldStats.transmissions.length
            } packets lost`}
          />
          {Object.keys(worldStats.custom_stats).map((stat_key, index) => {
            const title =
              stat_key
                .split("_")
                .map((stat_k) => stat_k[0].toUpperCase() + stat_k.slice(1))
                .join(" ") + " Average";
            return (
              <MetricCard
                key={`custom_stat_${index}`}
                title={title}
                value={`${worldStats.custom_stats[stat_key][0].toFixed(2)}`}
                sub={`Count: ${
                  worldStats.custom_stats[stat_key][3]
                }\nMin:   ${worldStats.custom_stats[stat_key][1].toFixed(
                  2
                )}\nMax:   ${worldStats.custom_stats[stat_key][2].toFixed(2)}`}
              />
            );
          })}
        </Masonry>
      </Box>
      {document.getElementById("ts_x1") &&
        createPortal(
          <>
            {globalState === "stopped" ? (
              <>
                <Button variant="outlined" onClick={handleReset} color="error">
                  Reset
                </Button>
                <Button onClick={handleStart} color="secondary">
                  Select New Implementation
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="outlined"
                  onClick={handleActivity}
                  color="primary"
                  disabled={
                    globalState !== "running" ||
                    isWorldActive ||
                    isWorldActivating
                  }
                >
                  {isWorldActive
                    ? "Lorem Activities Started"
                    : "Start Lorem Activities"}
                </Button>
                <Button
                  variant="contained"
                  onClick={handleStop}
                  color="error"
                  disabled={globalState !== "running"}
                >
                  Stop
                </Button>
                {globalState === "stopping" && <CircularProgress size={20} />}
                {globalState === "stopping" && (
                  <Typography variant="body2">
                    This takes 30 seconds at most.
                  </Typography>
                )}
                {isWorldActivating && <CircularProgress size={20} />}
                {isWorldActivating && (
                  <Typography variant="body2">
                    Starting network activities...
                  </Typography>
                )}
              </>
            )}
          </>,
          document.getElementById("ts_x1") as HTMLDivElement
        )}
    </>
  );
};

export default Metrics;
