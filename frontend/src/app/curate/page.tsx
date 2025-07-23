"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  Palette, 
  Upload, 
  Star, 
  TrendingUp, 
  Users, 
  Eye,
  Award,
  CheckCircle,
  AlertTriangle,
  BarChart3,
  Filter,
  Search
} from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { assessQuality, getUserRecommendations, getTrendingItems } from "@/lib/api";
import { toast } from "@/components/ui/toaster";
import { cn } from "@/lib/utils";

const qualityCategories = [
  { id: "excellent", name: "Excellent", color: "from-green-500 to-emerald-500", icon: Award },
  { id: "good", name: "Good", color: "from-blue-500 to-cyan-500", icon: CheckCircle },
  { id: "fair", name: "Fair", color: "from-yellow-500 to-orange-500", icon: AlertTriangle },
  { id: "poor", name: "Poor", color: "from-red-500 to-pink-500", icon: AlertTriangle },
];

const ScoreCard = ({ title, score, details, color }: any) => (
  <div className="p-4 rounded-lg bg-white/5 border border-white/10">
    <div className="flex items-center justify-between mb-2">
      <h4 className="text-sm font-medium text-gray-300">{title}</h4>
      <span className={`text-lg font-bold bg-gradient-to-r ${color} bg-clip-text text-transparent`}>
        {score}
      </span>
    </div>
    <div className="w-full bg-white/10 rounded-full h-2">
      <div 
        className={`bg-gradient-to-r ${color} h-2 rounded-full transition-all duration-500`}
        style={{ width: `${score}%` }}
      />
    </div>
    {details && (
      <p className="text-xs text-gray-400 mt-2">{details}</p>
    )}
  </div>
);

export default function CuratePage() {
  const [selectedTab, setSelectedTab] = useState("assess");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [assessment, setAssessment] = useState<any>(null);

  const { data: trending } = useQuery({
    queryKey: ["trending"],
    queryFn: () => getTrendingItems("week"),
  });

  const { data: recommendations } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => getUserRecommendations("user123"),
  });

  const assessMutation = useMutation({
    mutationFn: async (file: File) => {
      const base64 = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
      });
      return assessQuality(base64.split(',')[1]);
    },
    onSuccess: (data) => {
      setAssessment(data);
      toast.success("Quality assessment completed!");
    },
    onError: () => {
      toast.error("Assessment failed");
    },
  });

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      assessMutation.mutate(file);
    }
  };

  return (
    <div className="min-h-screen py-8 px-6">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
              <Palette className="w-6 h-6 text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            AI Curation Engine
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            AI-powered quality assessment and intelligent recommendation system
          </p>
        </motion.div>

        {/* Tab Navigation */}
        <div className="flex items-center justify-center mb-8">
          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-1">
            {[
              { id: "assess", name: "Quality Assessment", icon: Award },
              { id: "trending", name: "Trending", icon: TrendingUp },
              { id: "recommendations", name: "Recommendations", icon: Users },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id)}
                  className={cn(
                    "relative px-6 py-3 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2",
                    selectedTab === tab.id
                      ? "bg-gradient-to-r from-orange-500/20 to-red-500/20 text-white"
                      : "text-gray-400 hover:text-white"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                  {selectedTab === tab.id && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-red-500/20 rounded-lg border border-orange-500/30"
                    />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Quality Assessment Tab */}
        {selectedTab === "assess" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid lg:grid-cols-2 gap-8"
          >
            {/* Upload Area */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8">
              <div className="flex items-center mb-6">
                <Upload className="w-6 h-6 text-orange-400 mr-3" />
                <h2 className="text-2xl font-bold text-white">Upload for Assessment</h2>
              </div>

              <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center hover:border-orange-500/50 transition-colors">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-medium text-white mb-2">
                    Drop your image here or click to upload
                  </p>
                  <p className="text-gray-400">
                    Supports JPG, PNG, WebP up to 10MB
                  </p>
                </label>
              </div>

              {uploadedFile && (
                <div className="mt-6 p-4 bg-white/5 rounded-lg">
                  <p className="text-sm text-gray-300">
                    Uploaded: {uploadedFile.name}
                  </p>
                  {assessMutation.isPending && (
                    <div className="mt-2 flex items-center text-orange-400">
                      <div className="w-4 h-4 border-2 border-orange-400/30 border-t-orange-400 rounded-full animate-spin mr-2"></div>
                      Analyzing...
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Assessment Results */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8">
              <div className="flex items-center mb-6">
                <BarChart3 className="w-6 h-6 text-green-400 mr-3" />
                <h2 className="text-2xl font-bold text-white">Assessment Results</h2>
              </div>

              {assessment ? (
                <div className="space-y-6">
                  {/* Overall Score */}
                  <div className="text-center p-6 rounded-xl bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20">
                    <div className="text-4xl font-bold text-white mb-2">
                      {assessment.overall_score}
                    </div>
                    <div className="text-green-400 font-medium">
                      {assessment.quality_category}
                    </div>
                  </div>

                  {/* Component Scores */}
                  <div className="space-y-4">
                    <ScoreCard
                      title="Visual Quality"
                      score={assessment.component_scores?.visual_quality?.score || 0}
                      color="from-blue-500 to-cyan-500"
                    />
                    <ScoreCard
                      title="Aesthetic Appeal"
                      score={assessment.component_scores?.aesthetic_appeal?.score || 0}
                      color="from-purple-500 to-pink-500"
                    />
                    <ScoreCard
                      title="Fashion Relevance"
                      score={assessment.component_scores?.fashion_relevance?.score || 0}
                      color="from-green-500 to-emerald-500"
                    />
                    <ScoreCard
                      title="Technical Quality"
                      score={assessment.component_scores?.technical_quality?.score || 0}
                      color="from-orange-500 to-red-500"
                    />
                  </div>

                  {/* Recommendations */}
                  {assessment.recommendations && assessment.recommendations.length > 0 && (
                    <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                      <h4 className="font-medium text-white mb-2">Recommendations</h4>
                      <ul className="space-y-1">
                        {assessment.recommendations.map((rec: string, index: number) => (
                          <li key={index} className="text-sm text-gray-300">
                            • {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-16">
                  <Eye className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">Upload an image to see quality assessment</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Trending Tab */}
        {selectedTab === "trending" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
          >
            <div className="flex items-center mb-8">
              <TrendingUp className="w-6 h-6 text-pink-400 mr-3" />
              <h2 className="text-2xl font-bold text-white">Trending Items</h2>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {trending?.items?.map((item: any, index: number) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-6 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-200"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium text-white">{item.title}</h3>
                    <div className="flex items-center text-pink-400">
                      <TrendingUp className="w-4 h-4 mr-1" />
                      <span className="text-sm">{item.trend_score}</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mb-4">{item.description}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{item.category}</span>
                    <span>{item.engagement_count} engagements</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Recommendations Tab */}
        {selectedTab === "recommendations" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
          >
            <div className="flex items-center mb-8">
              <Users className="w-6 h-6 text-cyan-400 mr-3" />
              <h2 className="text-2xl font-bold text-white">Personalized Recommendations</h2>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {recommendations?.recommendations?.map((rec: any, index: number) => (
                <motion.div
                  key={rec.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-6 rounded-xl bg-white/5 border border-white/10"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium text-white">{rec.title}</h3>
                    <div className="flex items-center text-yellow-400">
                      <Star className="w-4 h-4 mr-1" />
                      <span className="text-sm">{rec.confidence_score}</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mb-4">{rec.reason}</p>
                  <div className="text-xs text-gray-500">{rec.category}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}