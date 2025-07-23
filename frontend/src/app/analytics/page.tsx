"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Zap,
  Activity,
  Clock,
  Target,
  Award,
  Eye,
  Brain,
  Palette,
  Monitor
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { checkAllServices } from "@/lib/api";
import { cn } from "@/lib/utils";

const MetricCard = ({ title, value, change, icon: Icon, color, trend }: any) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-200"
  >
    <div className="flex items-center justify-between mb-4">
      <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${color} flex items-center justify-center`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div className={cn(
        "flex items-center text-sm font-medium",
        trend === "up" ? "text-green-400" : trend === "down" ? "text-red-400" : "text-gray-400"
      )}>
        <TrendingUp className={cn("w-4 h-4 mr-1", trend === "down" && "rotate-180")} />
        {change}
      </div>
    </div>
    <div className="text-2xl font-bold text-white mb-1">{value}</div>
    <div className="text-sm text-gray-400">{title}</div>
  </motion.div>
);

const ServiceStatus = ({ service, status, responseTime }: any) => (
  <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/10">
    <div className="flex items-center space-x-3">
      <div className={cn(
        "w-3 h-3 rounded-full",
        status === "healthy" ? "bg-green-400 animate-pulse" : "bg-red-400"
      )}></div>
      <span className="font-medium text-white">{service}</span>
    </div>
    <div className="flex items-center space-x-4 text-sm">
      <span className="text-gray-400">{responseTime}ms</span>
      <span className={cn(
        "px-2 py-1 rounded-full text-xs font-medium",
        status === "healthy" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
      )}>
        {status}
      </span>
    </div>
  </div>
);

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("24h");

  const { data: serviceHealth, isLoading } = useQuery({
    queryKey: ["service-health"],
    queryFn: checkAllServices,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Mock analytics data
  const metrics = [
    {
      title: "Total Generations",
      value: "12,847",
      change: "+12.5%",
      icon: Zap,
      color: "from-purple-500 to-pink-500",
      trend: "up"
    },
    {
      title: "Active Users",
      value: "1,234",
      change: "+8.2%",
      icon: Users,
      color: "from-blue-500 to-cyan-500",
      trend: "up"
    },
    {
      title: "Memory Entries",
      value: "45,692",
      change: "+15.3%",
      icon: Brain,
      color: "from-green-500 to-emerald-500",
      trend: "up"
    },
    {
      title: "Render Jobs",
      value: "8,956",
      change: "-2.1%",
      icon: Eye,
      color: "from-orange-500 to-red-500",
      trend: "down"
    },
  ];

  const performanceMetrics = [
    { name: "API Response Time", value: "145ms", status: "excellent" },
    { name: "Generation Success Rate", value: "99.2%", status: "excellent" },
    { name: "Memory Retrieval Speed", value: "23ms", status: "excellent" },
    { name: "Render Queue Length", value: "12", status: "good" },
  ];

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
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            Analytics Dashboard
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Real-time metrics and insights for the GEN-VIEW-KSE platform
          </p>
        </motion.div>

        {/* Time Range Selector */}
        <div className="flex items-center justify-center mb-8">
          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-1">
            {["1h", "24h", "7d", "30d"].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={cn(
                  "px-6 py-2 rounded-lg font-medium transition-all duration-200",
                  timeRange === range
                    ? "bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white"
                    : "text-gray-400 hover:text-white"
                )}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        {/* Main Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {metrics.map((metric, index) => (
            <MetricCard key={metric.title} {...metric} />
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Service Health */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
            >
              <div className="flex items-center mb-6">
                <Activity className="w-6 h-6 text-green-400 mr-3" />
                <h2 className="text-xl font-bold text-white">Service Health</h2>
              </div>

              <div className="space-y-4">
                {isLoading ? (
                  [...Array(4)].map((_, i) => (
                    <div key={i} className="animate-pulse bg-white/10 rounded-lg h-16"></div>
                  ))
                ) : (
                  serviceHealth?.map((service: any, index: number) => (
                    <ServiceStatus
                      key={service.service}
                      service={service.service}
                      status={service.status}
                      responseTime={Math.floor(Math.random() * 200) + 50}
                    />
                  ))
                )}
              </div>

              {/* Overall Health Score */}
              <div className="mt-6 p-4 rounded-lg bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">Overall Health</span>
                  <div className="flex items-center text-green-400">
                    <Award className="w-4 h-4 mr-1" />
                    <span className="text-sm font-bold">98.5%</span>
                  </div>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full" style={{ width: "98.5%" }}></div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Performance Metrics */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <Target className="w-6 h-6 text-blue-400 mr-3" />
                  <h2 className="text-xl font-bold text-white">Performance Metrics</h2>
                </div>
                <div className="text-sm text-gray-400">Last updated: 2 min ago</div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {performanceMetrics.map((metric, index) => (
                  <motion.div
                    key={metric.name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 rounded-lg bg-white/5 border border-white/10"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-300">{metric.name}</span>
                      <span className={cn(
                        "px-2 py-1 rounded-full text-xs font-medium",
                        metric.status === "excellent" ? "bg-green-500/20 text-green-400" :
                        metric.status === "good" ? "bg-blue-500/20 text-blue-400" :
                        "bg-yellow-500/20 text-yellow-400"
                      )}>
                        {metric.status}
                      </span>
                    </div>
                    <div className="text-2xl font-bold text-white">{metric.value}</div>
                  </motion.div>
                ))}
              </div>

              {/* Real-time Activity Chart Placeholder */}
              <div className="mt-8 p-6 rounded-lg bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20">
                <h3 className="text-lg font-semibold text-white mb-4">Real-time Activity</h3>
                <div className="h-32 bg-black/20 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <BarChart3 className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-400">Live metrics visualization</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Usage Statistics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
        >
          <div className="flex items-center mb-6">
            <Monitor className="w-6 h-6 text-cyan-400 mr-3" />
            <h2 className="text-2xl font-bold text-white">Service Usage</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { service: "Generation API", requests: "45.2K", icon: Zap, color: "from-purple-500 to-pink-500" },
              { service: "Memory Service", requests: "32.1K", icon: Brain, color: "from-blue-500 to-cyan-500" },
              { service: "Rendering Engine", requests: "18.7K", icon: Eye, color: "from-green-500 to-emerald-500" },
              { service: "Curation System", requests: "12.3K", icon: Palette, color: "from-orange-500 to-red-500" },
            ].map((service, index) => {
              const Icon = service.icon;
              return (
                <motion.div
                  key={service.service}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                  className="text-center p-6 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-200"
                >
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${service.color} flex items-center justify-center mx-auto mb-4`}>
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  <div className="text-2xl font-bold text-white mb-1">{service.requests}</div>
                  <div className="text-sm text-gray-400">{service.service}</div>
                  <div className="text-xs text-gray-500 mt-2">requests today</div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </div>
  );
}