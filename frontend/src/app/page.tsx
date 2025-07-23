"use client";

import { motion } from "framer-motion";
import { 
  Sparkles, 
  Brain, 
  Eye, 
  Palette, 
  Zap, 
  Shield, 
  Cpu, 
  ArrowRight,
  Play,
  Star,
  Users,
  TrendingUp
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const features = [
  {
    icon: Sparkles,
    title: "AI Generation",
    description: "Revolutionary text-to-image generation with style transfer and advanced neural networks",
    color: "from-purple-500 to-pink-500",
    href: "/generate"
  },
  {
    icon: Brain,
    title: "KSE Memory",
    description: "Intelligent memory system with temporal reasoning and multi-modal embeddings",
    color: "from-blue-500 to-cyan-500",
    href: "/memory"
  },
  {
    icon: Eye,
    title: "NeRF Rendering",
    description: "3D neural radiance fields for photorealistic product visualization",
    color: "from-green-500 to-emerald-500",
    href: "/render"
  },
  {
    icon: Palette,
    title: "Smart Curation",
    description: "AI-powered quality assessment and intelligent recommendation system",
    color: "from-orange-500 to-red-500",
    href: "/curate"
  }
];

const stats = [
  { label: "AI Models", value: "10+", icon: Cpu },
  { label: "API Endpoints", value: "35+", icon: Zap },
  { label: "Success Rate", value: "99.9%", icon: Shield },
  { label: "Users", value: "1K+", icon: Users }
];

export default function HomePage() {
  const [hoveredFeature, setHoveredFeature] = useState<number | null>(null);

  return (
    <div className="relative">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="flex items-center justify-center mb-6">
              <div className="px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 backdrop-blur-sm">
                <span className="text-sm font-medium text-purple-300">🚀 Production Ready v1.0</span>
              </div>
            </div>

            <h1 className="text-6xl md:text-8xl font-bold mb-6 bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent leading-tight">
              GEN-VIEW-KSE
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-4xl mx-auto leading-relaxed">
              Revolutionary AI platform for fashion generation, visualization, and curation with 
              <span className="text-transparent bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text font-semibold"> advanced neural rendering</span> and 
              <span className="text-transparent bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text font-semibold"> intelligent memory systems</span>
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
              <Link
                href="/generate"
                className="group relative px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl font-semibold text-white hover:shadow-2xl hover:shadow-purple-500/25 transition-all duration-300 transform hover:scale-105"
              >
                <span className="flex items-center">
                  Start Creating
                  <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl blur opacity-0 group-hover:opacity-50 transition-opacity duration-300 -z-10"></div>
              </Link>

              <button className="group flex items-center px-6 py-4 rounded-xl border border-white/20 text-white hover:bg-white/5 transition-all duration-300">
                <Play className="mr-2 w-5 h-5" />
                Watch Demo
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
              {stats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 + index * 0.1 }}
                    className="text-center p-4 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10"
                  >
                    <Icon className="w-6 h-6 mx-auto mb-2 text-gray-400" />
                    <div className="text-2xl font-bold text-white">{stat.value}</div>
                    <div className="text-sm text-gray-400">{stat.label}</div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Powerful AI Features
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Experience the future of fashion technology with our comprehensive suite of AI-powered tools
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              const isHovered = hoveredFeature === index;
              
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  onMouseEnter={() => setHoveredFeature(index)}
                  onMouseLeave={() => setHoveredFeature(null)}
                  className="group relative"
                >
                  <Link href={feature.href}>
                    <div className="relative p-8 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-white/20 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl">
                      {/* Gradient Background */}
                      <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-300`}></div>
                      
                      {/* Icon */}
                      <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className="w-8 h-8 text-white" />
                      </div>

                      {/* Content */}
                      <h3 className="text-xl font-bold text-white mb-3 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-300 group-hover:bg-clip-text transition-all duration-300">
                        {feature.title}
                      </h3>
                      <p className="text-gray-400 group-hover:text-gray-300 transition-colors duration-300">
                        {feature.description}
                      </p>

                      {/* Arrow */}
                      <div className="absolute top-8 right-8 opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-all duration-300">
                        <ArrowRight className="w-5 h-5 text-white" />
                      </div>

                      {/* Glow Effect */}
                      {isHovered && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className={`absolute -inset-1 bg-gradient-to-br ${feature.color} rounded-2xl blur opacity-20 -z-10`}
                        />
                      )}
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section className="py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Cutting-Edge Technology
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Built with state-of-the-art AI models and production-ready infrastructure
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className="p-8 rounded-2xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20"
            >
              <Cpu className="w-12 h-12 text-purple-400 mb-6" />
              <h3 className="text-2xl font-bold text-white mb-4">Neural Architecture</h3>
              <ul className="space-y-2 text-gray-300">
                <li>• Neural Radiance Fields (NeRF)</li>
                <li>• CLIP Multi-Modal Understanding</li>
                <li>• Transformer-based Generation</li>
                <li>• Advanced Quality Assessment</li>
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: true }}
              className="p-8 rounded-2xl bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20"
            >
              <Shield className="w-12 h-12 text-blue-400 mb-6" />
              <h3 className="text-2xl font-bold text-white mb-4">Production Ready</h3>
              <ul className="space-y-2 text-gray-300">
                <li>• 90/100 Production Score</li>
                <li>• Comprehensive Monitoring</li>
                <li>• Auto-scaling Infrastructure</li>
                <li>• 99.9% Uptime SLA</li>
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              viewport={{ once: true }}
              className="p-8 rounded-2xl bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20"
            >
              <TrendingUp className="w-12 h-12 text-green-400 mb-6" />
              <h3 className="text-2xl font-bold text-white mb-4">Performance</h3>
              <ul className="space-y-2 text-gray-300">
                <li>• Sub-second API Response</li>
                <li>• Real-time 3D Rendering</li>
                <li>• Intelligent Caching</li>
                <li>• Optimized Inference</li>
              </ul>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-pink-500/10"></div>
        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Ready to Transform Fashion?
            </h2>
            <p className="text-xl text-gray-400 mb-8">
              Join the revolution in AI-powered fashion generation and visualization
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/generate"
                className="group relative px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl font-semibold text-white hover:shadow-2xl hover:shadow-purple-500/25 transition-all duration-300 transform hover:scale-105"
              >
                <span className="flex items-center">
                  Get Started Now
                  <Sparkles className="ml-2 w-5 h-5 group-hover:rotate-12 transition-transform" />
                </span>
              </Link>
              <Link
                href="/analytics"
                className="px-8 py-4 rounded-xl border border-white/20 text-white hover:bg-white/5 transition-all duration-300"
              >
                View Analytics
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
