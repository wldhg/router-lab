import { globalTheme_, globalUse3DGraph_ } from "@/recoil";
import ThreeDRotationIcon from "@mui/icons-material/ThreeDRotation";
import Backdrop from "@mui/material/Backdrop";
import Box from "@mui/material/Box";
import CssBaseline from "@mui/material/CssBaseline";
import ToggleButton from "@mui/material/ToggleButton";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { ThemeProvider, alpha, createTheme } from "@mui/material/styles";
import { useEffect, useState } from "react";
import { useRecoilState } from "recoil";
import BackdropGuide from "./BackdropGuide";
import FnSocket from "./FnSocket";
import GraphView from "./GraphView";
import Loggie from "./Loggie";
import TopPanel from "./TopPanel";

const getSystemTheme = () => {
  if (typeof window === "undefined") {
    return "dark";
  }
  return window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
};

export default function Frame() {
  const [guideVisibility, setGuideVisibility] = useState(false);
  const [themeInitialized, setThemeInitialized] = useState(false);
  const [themeName, setThemeName] = useRecoilState(globalTheme_);
  const [globalUse3DGraph, setGlobalUse3DGraph] =
    useRecoilState(globalUse3DGraph_);

  useEffect(() => {
    const resizeHandler = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      if (width < 970 || height < 600) {
        setGuideVisibility(true);
      } else {
        setGuideVisibility(false);
      }
    };

    resizeHandler();
    window.addEventListener("resize", resizeHandler);

    return () => {
      window.removeEventListener("resize", resizeHandler);
    };
  }, []);

  useEffect(() => {
    const matchMediaDarkHandler = (event: { matches: any }) => {
      const isAuto = localStorage.getItem("rlab-theme") === "auto";
      if (!isAuto) {
        return;
      }
      const newColorScheme = event.matches ? "dark" : "light";
      setThemeName(newColorScheme);
    };

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", matchMediaDarkHandler);

    return () => {
      mediaQuery.removeEventListener("change", matchMediaDarkHandler);
    };
  }, [setThemeName]);

  useEffect(() => {
    let localTheme = localStorage.getItem("rlab-theme");
    if (localTheme === null || getSystemTheme() === localTheme) {
      localStorage.setItem("rlab-theme", "auto");
      localTheme = getSystemTheme();
    } else if (localTheme === "auto") {
      localTheme = getSystemTheme();
    }

    if (localTheme === "dark") {
      setThemeName("dark");
    } else {
      setThemeName("light");
    }

    setThemeInitialized(true);
  }, [setThemeName, setThemeInitialized]);

  useEffect(() => {
    if (themeInitialized) {
      if (getSystemTheme() === themeName) {
        localStorage.setItem("rlab-theme", "auto");
      } else {
        localStorage.setItem("rlab-theme", themeName);
      }
    }
  }, [themeName, themeInitialized]);

  const theme = createTheme({
    palette: {
      mode: themeName,
    },
    typography: {
      button: {
        textTransform: "none",
      },
      fontFamily:
        'Pretendard,"Noto Sans KR","Noto Sans CJK KR","Noto Sans",sans-serif',
    },
  });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <FnSocket />
      <Box
        id="rlab-main"
        className={themeName === "dark" ? "dark" : "light"}
        sx={{
          width: "100%",
          height: "100%",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {guideVisibility ? (
          <Backdrop
            open={true}
            sx={{
              zIndex: (theme) => theme.zIndex.drawer + 50,
              backgroundColor: (theme) =>
                alpha(theme.palette.background.default, 0.5),
            }}
          >
            <Typography variant="h5">
              Please resize your window to 970×600 or larger.
            </Typography>
          </Backdrop>
        ) : (
          <>
            <TopPanel />
            <Box
              sx={{
                width: "100%",
                height: "100%",
                pt: 6.5,
              }}
            >
              <GraphView />
              <BackdropGuide />
            </Box>
            <Loggie />
            <Box
              sx={{
                position: "fixed",
                bottom: 0,
                mb: 2,
                mr: 2,
                right: 0,
              }}
            >
              <Tooltip title={globalUse3DGraph ? "View in 2D" : "View in 3D"}>
                <ToggleButton
                  value="check"
                  selected={globalUse3DGraph}
                  onChange={() => setGlobalUse3DGraph(!globalUse3DGraph)}
                >
                  <ThreeDRotationIcon />
                </ToggleButton>
              </Tooltip>
            </Box>
          </>
        )}
      </Box>
    </ThemeProvider>
  );
}
