"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Eye, 
  Camera, 
  Play, 
  Square, 
  RotateCcw, 
  Zap, 
  Settings, 
  Monitor,
  Video,
  Image as ImageIcon,
  Maximize,
  Move3D,
  Layers
} from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { renderImage, render360Video, getRenderStatus } from "@/lib/api";
import { toast } from "@/components/ui/toaster";
import { cn } from "@/lib/utils";

const qualityOptions = [
  { id: "low", name: "Draft", description: "Fast preview rendering", resolution: "512x512" },
  { id: "medium", name: "Standard", description: "Balanced quality", resolution: "1024x1024" },
  { id: "high", name: "Premium", description: "High-quality render", resolution: "2048x2048" },
];

const cameraPresets = [
  { id: "front", name: "Front View", position: [0, 0, 2], rotation: [0, 0, 0] },
  { id: "profile", name: "Profile", position: [2, 0, 0], rotation: [0, 90, 0] },
  { id: "three-quarter", name: "3/4 View", position: [1.5, 0.5, 1.5], rotation: [0, 45, 0] },
  { id: "top", name: "Top Down", position: [0, 3, 0], rotation: [90, 0, 0] },
];

export default function RenderPage() {
  const [selectedQuality, setSelectedQuality] = useState("medium");
  const [selectedPreset, setSelectedPreset] = useState("front");
  const [renderMode, setRenderMode] = useState<"image" | "360video">("image");
  const [isRendering, setIsRendering] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  // Camera controls
  const [cameraPosition, setCameraPosition] = useState([0, 0, 2]);
  const [cameraRotation, setCameraRotation] = useState([0, 0, 0]);
  const [fov, setFov] = useState(45);

  const renderMutation = useMutation({
    mutationFn: (request: any) => {
      if (renderMode === "image") {
        return renderImage(request);
      } else {
        return render360Video(request);
      }
    },
    onSuccess: (data) => {
      setCurrentJobId(data.job_id);
      setIsRendering(true);
      toast.success("Rendering started!", `Job ID: ${data.job_id}`);
    },
    onError: (error: any) => {
      toast.error("Rendering failed", error.response?.data?.detail || error.message);
    },
  });

  const { data: renderStatus } = useQuery({
    queryKey: ["render-status", currentJobId],
    queryFn: () => getRenderStatus(currentJobId!),
    enabled: !!currentJobId && isRendering,
    refetchInterval: (data) => {
      if (data?.status === "completed" || data?.status === "failed") {
        setIsRendering(false);
        return false;
      }
      return 2000;
    },
  });

  const handleRender = () => {
    const request = {
      model_id: "default_model",
      camera_pose: [
        [1, 0, 0, cameraPosition[0]],
        [0, 1, 0, cameraPosition[1]],
        [0, 0, 1, cameraPosition[2]],
        [0, 0, 0, 1],
      ],
      intrinsics: {
        fx: 500,
        fy: 500,
        cx: 256,
        cy: 256,
        fov: fov,
      },
      resolution: selectedQuality === "low" ? [512, 512] : selectedQuality === "medium" ? [1024, 1024] : [2048, 2048],
      quality: selectedQuality,
    };

    renderMutation.mutate(request);
  };

  const applyPreset = (preset: any) => {
    setCameraPosition(preset.position);
    setCameraRotation(preset.rotation);
    setSelectedPreset(preset.id);
  };

  return (
    <div className="min-h-screen py-8 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
              <Eye className="w-6 h-6 text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            NeRF Rendering Studio
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            3D neural radiance fields for photorealistic product visualization
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* Control Panel */}
          <div className="lg:col-span-1 space-y-6">
            {/* Render Mode */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
            >
              <div className="flex items-center mb-4">
                <Monitor className="w-5 h-5 text-green-400 mr-2" />
                <h3 className="text-lg font-semibold text-white">Render Mode</h3>
              </div>
              <div className="space-y-2">
                <button
                  onClick={() => setRenderMode("image")}
                  className={cn(
                    "w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200",
                    renderMode === "image"
                      ? "bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/50"
                      : "bg-white/5 hover:bg-white/10"
                  )}
                >
                  <ImageIcon className="w-4 h-4" />
                  <div className="text-left">
                    <div className="font-medium text-white">Single Image</div>
                    <div className="text-xs text-gray-400">Static render</div>
                  </div>
                </button>
                <button
                  onClick={() => setRenderMode("360video")}
                  className={cn(
                    "w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200",
                    renderMode === "360video"
                      ? "bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border border-blue-500/50"
                      : "bg-white/5 hover:bg-white/10"
                  )}
                >
                  <Video className="w-4 h-4" />
                  <div className="text-left">
                    <div className="font-medium text-white">360° Video</div>
                    <div className="text-xs text-gray-400">Rotating view</div>
                  </div>
                </button>
              </div>
            </motion.div>

            {/* Camera Presets */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
            >
              <div className="flex items-center mb-4">
                <Camera className="w-5 h-5 text-blue-400 mr-2" />
                <h3 className="text-lg font-semibold text-white">Camera Presets</h3>
              </div>
              <div className="space-y-2">
                {cameraPresets.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => applyPreset(preset)}
                    className={cn(
                      "w-full px-3 py-2 rounded-lg text-left transition-all duration-200",
                      selectedPreset === preset.id
                        ? "bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border border-blue-500/50 text-white"
                        : "text-gray-300 hover:bg-white/5"
                    )}
                  >
                    <div className="font-medium">{preset.name}</div>
                  </button>
                ))}
              </div>
            </motion.div>

            {/* Quality Settings */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
            >
              <div className="flex items-center mb-4">
                <Settings className="w-5 h-5 text-purple-400 mr-2" />
                <h3 className="text-lg font-semibold text-white">Quality</h3>
              </div>
              <div className="space-y-2">
                {qualityOptions.map((quality) => (
                  <button
                    key={quality.id}
                    onClick={() => setSelectedQuality(quality.id)}
                    className={cn(
                      "w-full p-3 rounded-lg text-left transition-all duration-200 border",
                      selectedQuality === quality.id
                        ? "bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-500/50"
                        : "bg-white/5 border-white/10 hover:border-white/20"
                    )}
                  >
                    <div className="font-medium text-white">{quality.name}</div>
                    <div className="text-xs text-gray-400">{quality.description}</div>
                    <div className="text-xs text-gray-500 mt-1">{quality.resolution}</div>
                  </button>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Main Viewport */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <Maximize className="w-6 h-6 text-cyan-400 mr-3" />
                  <h2 className="text-2xl font-bold text-white">3D Viewport</h2>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
                    <RotateCcw className="w-4 h-4 text-gray-400" />
                  </button>
                  <button className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
                    <Move3D className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>

              {/* 3D Preview Area */}
              <div className="aspect-square bg-gradient-to-br from-gray-900 to-black rounded-xl border border-white/10 flex items-center justify-center relative overflow-hidden">
                {/* Grid Background */}
                <div className="absolute inset-0 opacity-20">
                  <div className="absolute inset-0" style={{
                    backgroundImage: `
                      linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
                    `,
                    backgroundSize: '20px 20px'
                  }}></div>
                </div>

                {/* 3D Object Placeholder */}
                <div className="relative z-10 w-48 h-48 bg-gradient-to-br from-purple-500/30 to-pink-500/30 rounded-2xl flex items-center justify-center transform rotate-12 hover:rotate-0 transition-transform duration-500">
                  <Layers className="w-16 h-16 text-white/80" />
                </div>

                {/* Camera Position Indicator */}
                <div className="absolute top-4 left-4 bg-black/50 backdrop-blur-sm rounded-lg p-2">
                  <div className="text-xs text-gray-300">
                    <div>Pos: [{cameraPosition.join(", ")}]</div>
                    <div>FOV: {fov}°</div>
                  </div>
                </div>

                {/* Render Status Overlay */}
                <AnimatePresence>
                  {isRendering && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center"
                    >
                      <div className="text-center">
                        <div className="w-16 h-16 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-4"></div>
                        <div className="text-white font-medium">Rendering...</div>
                        <div className="text-gray-400 text-sm mt-1">
                          Status: {renderStatus?.status || "processing"}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Render Button */}
              <button
                onClick={handleRender}
                disabled={renderMutation.isPending || isRendering}
                className="w-full mt-6 py-4 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl font-semibold text-white hover:shadow-2xl hover:shadow-green-500/25 transition-all duration-300 transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {isRendering ? (
                  <span className="flex items-center justify-center">
                    <Square className="w-5 h-5 mr-2" />
                    Rendering...
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <Play className="w-5 h-5 mr-2" />
                    Start Render
                  </span>
                )}
              </button>
            </motion.div>
          </div>

          {/* Camera Controls */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 space-y-6"
            >
              <div className="flex items-center mb-4">
                <Move3D className="w-5 h-5 text-orange-400 mr-2" />
                <h3 className="text-lg font-semibold text-white">Camera Controls</h3>
              </div>

              {/* Position Controls */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">Position</label>
                <div className="space-y-3">
                  {["X", "Y", "Z"].map((axis, index) => (
                    <div key={axis}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-400">{axis}</span>
                        <span className="text-xs text-white">{cameraPosition[index]}</span>
                      </div>
                      <input
                        type="range"
                        min="-5"
                        max="5"
                        step="0.1"
                        value={cameraPosition[index]}
                        onChange={(e) => {
                          const newPosition = [...cameraPosition];
                          newPosition[index] = parseFloat(e.target.value);
                          setCameraPosition(newPosition);
                        }}
                        className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer slider"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* FOV Control */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-300">Field of View</label>
                  <span className="text-sm text-white">{fov}°</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="120"
                  step="1"
                  value={fov}
                  onChange={(e) => setFov(parseInt(e.target.value))}
                  className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer slider"
                />
              </div>

              {/* Quick Actions */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">Quick Actions</label>
                <div className="space-y-2">
                  <button
                    onClick={() => {
                      setCameraPosition([0, 0, 2]);
                      setCameraRotation([0, 0, 0]);
                      setFov(45);
                    }}
                    className="w-full py-2 px-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-gray-300 transition-colors"
                  >
                    Reset Camera
                  </button>
                  <button className="w-full py-2 px-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-gray-300 transition-colors">
                    Auto Focus
                  </button>
                </div>
              </div>

              {/* Render Progress */}
              {renderStatus && (
                <div className="p-4 rounded-lg bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">Render Progress</span>
                    <span className="text-xs text-blue-400">{renderStatus.status}</span>
                  </div>
                  {renderStatus.status === "processing" && (
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full animate-pulse" style={{ width: "65%" }}></div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}