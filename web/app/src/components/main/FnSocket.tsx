
import { useEffect } from "react";
import { io } from "socket.io-client";

export default function FnSocket() {

  useEffect(() => {
    const socket = io("http://localhost:49699/rlab", {
      autoConnect: false,
    });
    socket.on("connect", () => {
      // connected
    });
    socket.on("disconnect", () => {
      // disconnected
    });
    socket.on("error", (error) => {
      console.error(error);
    });
    socket.onAny((event, ...args) => {
      console.debug(event, args);
    });
    socket.connect();

    return () => {
      socket.disconnect();
    };
  }, []);

  return null;
}
