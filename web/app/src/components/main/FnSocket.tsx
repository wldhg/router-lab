import { globalSocket_, globalState_ } from "@/recoil";
import MuiAlert, { AlertProps } from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";
import { forwardRef, useEffect, useRef, useState } from "react";
import { useRecoilState, useSetRecoilState } from "recoil";
import { Socket, io } from "socket.io-client";

const Alert = forwardRef<HTMLDivElement, AlertProps>(function Alert(
  props,
  ref
) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

export default function FnSocket() {
  const socketRef = useRef<Socket | null>(null);
  const setGlobalSocket = useSetRecoilState(globalSocket_);
  const [globalState, setGlobalState] = useRecoilState(globalState_);
  const [open, setOpen] = useState(false);
  const [snackbarContent, setSnackbarContent] = useState("");

  useEffect(() => {
    if (socketRef.current === null) {
      socketRef.current = io("http://localhost:7000/rlab", {
        autoConnect: false,
      });
      setGlobalSocket(socketRef.current);
    }
    socketRef.current.on("connect", () => {
      setGlobalState("connected");
    });
    socketRef.current.on("disconnect", () => {
      setGlobalState("connecting");
    });

    socketRef.current.on("error", (error) => {
      console.error(error);
      setSnackbarContent(error);
      setOpen(true);
    });
    socketRef.current.onAny((event, ...args) => {
      console.debug(event, args);
      if (args.length > 0) {
        const argo = args[0] as any;
        if (argo["status"] === 500) {
          console.error(argo);
          setSnackbarContent(argo["error"]);
          setOpen(true);
        }
      }
    });
    if (!socketRef.current.connected) {
      socketRef.current.connect();
    }

    return () => {
      if (socketRef.current === null) {
        setGlobalSocket(null);
        return;
      }
      socketRef.current.off("connect");
      socketRef.current.off("disconnect");
      socketRef.current.off("error");
      socketRef.current.offAny();
    };
  }, [setGlobalState, setGlobalSocket]);

  const snackbarClose = () => {
    setOpen(false);
  };

  return (
    <Snackbar
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
      open={open}
      autoHideDuration={6000}
      onClose={snackbarClose}
    >
      <Alert onClose={snackbarClose} severity="error" sx={{ width: "100%" }}>
        {snackbarContent}
      </Alert>
    </Snackbar>
  );
}
