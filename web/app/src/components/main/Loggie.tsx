import { globalState_, worldLogsPointer_, worldLogs_ } from "@/recoil";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import { alpha, useTheme } from "@mui/material/styles";
import { useEffect, useRef, useState } from "react";
import { ListChildComponentProps, VariableSizeList } from "react-window";
import { useRecoilValue } from "recoil";

const loggieHeight = 340;
const upperPadCount = 8;
const colorMap = {
  INFO: "text.primary",
  WARNING: "#ff9800",
  ERROR: "#f44336",
  DEBUG: "#4caf50",
};

type ColorMapKey = keyof typeof colorMap;

const LoggieLine = (props: ListChildComponentProps) => {
  const { index, style } = props;

  const worldLogs = useRecoilValue(worldLogs_);
  const worldLogsPointer = useRecoilValue(worldLogsPointer_);

  if (index < upperPadCount) {
    return <span key={`log_${index}`}> </span>;
  }

  let logType: ColorMapKey = "INFO";
  if (worldLogs[index - upperPadCount].indexOf("| ERROR    |") !== -1) {
    logType = "ERROR";
  } else if (worldLogs[index - upperPadCount].indexOf("| WARNING  |") !== -1) {
    logType = "WARNING";
  } else if (worldLogs[index - upperPadCount].indexOf("| DEBUG    |") !== -1) {
    logType = "DEBUG";
  }

  return (
    <Stack
      key={`log_${index}`}
      sx={{
        width: "740px",
        flexDirection: "row",
        gap: 1,
        paddingTop: "3px",
        paddingBottom: "3px",
        "&:hover": {
          backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.1),
        },
        ...style,
      }}
    >
      <Box
        sx={{
          width: "50px",
          fontSize: "0.875rem",
          color: "primary.main",
          lineHeight: "16px",
          pl: 1.5,
        }}
      >
        <code
          style={{
            fontFamily: "'Fira Mono', monospace",
          }}
        >
          {worldLogsPointer - worldLogs.length + index - upperPadCount}
        </code>
      </Box>
      <pre
        style={{
          margin: 0,
          fontSize: "0.875rem",
          width: "652px",
          wordBreak: "break-all",
          overflow: "hidden",
          lineHeight: "16px",
          whiteSpace: "pre-wrap",
          color: colorMap[logType] || "text.primary",
        }}
      >
        <code
          style={{
            fontFamily: "'Fira Mono', monospace",
          }}
        >
          {worldLogs[index - upperPadCount]}
        </code>
      </pre>
    </Stack>
  );
};

const Loggie = () => {
  const [isLoggieOpened, setIsLoggieOpened] = useState(true);
  const worldLogs = useRecoilValue(worldLogs_);
  const globalState = useRecoilValue(globalState_);
  const theme = useTheme();
  const isHovering = useRef(false);
  const listRef = useRef<VariableSizeList>(null);

  const toggleLoggie = () => {
    setIsLoggieOpened(!isLoggieOpened);
  };

  const getItemHeight = (index: number) => {
    if (index < upperPadCount) {
      return 24;
    }
    let height = 0;
    worldLogs[index - upperPadCount].split("\n").forEach((line) => {
      height += Math.max(Math.ceil(line.length / 93), 1);
    });
    return height * 16 + 6;
  };

  const isLoggieVisible = ![
    "connected",
    "connecting",
    "configuring",
    "configured",
  ].includes(globalState);

  useEffect(() => {
    if (listRef.current) {
      listRef.current?.resetAfterIndex(upperPadCount);
      if (!isHovering.current) {
        listRef.current?.scrollToItem(worldLogs.length + upperPadCount);
      }
    }
  }, [worldLogs]);

  return (
    <>
      <Button
        sx={{
          position: "absolute",
          left: 0,
          bottom: isLoggieOpened ? loggieHeight : -24,
          ml: 1,
          mb: 4,
          opacity: isLoggieVisible ? 0.5 : 0,
          transition: "opacity 0.3s, bottom 0.5s cubic-bezier(.17,.67,.05,.95)",
          ":hover": {
            opacity: isLoggieVisible ? 1 : 0,
          },
        }}
        onClick={toggleLoggie}
      >
        {isLoggieOpened ? "Hide Logs" : "Show Logs"}
      </Button>
      <Box
        sx={{
          position: "absolute",
          left: 0,
          bottom: isLoggieOpened ? 0 : -loggieHeight - 30,
          ml: 1,
          mb: 3,
          width: "740px",
          height: loggieHeight,
          opacity: isLoggieVisible ? 1 : 0,
          transition: "opacity 0.3s, bottom 0.5s cubic-bezier(.17,.67,.05,.95)",
          borderRadius: 2,
          backgroundColor: (theme) =>
            alpha(theme.palette.background.paper, 0.5),
          overflow: "hidden",
        }}
        onMouseEnter={() => {
          isHovering.current = true;
        }}
        onMouseLeave={() => {
          isHovering.current = false;
        }}
      >
        <VariableSizeList
          ref={listRef}
          height={loggieHeight}
          width={740}
          itemSize={getItemHeight}
          itemCount={worldLogs.length + upperPadCount}
          overscanCount={10}
          onItemsRendered={(props) => {
            if (!isHovering.current) {
              listRef.current?.scrollToItem(worldLogs.length + upperPadCount);
            }
          }}
        >
          {LoggieLine}
        </VariableSizeList>
        <div
          style={{
            width: "100%",
            height: "50px",
            background: `linear-gradient(0deg, ${alpha(
              theme.palette.background.paper,
              0
            )} 0%, ${alpha(theme.palette.background.paper, 1)} 100%)`,
            position: "absolute",
            top: 0,
            left: 0,
          }}
        />
      </Box>
    </>
  );
};

export default Loggie;
