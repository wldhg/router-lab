import Main from "@/components/main";
import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import Head from 'next/head';
import { useEffect, useState } from 'react';
import { RecoilRoot } from "recoil";

export default function Home() {
  const [themeName, setThemeName] = useState("dark");

  useEffect(() => {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      setThemeName("dark");
    } else {
      setThemeName("light");
    }

    const matchMediaDarkHandler = (event: { matches: any; }) => {
      const newColorScheme = event.matches ? "dark" : "light";
      setThemeName(newColorScheme);
    };

    const mediaQuery = window
      .matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", matchMediaDarkHandler);

    return () => {
      mediaQuery
        .removeEventListener("change", matchMediaDarkHandler);
    };
  }, []);

  const theme = createTheme({
    palette: {
      // @ts-ignore-next-line
      mode: themeName,
    },
    typography: {
      button: {
        textTransform: "none",
      },
      fontFamily: 'Pretendard,"Noto Sans KR","Noto Sans CJK KR","Noto Sans",sans-serif',
    },
  });

  return (
    <>
      <Head>
        <title>Router Lab Visualizer</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <RecoilRoot>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Main />
        </ThemeProvider>
      </RecoilRoot>
    </>
  )
}
