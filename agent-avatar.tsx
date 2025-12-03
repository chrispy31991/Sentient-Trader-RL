"use client"

import { Canvas } from "@react-three/fiber"
import { OrbitControls, Sphere, MeshDistortMaterial } from "@react-three/drei"
import { useFrame } from "@react-three/fiber"
import { useRef } from "react"
import type * as THREE from "three"

function ThinkingSphere({ isThinking }: { isThinking: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (meshRef.current && isThinking) {
      meshRef.current.rotation.x = state.clock.getElapsedTime() * 0.3
      meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.5
    }
  })

  return (
    <Sphere ref={meshRef} args={[1, 64, 64]} scale={isThinking ? 1.2 : 1}>
      <MeshDistortMaterial
        color={isThinking ? "#a855f7" : "#3b82f6"}
        attach="material"
        distort={isThinking ? 0.4 : 0.2}
        speed={isThinking ? 2 : 1}
        roughness={0.2}
        metalness={0.8}
      />
    </Sphere>
  )
}

export function AgentAvatar({ isThinking }: { isThinking: boolean }) {
  return (
    <div className="w-full h-full bg-gradient-to-br from-purple-950/20 to-blue-950/20 rounded-lg">
      <Canvas camera={{ position: [0, 0, 3], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#a855f7" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#3b82f6" />
        <ThinkingSphere isThinking={isThinking} />
        <OrbitControls enableZoom={false} enablePan={false} />
      </Canvas>
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 glass px-3 py-1 rounded-full border border-purple-500/30">
        <span className="text-xs text-purple-300">{isThinking ? "Thinking..." : "Idle"}</span>
      </div>
    </div>
  )
}
