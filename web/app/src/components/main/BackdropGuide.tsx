import { globalState_, globalTopPanelPinned_ } from "@/recoil";
import Backdrop from "@mui/material/Backdrop";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { alpha } from "@mui/material/styles";
import { useRecoilValue } from "recoil";

const BackdropGuide = () => {
  const globalState = useRecoilValue(globalState_);
  const globalTopPanelPinned = useRecoilValue(globalTopPanelPinned_);

  let visibility = false;
  let content = <span></span>;

  if (globalState === "connecting") {
    visibility = true;
    content = (
      <Stack sx={{ flexDirection: "column", alignItems: "center", gap: 4 }}>
        <Typography variant="h5">Connecting...</Typography>
        <CircularProgress />
      </Stack>
    );
  } else if (globalState === "connected") {
    visibility = true;
    content = (
      <Stack sx={{ flexDirection: "column", alignItems: "center", gap: 4 }}>
        <Typography variant="h5">
          Confirm the world configuration parameters.
        </Typography>
      </Stack>
    );
  } else if (globalState === "configuring") {
    visibility = true;
    content = (
      <Stack sx={{ flexDirection: "column", alignItems: "center", gap: 4 }}>
        <Typography variant="h5">Configuring...</Typography>
        <Typography
          variant="body2"
          sx={{
            maxWidth: "50%",
            textAlign: "center",
          }}
        >
          If you combine a moderate number of nodes with a high sparsity
          condition, be prepared for an extremely time-consuming configuration
          process. In such instances, refreshing the page and attempting
          different conditions may be a better option.
        </Typography>
        <CircularProgress />
      </Stack>
    );
  }

  return (
    <Backdrop
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        mt: globalTopPanelPinned ? "460px" : 6.5,
        backgroundColor: (theme) =>
          alpha(theme.palette.background.default, 0.5),
      }}
      open={visibility}
      transitionDuration={500}
    >
      {content}
    </Backdrop>
  );
};

export default BackdropGuide;
