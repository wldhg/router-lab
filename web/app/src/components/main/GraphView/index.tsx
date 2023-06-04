import {
  globalTopPanelPinned_,
  globalUse3DGraph_,
  worldInformation_,
  worldStats_,
} from "@/recoil";
import Box from "@mui/material/Box";
import { alpha, useTheme } from "@mui/material/styles";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import * as THREE from "three";
import NodeStats from "./NodeStats";

type Nodes = {
  id: string;
  name: string;
  color: string;
}[];

type Links = {
  source: string;
  target: string;
  color: string;
}[];

type Data = {
  nodes: Nodes;
  links: Links;
};

const DynamicGraphView3D = dynamic(
  () => import("react-force-graph").then((mod) => mod.ForceGraph3D),
  {
    ssr: false,
  }
);

const DynamicGraphView2D = dynamic(
  () => import("react-force-graph").then((mod) => mod.ForceGraph2D),
  {
    ssr: false,
  }
);

const GraphView = () => {
  const worldInformation = useRecoilValue(worldInformation_);
  const worldStats = useRecoilValue(worldStats_);
  const [data, setData] = useState<Data>({
    nodes: [],
    links: [],
  });
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const globalTopPanelPinned = useRecoilValue(globalTopPanelPinned_);
  const globalUse3DGraph = useRecoilValue(globalUse3DGraph_);
  const [windowWidth, setWindowWidth] = useState(0);
  const [windowHeight, setWindowHeight] = useState(0);
  const theme = useTheme();

  useEffect(() => {
    const resizeHandler = () => {
      setWindowWidth(window.innerWidth);
      setWindowHeight(
        window.innerHeight - 52 - (globalTopPanelPinned ? 460 : 0)
      );
    };

    resizeHandler();
    window.addEventListener("resize", resizeHandler);

    return () => {
      window.removeEventListener("resize", resizeHandler);
    };
  }, [globalTopPanelPinned]);

  useEffect(() => {
    setSelectedNode(null);
  }, [worldInformation]);

  useEffect(() => {
    const nodes: Nodes = [];
    const links: Links = [];

    for (let i = 0; i < worldInformation.node_ips.length; i++) {
      nodes.push({
        id: worldInformation.node_ips[i],
        name: worldInformation.node_ips[i],
        color: theme.palette.primary.main,
      });

      for (let j = 0; j < worldInformation.node_ips.length; j++) {
        if (i === j) {
          continue;
        }
        if (worldInformation.topo[i][j]) {
          links.push({
            source: worldInformation.node_ips[i],
            target: worldInformation.node_ips[j],
            color: theme.palette.text.primary,
          });
        }
      }
    }

    setData({
      nodes,
      links,
    });
  }, [worldInformation, theme, globalUse3DGraph]);

  const drawNode3D = useCallback(
    (node: any) => {
      if (!worldStats.nodes_updown) {
        return null;
      }
      const node_ip = node.id as string;
      if (worldStats.nodes_updown[node_ip]) {
        const material = new THREE.MeshBasicMaterial({
          color: theme.palette.error.main,
          opacity: 0.5,
          transparent: true,
          fog: true,
          wireframe: selectedNode === node.id,
          wireframeLinewidth: 1,
          wireframeLinejoin: "round",
          wireframeLinecap: "round",
        });
        const geometry = new THREE.SphereGeometry(
          selectedNode === node.id ? 6.5 : 4,
          10,
          10
        );
        const threeObj = new THREE.Mesh(geometry, material);
        threeObj.renderOrder = 1;
        return threeObj;
      }
      if (selectedNode === node.id) {
        const material = new THREE.MeshBasicMaterial({
          color: theme.palette.primary.main,
          opacity: 0.5,
          transparent: true,
          fog: true,
          wireframe: true,
          wireframeLinewidth: 1,
          wireframeLinejoin: "round",
          wireframeLinecap: "round",
        });
        const geometry = new THREE.SphereGeometry(6.5, 10, 10);
        const threeObj = new THREE.Mesh(geometry, material);
        threeObj.renderOrder = 1;
        return threeObj;
      }
      return null;
    },
    [worldStats, theme, selectedNode]
  );

  const drawTransmission3D = useCallback(
    (link: any) => {
      if (!worldStats.transmissions) {
        return null;
      }
      for (let i = 0; i < worldStats.transmissions.length; i++) {
        const transmission = worldStats.transmissions[i];
        if (
          transmission[0] === link.source.id &&
          transmission[1] === link.target.id
        ) {
          const percentage = (transmission[3] as number) / 100;
          // Create a cylinder object that starts from source and ends at target
          const material = new THREE.MeshBasicMaterial({
            color: worldStats.nodes_updown[link.target.id]
              ? theme.palette.error.main
              : theme.palette.success.main,
            opacity: 0.5,
            transparent: true,
            fog: true,
          });
          const subtracted = new THREE.Vector3(
            link.target.x - link.source.x,
            link.target.y - link.source.y,
            link.target.z - link.source.z
          );
          const direction = subtracted.normalize();
          const height =
            Math.sqrt(
              Math.pow(link.target.x - link.source.x, 2) +
                Math.pow(link.target.y - link.source.y, 2) +
                Math.pow(link.target.z - link.source.z, 2)
            ) * percentage;
          const geometry = new THREE.CylinderGeometry(1, 1, height, 10, 1);
          const threeObj = new THREE.Mesh(geometry, material);
          threeObj.position.set(
            link.source.x + direction.x * height * 0.5,
            link.source.y + direction.y * height * 0.5,
            link.source.z + direction.z * height * 0.5
          );
          threeObj.lookAt(link.target.x, link.target.y, link.target.z);
          threeObj.rotateX(Math.PI / 2);
          threeObj.renderOrder = 1;
          return threeObj;
        }
      }
      return null;
    },
    [worldStats, theme]
  );

  const drawNode2D = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      if (!worldStats.nodes_updown) {
        return null;
      }
      const node_ip = node.id as string;
      let node_color = theme.palette.primary.main;
      if (worldStats.nodes_updown[node_ip]) {
        node_color = theme.palette.error.main;
      }
      ctx.beginPath();
      ctx.arc(
        node.x,
        node.y,
        selectedNode === node.id ? 6 : 4,
        0,
        2 * Math.PI,
        false
      );
      ctx.fillStyle = node_color;
      ctx.fill();
      ctx.lineWidth = selectedNode === node.id ? 2 : 1;
      ctx.strokeStyle =
        selectedNode === node.id ? theme.palette.warning.main : node_color;
      ctx.stroke();
    },
    [worldStats, theme, selectedNode]
  );

  const drawTransmission2D = useCallback(
    (link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      if (!worldStats.transmissions) {
        return null;
      }
      for (let i = 0; i < worldStats.transmissions.length; i++) {
        const transmission = worldStats.transmissions[i];
        if (
          transmission[0] === link.source.id &&
          transmission[1] === link.target.id
        ) {
          const percentage = (transmission[3] as number) / 100;
          ctx.beginPath();
          ctx.moveTo(link.source.x, link.source.y);
          ctx.lineTo(
            link.source.x + (link.target.x - link.source.x) * percentage,
            link.source.y + (link.target.y - link.source.y) * percentage
          );
          ctx.lineWidth = 1;
          if (worldStats.nodes_updown[link.target.id]) {
            ctx.strokeStyle = theme.palette.error.main;
          } else {
            ctx.strokeStyle = theme.palette.success.main;
          }
          ctx.stroke();
          return;
        }
      }
      ctx.beginPath();
      ctx.moveTo(link.source.x, link.source.y);
      ctx.lineTo(link.target.x, link.target.y);
      ctx.lineWidth = 0.3;
      ctx.strokeStyle = alpha(theme.palette.text.primary, 0.3);
      ctx.stroke();
    },
    [worldStats, theme]
  );

  const handleNodeClick = (node: any) => {
    setSelectedNode(node.id);
  };

  const handleBackgroundClick = () => {
    setSelectedNode(null);
  };

  return (
    <>
      <Box sx={{ overflow: "hidden", mt: globalTopPanelPinned ? "460px" : 0 }}>
        {worldInformation.id !== "" && globalUse3DGraph ? (
          <DynamicGraphView3D
            graphData={data}
            // @ts-ignore
            nodeThreeObject={drawNode3D}
            // @ts-ignore
            linkThreeObject={drawTransmission3D}
            linkThreeObjectExtend={true}
            width={windowWidth}
            height={windowHeight}
            backgroundColor={theme.palette.background.paper}
            nodeColor="color"
            linkColor="color"
            onNodeDragEnd={(node) => {
              node.fx = node.x;
              node.fy = node.y;
              node.fz = node.z;
            }}
            onNodeClick={handleNodeClick}
            onBackgroundClick={handleBackgroundClick}
          />
        ) : (
          <DynamicGraphView2D
            graphData={data}
            nodeCanvasObject={drawNode2D}
            linkCanvasObject={drawTransmission2D}
            width={windowWidth}
            height={windowHeight}
            backgroundColor={theme.palette.background.paper}
            linkColor="color"
            onNodeDragEnd={(node) => {
              node.fx = node.x;
              node.fy = node.y;
              node.fz = node.z;
            }}
            onNodeClick={handleNodeClick}
            onBackgroundClick={handleBackgroundClick}
          />
        )}
      </Box>
      {selectedNode !== null ? (
        <NodeStats nodeIP={selectedNode} closeAction={handleBackgroundClick} />
      ) : null}
    </>
  );
};

export default GraphView;
