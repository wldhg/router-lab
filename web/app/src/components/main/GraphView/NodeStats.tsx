import { globalSocket_, globalUse3DGraph_, worldStats_ } from "@/recoil";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import { Canvas } from "@react-three/fiber";
import { useEffect, useRef, useState } from "react";
import { useRecoilValue } from "recoil";
import * as THREE from "three";

interface Node3DProps {
  nodeDown: boolean;
}

const Node3D = (props: Node3DProps) => {
  const { nodeDown } = props;
  const theme = useTheme();
  const ref = useRef<THREE.Mesh>(null!);

  return (
    <mesh ref={ref} position={[0, 0, -8]}>
      <sphereBufferGeometry args={[6.5, 10, 10]} />
      <meshBasicMaterial
        color={nodeDown ? theme.palette.error.main : theme.palette.info.main}
        wireframe={true}
        wireframeLinewidth={1}
        wireframeLinejoin="round"
        wireframeLinecap="round"
      />
    </mesh>
  );
};

interface NodeStatsProps {
  nodeIP: string;
  closeAction: () => void;
}
const NodeStats = (props: NodeStatsProps) => {
  const { nodeIP, closeAction } = props;
  const globalSocket = useRecoilValue(globalSocket_);
  const globalUse3DGraph = useRecoilValue(globalUse3DGraph_);
  const [nodeStats, setNodeStats] = useState<any>({});
  const [nodeStatsLoading, setNodeStatsLoading] = useState(true);
  const worldStats = useRecoilValue(worldStats_);
  const theme = useTheme();

  useEffect(() => {
    if (globalSocket && nodeIP) {
      globalSocket.emit("node_stats", { ip: nodeIP });
      globalSocket.on("node_stats", (data: any) => {
        setNodeStats(data["data"]);
        setNodeStatsLoading(false);
      });

      const interval = setInterval(() => {
        globalSocket.emit("node_stats", { ip: nodeIP });
      }, 1000);

      return () => {
        globalSocket.off("node_stats");
        clearInterval(interval);
      };
    }
  }, [globalSocket, nodeIP]);

  return (
    <Card
      sx={{
        position: "fixed",
        bottom: 0,
        right: 0,
        mb: 10,
        mr: 2,
        pb: 2,
        borderRadius: 2,
      }}
    >
      <CardContent>
        {globalUse3DGraph && worldStats.nodes_updown ? (
          <Canvas style={{ width: 50, height: 50, marginLeft: -8 }}>
            <Node3D nodeDown={worldStats.nodes_updown[nodeIP]} />
          </Canvas>
        ) : (
          <svg width="25" height="25">
            <circle
              cx="12.5"
              cy="12.5"
              r="10"
              fill={
                worldStats.nodes_updown[nodeIP]
                  ? theme.palette.error.main
                  : theme.palette.primary.main
              }
              strokeWidth={4}
              stroke={theme.palette.warning.main}
            />
          </svg>
        )}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mt: 1,
            fontWeight: 500,
          }}
          gutterBottom
        >
          Node Metrics
        </Typography>
        <Typography variant="h5" gutterBottom>
          {nodeIP}
        </Typography>
        {nodeStatsLoading ? (
          <Box sx={{ display: "flex" }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Typography
              variant="body1"
              sx={{
                whiteSpace: "pre-wrap",
                fontFamily: "'Fira Mono', monospace",
              }}
            >
              Sent: {nodeStats?.sent_pkts} pkts
            </Typography>
            <Typography
              variant="body1"
              sx={{
                whiteSpace: "pre-wrap",
                fontFamily: "'Fira Mono', monospace",
              }}
            >
              Sent Bytes: {nodeStats?.sent_bytes} bytes
            </Typography>
            <Typography
              variant="body1"
              sx={{
                whiteSpace: "pre-wrap",
                fontFamily: "'Fira Mono', monospace",
              }}
            >
              Received: {nodeStats?.recv_pkts} pkts
            </Typography>
            <Typography
              variant="body1"
              sx={{
                whiteSpace: "pre-wrap",
                fontFamily: "'Fira Mono', monospace",
              }}
            >
              Received Bytes: {nodeStats?.recv_bytes} bytes
            </Typography>
          </>
        )}
        <br />
        <Button
          onClick={closeAction}
          style={{
            float: "right",
          }}
        >
          Close
        </Button>
      </CardContent>
    </Card>
  );
};

export default NodeStats;
