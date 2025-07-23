"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Sparkles, 
  Upload, 
  Download, 
  Wand2, 
  Image as ImageIcon, 
  Loader2,
  Settings,
  Palette,
  Zap,
  RefreshCw
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { generateImage, getGenerationStatus, listGenerations, type GenerationRequest } from "@/lib/api";
import { toast } from "@/components/ui/toaster";
import { cn } from "@/lib/utils";

const stylePresets = [
  { id: "photorealistic", name: "Photorealistic", description: "Ultra-realistic fashion photography" },
  { id: "artistic", name: "Artistic", description: "Creative and artistic interpretation" },
  { id: "minimalist", name: "Minimalist", description: "Clean, simple aesthetic" },
  { id: "vintage", name: "Vintage", description: "Retro-inspired styling" },
  { id: "futuristic", name: "Futuristic", description: "Modern, sci-fi aesthetic" },
  { id: "editorial", name: "Editorial", description: "High-fashion magazine style" },
];

const qualityOptions = [
  { id: "low", name: "Fast", description: "Quick generation, lower quality", time: "~30s" },
  { id: "medium", name: "Balanced", description: "Good quality and speed", time: "~60s" },
  { id: "high", name: "Premium", description: "Highest quality, slower", time: "~120s" },
];

export default function GeneratePage() {
  const [prompt, setPrompt] = useState("");
  const [selectedStyle, setSelectedStyle] = useState("photorealistic");
  const [selectedQuality, setSelectedQuality] = useState("medium");
  const [numImages, setNumImages] = useState(1);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch recent generations
  const { data: recentGenerations, isLoading: loadingRecent } = useQuery({
    queryKey: ["generations"],
    queryFn: () => listGenerations(12),
  });

  // Generate image mutation
  const generateMutation = useMutation({
    mutationFn: (request: GenerationRequest) => generateImage(request),
    onSuccess: (data) => {
      setActiveJobId(data.job_id);
      toast.success("Generation started!", `Job ID: ${data.job_id}`);
      queryClient.invalidateQueries({ queryKey: ["generations"] });
    },
    onError: (error: any) => {
      toast.error("Generation failed", error.response?.data?.detail || error.message);
    },
  });

  // Poll for job status
  const { data: jobStatus } = useQuery({
    queryKey: ["generation-status", activeJobId],
    queryFn: () => getGenerationStatus(activeJobId!),
    enabled: !!activeJobId,
    refetchInterval: (data) => {
      if (data?.status === "completed" || data?.status === "failed") {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });

  const handleGenerate = () => {
    if (!prompt.trim()) {
      toast.error("Please enter a prompt");
      return;
    }

    generateMutation.mutate({
      prompt: prompt.trim(),
      style: selectedStyle,
      quality: selectedQuality as "low" | "medium" | "high",
      num_images: numImages,
    });
  };

  const isGenerating = generateMutation.isPending || (jobStatus?.status === "processing");

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
            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            AI Fashion Generation
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Transform your ideas into stunning fashion imagery with our advanced AI generation system
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Generation Panel */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
            >
              <div className="flex items-center mb-6">
                <Wand2 className="w-6 h-6 text-purple-400 mr-3" />
                <h2 className="text-2xl font-bold text-white">Create New Generation</h2>
              </div>

              {/* Prompt Input */}
              <div className="mb-8">
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Describe your fashion vision
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="A elegant evening dress with flowing fabric, studio lighting, high fashion photography..."
                  className="w-full h-32 px-4 py-3 bg-black/20 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Style Selection */}
              <div className="mb-8">
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Style Preset
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {stylePresets.map((style) => (
                    <button
                      key={style.id}
                      onClick={() => setSelectedStyle(style.id)}
                      className={cn(
                        "p-4 rounded-xl border transition-all duration-200 text-left",
                        selectedStyle === style.id
                          ? "bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-500/50"
                          : "bg-white/5 border-white/10 hover:border-white/20"
                      )}
                    >
                      <div className="font-medium text-white mb-1">{style.name}</div>
                      <div className="text-xs text-gray-400">{style.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Quality & Settings */}
              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Quality
                  </label>
                  <div className="space-y-2">
                    {qualityOptions.map((quality) => (
                      <button
                        key={quality.id}
                        onClick={() => setSelectedQuality(quality.id)}
                        className={cn(
                          "w-full p-3 rounded-lg border transition-all duration-200 text-left",
                          selectedQuality === quality.id
                            ? "bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border-blue-500/50"
                            : "bg-white/5 border-white/10 hover:border-white/20"
                        )}
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <div className="font-medium text-white">{quality.name}</div>
                            <div className="text-xs text-gray-400">{quality.description}</div>
                          </div>
                          <div className="text-xs text-gray-400">{quality.time}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Number of Images
                  </label>
                  <div className="grid grid-cols-4 gap-2">
                    {[1, 2, 3, 4].map((num) => (
                      <button
                        key={num}
                        onClick={() => setNumImages(num)}
                        className={cn(
                          "p-3 rounded-lg border transition-all duration-200 text-center font-medium",
                          numImages === num
                            ? "bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-green-500/50 text-white"
                            : "bg-white/5 border-white/10 hover:border-white/20 text-gray-300"
                        )}
                      >
                        {num}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !prompt.trim()}
                className="w-full py-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl font-semibold text-white hover:shadow-2xl hover:shadow-purple-500/25 transition-all duration-300 transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {isGenerating ? (
                  <span className="flex items-center justify-center">
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Generating...
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <Sparkles className="w-5 h-5 mr-2" />
                    Generate Fashion
                  </span>
                )}
              </button>

              {/* Generation Status */}
              <AnimatePresence>
                {jobStatus && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="mt-6 p-4 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-white">Generation Status</span>
                      <span className={cn(
                        "px-2 py-1 rounded-full text-xs font-medium",
                        jobStatus.status === "completed" ? "bg-green-500/20 text-green-400" :
                        jobStatus.status === "failed" ? "bg-red-500/20 text-red-400" :
                        "bg-blue-500/20 text-blue-400"
                      )}>
                        {jobStatus.status}
                      </span>
                    </div>
                    {jobStatus.status === "processing" && (
                      <div className="w-full bg-white/10 rounded-full h-2">
                        <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full animate-pulse" style={{ width: "60%" }}></div>
                      </div>
                    )}
                    {jobStatus.error && (
                      <p className="text-sm text-red-400 mt-2">{jobStatus.error}</p>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <ImageIcon className="w-5 h-5 text-green-400 mr-2" />
                  <h3 className="text-lg font-semibold text-white">Recent Generations</h3>
                </div>
                <button
                  onClick={() => queryClient.invalidateQueries({ queryKey: ["generations"] })}
                  className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <RefreshCw className="w-4 h-4 text-gray-400" />
                </button>
              </div>

              {loadingRecent ? (
                <div className="space-y-4">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="bg-white/10 rounded-lg h-32 mb-2"></div>
                      <div className="bg-white/10 rounded h-4 w-3/4"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {recentGenerations?.jobs?.map((job: any) => (
                    <div key={job.job_id} className="p-4 rounded-lg bg-white/5 border border-white/10">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-white truncate">
                          {job.prompt?.substring(0, 30)}...
                        </span>
                        <span className={cn(
                          "px-2 py-1 rounded-full text-xs",
                          job.status === "completed" ? "bg-green-500/20 text-green-400" :
                          job.status === "failed" ? "bg-red-500/20 text-red-400" :
                          "bg-yellow-500/20 text-yellow-400"
                        )}>
                          {job.status}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(job.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}