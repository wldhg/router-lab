import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import RotateLeftIcon from '@mui/icons-material/RotateLeft';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import FnSocket from "./FnSocket";

export default function Frame() {
  return (
    <>
      <FnSocket />
      <Stack>
        <Paper elevation={3} sx={{ marginTop: -4, paddingTop: 4, }}>
          <Stack sx={{ flexDirection: "row", px: 3, py: 1, alignItems: "center" }}>
            <Typography variant="h6" sx={{ fontWeight: 700, mr: 4 }}>Router Lab Visualizer</Typography>
            <Stack sx={{ flexDirection: "row", gap: 1 }}>
              <Button color="error" variant="outlined" startIcon={<RotateLeftIcon />}>
                Reset
              </Button>
              <Button startIcon={<PlayArrowIcon />}>
                Start
              </Button>
            </Stack>
          </Stack>
        </Paper>
      </Stack>
    </>
  );
};
