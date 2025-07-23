import axios from "axios";

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";

// Service URLs
export const SERVICES = {
  GENERATION: process.env.NEXT_PUBLIC_GENERATION_API || "http://localhost:8001",
  MEMORY: process.env.NEXT_PUBLIC_MEMORY_SERVICE || "http://localhost:8002", 
  RENDERING: process.env.NEXT_PUBLIC_RENDERING_SERVICE || "http://localhost:8003",
  CURATION: process.env.NEXT_PUBLIC_CURATION_ENGINE || "http://localhost:8004",
};

// Create axios instances for each service
const createApiClient = (baseURL: string) => {
  const client = axios.create({
    baseURL,
    timeout: 30000, // 30 seconds
    headers: {
      "Content-Type": "application/json",
    },
  });

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem("auth_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Handle unauthorized access
        localStorage.removeItem("auth_token");
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }
  );

  return client;
};

export const generationApi = createApiClient(SERVICES.GENERATION);
export const memoryApi = createApiClient(SERVICES.MEMORY);
export const renderingApi = createApiClient(SERVICES.RENDERING);
export const curationApi = createApiClient(SERVICES.CURATION);

// API Types
export interface GenerationRequest {
  prompt: string;
  style?: string;
  quality?: "low" | "medium" | "high";
  num_images?: number;
}

export interface GenerationResponse {
  job_id: string;
  status: string;
  message: string;
  estimated_time?: number;
}

export interface GenerationResult {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  result?: {
    images: string[];
    metadata: any;
  };
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface MemoryEntry {
  id: string;
  content: string;
  embedding?: number[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface RenderRequest {
  model_id: string;
  camera_pose: number[][];
  intrinsics: Record<string, number>;
  resolution?: number[];
  quality?: "low" | "medium" | "high";
}

export interface QualityAssessment {
  overall_score: number;
  quality_category: string;
  component_scores: {
    visual_quality: { score: number; details: any };
    aesthetic_appeal: { score: number; details: any };
    fashion_relevance: { score: number; details: any };
    technical_quality: { score: number; details: any };
    brand_alignment: { score: number; details: any };
  };
  recommendations: string[];
}

// API Functions

// Generation API
export const generateImage = async (request: GenerationRequest): Promise<GenerationResponse> => {
  const response = await generationApi.post("/api/v1/generate/text-to-image", request);
  return response.data;
};

export const getGenerationStatus = async (jobId: string): Promise<GenerationResult> => {
  const response = await generationApi.get(`/api/v1/generate/job/${jobId}`);
  return response.data;
};

export const listGenerations = async (limit = 20) => {
  const response = await generationApi.get(`/api/v1/generate/jobs?limit=${limit}`);
  return response.data;
};

// Memory API
export const storeMemory = async (content: string, metadata?: Record<string, any>) => {
  const response = await memoryApi.post("/api/v1/memory/store", {
    content,
    metadata: metadata || {},
  });
  return response.data;
};

export const searchMemory = async (query: string, limit = 10) => {
  const response = await memoryApi.post("/api/v1/memory/search", {
    query,
    limit,
  });
  return response.data;
};

export const getMemoryEntries = async (limit = 20) => {
  const response = await memoryApi.get(`/api/v1/memory/entries?limit=${limit}`);
  return response.data;
};

// Rendering API
export const renderImage = async (request: RenderRequest) => {
  const response = await renderingApi.post("/api/v1/render/image", request);
  return response.data;
};

export const render360Video = async (request: any) => {
  const response = await renderingApi.post("/api/v1/render/360-video", request);
  return response.data;
};

export const getRenderStatus = async (jobId: string) => {
  const response = await renderingApi.get(`/api/v1/render/job/${jobId}`);
  return response.data;
};

// Curation API
export const assessQuality = async (imageData: string, context?: any): Promise<QualityAssessment> => {
  const response = await curationApi.post("/api/v1/curation/assess-quality", {
    image_data: imageData,
    context,
  });
  return response.data.assessment;
};

export const getUserRecommendations = async (userId: string, options?: any) => {
  const response = await curationApi.post("/api/v1/curation/recommendations/user", {
    user_id: userId,
    ...options,
  });
  return response.data;
};

export const getTrendingItems = async (timeWindow = "week", categories?: string[]) => {
  const response = await curationApi.post("/api/v1/curation/recommendations/trending", {
    time_window: timeWindow,
    categories,
  });
  return response.data;
};

// Health Check Functions
export const checkServiceHealth = async (service: keyof typeof SERVICES) => {
  try {
    const client = {
      GENERATION: generationApi,
      MEMORY: memoryApi,
      RENDERING: renderingApi,
      CURATION: curationApi,
    }[service];

    const response = await client.get("/api/v1/health");
    return { service, status: "healthy", data: response.data };
  } catch (error) {
    return { service, status: "unhealthy", error };
  }
};

export const checkAllServices = async () => {
  const services = Object.keys(SERVICES) as (keyof typeof SERVICES)[];
  const results = await Promise.allSettled(
    services.map((service) => checkServiceHealth(service))
  );

  return results.map((result, index) => ({
    service: services[index],
    ...(result.status === "fulfilled" ? result.value : { status: "error", error: result.reason }),
  }));
};

// Utility Functions
export const uploadFile = async (file: File, service: "generation" | "curation" = "generation") => {
  const formData = new FormData();
  formData.append("file", file);

  const client = service === "generation" ? generationApi : curationApi;
  const endpoint = service === "generation" ? "/api/v1/generate/upload" : "/api/v1/curation/assess-quality";

  const response = await client.post(endpoint, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

export const downloadResult = async (url: string, filename: string) => {
  const response = await fetch(url);
  const blob = await response.blob();
  
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
};

export default {
  generateImage,
  getGenerationStatus,
  listGenerations,
  storeMemory,
  searchMemory,
  getMemoryEntries,
  renderImage,
  render360Video,
  getRenderStatus,
  assessQuality,
  getUserRecommendations,
  getTrendingItems,
  checkServiceHealth,
  checkAllServices,
  uploadFile,
  downloadResult,
};