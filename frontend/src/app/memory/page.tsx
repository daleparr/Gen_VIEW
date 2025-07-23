"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Brain, Search, Plus, Network } from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { storeMemory, searchMemory, getMemoryEntries } from "@/lib/api";
import { toast } from "@/components/ui/toaster";

export default function MemoryPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [newMemoryContent, setNewMemoryContent] = useState("");

  const { data: memories, isLoading } = useQuery({
    queryKey: ["memories"],
    queryFn: () => getMemoryEntries(20),
  });

  const storeMutation = useMutation({
    mutationFn: (content: string) => storeMemory(content),
    onSuccess: () => {
      toast.success("Memory stored successfully!");
      setNewMemoryContent("");
    },
    onError: () => {
      toast.error("Failed to store memory");
    },
  });

  return (
    <div className="min-h-screen py-8 px-6">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            KSE Memory System
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Intelligent memory storage with temporal reasoning and multi-modal embeddings
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 space-y-6">
              <div>
                <div className="flex items-center mb-4">
                  <Search className="w-5 h-5 text-blue-400 mr-2" />
                  <h3 className="text-lg font-semibold text-white">Search Memories</h3>
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search memories..."
                  className="w-full px-4 py-3 bg-black/20 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <div className="flex items-center mb-4">
                  <Plus className="w-5 h-5 text-purple-400 mr-2" />
                  <h3 className="text-lg font-semibold text-white">Store Memory</h3>
                </div>
                <textarea
                  value={newMemoryContent}
                  onChange={(e) => setNewMemoryContent(e.target.value)}
                  placeholder="Enter memory content..."
                  className="w-full h-24 px-3 py-2 bg-black/20 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                />
                <button
                  onClick={() => storeMutation.mutate(newMemoryContent)}
                  disabled={!newMemoryContent.trim() || storeMutation.isPending}
                  className="w-full mt-3 py-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg font-medium text-white hover:shadow-lg transition-all duration-200 disabled:opacity-50"
                >
                  {storeMutation.isPending ? "Storing..." : "Store Memory"}
                </button>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8">
              <div className="flex items-center mb-8">
                <Network className="w-6 h-6 text-cyan-400 mr-3" />
                <h2 className="text-2xl font-bold text-white">Memory Network</h2>
              </div>

              {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="animate-pulse bg-white/10 rounded-xl h-32"></div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {memories?.memories?.map((memory: any, index: number) => (
                    <motion.div
                      key={memory.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-200"
                    >
                      <p className="text-white text-sm mb-3 line-clamp-3">{memory.content}</p>
                      <div className="text-xs text-gray-400">
                        {new Date(memory.created_at).toLocaleDateString()}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}