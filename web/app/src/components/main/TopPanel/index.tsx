import {
  GlobalState,
  globalAlgorithm_,
  globalState_,
  globalTheme_,
  globalTopPanelPinned_,
} from "@/recoil";
import LightModeIcon from "@mui/icons-material/LightMode";
import PushPinIcon from "@mui/icons-material/PushPin";
import PushPinOutlinedIcon from "@mui/icons-material/PushPinOutlined";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { alpha } from "@mui/material/styles";
import { useEffect, useState } from "react";
import { useRecoilState, useRecoilValue, useSetRecoilState } from "recoil";
import AlgorithmConfiguration from "./AlgorithmConfiguration";
import Metrics from "./Metrics";
import OSSNoticeContent from "./OSSNoticeContent";
import ParameterConfigurations from "./ParameterConfigurations";

import pkg from "../../../../package.json";

const stepsInt: {
  [key in GlobalState]: number;
} = {
  connecting: -1,
  connected: 0,
  configuring: 0,
  configured: 1,
  starting: 1,
  running: 1,
  stopping: 1,
  stopped: 2,
};

const stepsStr: {
  [key: number]: string;
} = {
  0: "Configuration",
  1: "Run Experiment",
  2: "Done",
};

const TopPanel = () => {
  const [panelExpanded, setPanelExtended] = useState(false);
  const [ossPanelExpanded, setOSSPanelExpanded] = useState(false);
  const [versionPanelExpanded, setVersionPanelExpanded] = useState(false);
  const [globalTheme, setGlobalTheme] = useRecoilState(globalTheme_);
  const setGlobalTopPanelPinned = useSetRecoilState(globalTopPanelPinned_);
  const globalState = useRecoilValue(globalState_);
  const globalAlgorithm = useRecoilValue(globalAlgorithm_);

  const toggleTheme = () => {
    const newTheme = globalTheme === "dark" ? "light" : "dark";
    setGlobalTheme(newTheme);
  };

  const togglePanel = () => {
    setPanelExtended(!panelExpanded);
  };

  const toggleOSSPanel = () => {
    setOSSPanelExpanded(!ossPanelExpanded);
  };

  const toggleVersionPanel = () => {
    setVersionPanelExpanded(!versionPanelExpanded);
  };

  const shouldPanelExpanded =
    globalState === "connected" ||
    globalState === "configuring" ||
    globalState === "configured" ||
    globalState === "starting" ||
    panelExpanded;

  useEffect(() => {
    setGlobalTopPanelPinned(shouldPanelExpanded);
  }, [shouldPanelExpanded, setGlobalTopPanelPinned]);

  let boxContent = (
    <Box
      sx={{
        width: "100%",
        height: "340px",
        borderRadius: 4,
        backgroundColor: (theme) => alpha(theme.palette.background.paper, 0.5),
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      No more detail available for now.
    </Box>
  );
  let algoOpacity = 0;
  if (globalState === "connected" || globalState === "configuring") {
    boxContent = <ParameterConfigurations />;
  } else if (globalState === "configured" || globalState === "starting") {
    boxContent = <AlgorithmConfiguration />;
  } else if (
    globalState === "running" ||
    globalState === "stopping" ||
    globalState === "stopped"
  ) {
    boxContent = <Metrics />;
    algoOpacity = 1;
  }

  return (
    <>
      <Paper
        elevation={3}
        sx={{
          marginTop: -4,
          paddingTop: 4,
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: shouldPanelExpanded ? "500px" : "90px",
          transition: "height 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
          zIndex: (theme) => theme.zIndex.drawer + 2,
          borderRadius: 4,
          overflow: "hidden",
          ":hover": {
            height: "500px",
            " > #tb_x2": {
              opacity: 1,
              mt: 1,
              height: "400px",
              py: 1,
            },
          },
          display: "block",
          " > #tb_x2": {
            opacity: shouldPanelExpanded ? 1 : 0,
            mt: shouldPanelExpanded ? 1 : 0,
            height: shouldPanelExpanded ? "400px" : "0px",
            py: shouldPanelExpanded ? 1 : 0,
          },
        }}
      >
        <Stack
          sx={{ flexDirection: "row", px: 3, py: 1, alignItems: "center" }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700, mr: 6 }}>
            Router Lab
          </Typography>
          <Stack
            sx={{
              flexGrow: 1,
              display: "flex",
              alignItems: "center",
              flexDirection: "row",
              mr: 6,
              gap: 4,
            }}
          >
            <Stepper
              activeStep={stepsInt[globalState]}
              sx={{ p: 0, flexGrow: 1, maxWidth: "500px" }}
            >
              {Object.keys(stepsStr).map((key) => {
                const numberKey = Number.parseInt(key);
                const stepKey = key.toString();
                const label = stepsStr[numberKey];
                return (
                  <Step key={stepKey}>
                    <StepLabel>{label}</StepLabel>
                  </Step>
                );
              })}
            </Stepper>
            <Stack
              id="ts_x1"
              sx={{
                gap: 2,
                flexDirection: "row",
                alignItems: "center",
                flexGrow: 1,
              }}
            ></Stack>
          </Stack>
          <Typography
            variant="body1"
            sx={{
              mr: 2,
              fontFamily: "'Fira Mono', monospace",
              opacity: algoOpacity,
              transition: "opacity .5s",
            }}
          >
            {globalAlgorithm}
          </Typography>
          <Tooltip title="Toggle Theme" sx={{ mr: 1 }}>
            <IconButton onClick={toggleTheme}>
              {globalTheme === "dark" ? <LightModeIcon /> : <LightModeIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title={panelExpanded ? "Unpin" : "Pin"}>
            <IconButton onClick={togglePanel}>
              {panelExpanded ? <PushPinIcon /> : <PushPinOutlinedIcon />}
            </IconButton>
          </Tooltip>
        </Stack>
        <Box
          id="tb_x2"
          sx={{
            width: "100%",
            px: 3,
            overflow: "hidden",
            position: "relative",
            transition: [
              "opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
              "margin-top 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
              "height 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
              "padding 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
            ].join(", "),
          }}
        >
          {boxContent}
          <Stack
            sx={{
              flexDirection: "row",
              gap: 1,
              position: "absolute",
              right: 0,
              bottom: 0,
              mr: 3,
              mb: 1,
            }}
          >
            <Button onClick={toggleOSSPanel}>OSS Notice</Button>
            <Button onClick={toggleVersionPanel}>v{pkg.version}</Button>
          </Stack>
        </Box>
      </Paper>
      <Dialog open={ossPanelExpanded} onClose={toggleOSSPanel}>
        <DialogTitle>
          Open Source Software
          <Typography variant="body2" gutterBottom component="div">
            Router Lab includes software developed by the following open source
            projects.
            <br />
            Thanks to all the contributors.
          </Typography>
          <Typography
            variant="body2"
            gutterBottom
            component="div"
            sx={{ opacity: 0.5 }}
          >
            The content is automatically generated from the distributed module
            package.
          </Typography>
        </DialogTitle>
        <DialogContent>
          <OSSNoticeContent />
        </DialogContent>
      </Dialog>
      <Dialog open={versionPanelExpanded} onClose={toggleVersionPanel}>
        <DialogTitle>Router Lab</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Frontend Version {pkg.version}
            <br />
            Author: wldhg{" "}
            <code
              style={{
                fontFamily: "'Fira Mono', monospace",
              }}
            >
              &lt;{atob("d2xkaGdAYXJ1LmJ5")}&gt;
            </code>
          </Typography>
          <Typography variant="body1" gutterBottom>
            This program has been created for educational purposes. Unlike real
            world networks, many parts have been omitted or replaced with
            simplified alternatives.
          </Typography>
          <Typography
            variant="body2"
            gutterBottom
            component="div"
            sx={{ mt: 2 }}
          >
            &copy; 2023 POSTECH Artificial Intelligence of Things Laboratory,
            All Rights Reserved.
          </Typography>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default TopPanel;
