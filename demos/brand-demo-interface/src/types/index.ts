/**
 * TypeScript type definitions for GEN-VIEW-KSE Demo Interface
 * Comprehensive types for multi-modal inputs, generation requests, and results
 */

// Generation Status Enum
export enum GenerationStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  TIMEOUT = 'timeout'
}

// Multi-Modal Input Types
export interface MultiModalInputs {
  textPrompt?: string;
  referenceImages: string[];
  sketchInputs: string[];
  colorPalette: string[];
  materialPreferences: string[];
  styleVectors: number[];
  brandContext?: BrandContext;
}

export interface BrandContext {
  brandId: string;
  designDNA: DesignDNA;
  guidelines: BrandGuidelines;
}

export interface DesignDNA {
  aesthetic: string;
  colorPreferences: string[];
  silhouetteStyle: string;
  targetDemographic: string;
  sustainabilityFocus?: boolean;
  luxuryLevel: number;
  innovationTendency: number;
}

export interface BrandGuidelines {
  allowedColors: string[];
  forbiddenElements: string[];
  priceRange: PriceRange;
  seasonalConstraints: SeasonalConstraints;
  materialRestrictions: string[];
}

export interface PriceRange {
  min: number;
  max: number;
  currency: string;
}

export interface SeasonalConstraints {
  preferredSeasons: string[];
  avoidSeasons: string[];
  climateConsiderations: string[];
}

// Brand Configuration
export interface BrandConfig {
  id: string;
  name: string;
  designDNA: DesignDNA;
  guidelines: BrandGuidelines;
  theme: BrandTheme;
  targetDemographic: string;
  pricePoint: string;
  sustainabilityRequirements?: SustainabilityRequirements;
}

export interface BrandTheme {
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  backgroundColor: string;
  textColor: string;
  fontFamily: string;
  borderRadius: number;
  shadows: boolean;
  gradients: boolean;
}

export interface SustainabilityRequirements {
  recycledMaterials: boolean;
  organicMaterials: boolean;
  ethicalProduction: boolean;
  carbonNeutral: boolean;
  circularDesign: boolean;
}

// Generation Request Types
export interface GenerationRequest {
  name: string;
  description?: string;
  inputs: MultiModalInputs;
  brandParameters: BrandParameters;
  targetPieces: number;
  qualityLevel: QualityLevel;
  creativityLevel: number;
  useMemoryContext: boolean;
  memoryDepth: number;
  optimizeForCommercial: boolean;
  targetConversionRate?: number;
}

export interface BrandParameters {
  brandId: string;
  designDnaAdherence: number;
  targetDemographic?: string;
  pricePoint?: string;
  sustainabilityRequirements?: SustainabilityRequirements;
  seasonalConstraints?: SeasonalConstraints;
}

export type QualityLevel = 'draft' | 'standard' | 'high' | 'ultra';

// Generation Response Types
export interface GenerationResponse {
  taskId: string;
  status: GenerationStatus;
  estimatedCompletion: string;
  kseContextRetrieved: boolean;
  memoryNodesAccessed: number;
  commercialPredictionsEnabled: boolean;
  websocketUrl: string;
}

// Generation Results Types
export interface GenerationResults {
  taskId: string;
  generationType: string;
  outputs: GenerationOutput[];
  metadata: GenerationMetadata;
  completedAt: string;
}

export interface GenerationOutput {
  outputId: string;
  conceptId?: string;
  outputIndex: number;
  outputType: string;
  resolution: [number, number];
  contentUrl: string;
  thumbnailUrl: string;
  generationMetadata: OutputGenerationMetadata;
  qualityAssessment: QualityAssessment;
  commercialOptimization?: CommercialOptimization;
  userInteraction?: UserInteraction;
}

export interface OutputGenerationMetadata {
  modelUsed: string;
  generationTime: number;
  seed: number;
  qualityLevel: QualityLevel;
  processingSteps?: string[];
}

export interface QualityAssessment {
  overallQuality: number;
  technicalQuality: number;
  aestheticQuality: number;
  brandAlignment: number;
  commercialViability: number;
  clipScore: number;
  styleConsistency: number;
  noveltyScore: number;
}

export interface CommercialOptimization {
  predictedConversionRate: number;
  predictedEngagement: number;
  marketFitScore: number;
  pricingOptimization: PricingOptimization;
  targetDemographics: string[];
  optimizationApplied: boolean;
  optimizationAdjustments?: OptimizationAdjustments;
}

export interface PricingOptimization {
  suggestedPriceRange: PriceRange;
  priceElasticity: number;
}

export interface OptimizationAdjustments {
  colorAppealBoost: number;
  silhouetteMarketFit: number;
  pricePointOptimization: number;
}

export interface UserInteraction {
  userRating?: number;
  isFavorite: boolean;
  isApproved: boolean;
  timeSpentViewing?: number;
  interactionCount: number;
  shared: boolean;
}

export interface GenerationMetadata {
  totalOutputs: number;
  averageQuality: number;
  generationTime: number;
  memoryNodesUsed: number;
  kseEnhanced: boolean;
  modelVersions: ModelVersions;
}

export interface ModelVersions {
  primaryModel: string;
  secondaryModels: Record<string, string>;
  clipVersion: string;
  kseVersion: string;
}

// KSE Memory Types
export interface MemoryInsights {
  brandId: string;
  totalNodes: number;
  recentGenerations: RecentGeneration[];
  designEvolution: DesignEvolution;
  commercialPerformance: CommercialPerformance;
  temporalPatterns: TemporalPatterns;
  memoryHealth: MemoryHealth;
  learningVelocity: LearningVelocity;
}

export interface RecentGeneration {
  id: string;
  timestamp: string;
  generationType: string;
  qualityScore: number;
  commercialSuccess?: boolean;
  userRating?: number;
}

export interface DesignEvolution {
  evolutionVelocity: number;
  consistencyTrend: string;
  innovationIndex: number;
  marketAlignment: number;
  trendDirection: string;
  strengthScore: number;
}

export interface CommercialPerformance {
  averageConversionRate: number;
  revenueTrend: string;
  topPerformingStyles: string[];
  engagementMetrics: EngagementMetrics;
}

export interface EngagementMetrics {
  averageTimeOnPage: number;
  bounceRate: number;
  socialShares: number;
  repeatPurchaseRate?: number;
}

export interface TemporalPatterns {
  seasonalCycles: string[];
  trendCycles: string[];
  innovationRhythm: string;
  consistencyPatterns: string;
}

export interface MemoryHealth {
  overallHealth: number;
  nodeCount: number;
  recentActivity: number;
  recommendations: string[];
}

export interface LearningVelocity {
  feedbackRate: number;
  improvementTrend: number;
  learningVelocity: number;
  velocityCategory: string;
}

// Commercial Prediction Types
export interface PredictionResults {
  conversionPrediction: ConversionPrediction;
  engagementPrediction: EngagementPrediction;
  marketFitAnalysis: MarketFitAnalysis;
  pricingRecommendations: PricingRecommendations;
  demographicInsights: DemographicInsights;
  competitiveAnalysis: CompetitiveAnalysis;
  riskAssessment: RiskAssessment;
}

export interface ConversionPrediction {
  predictedRate: number;
  confidenceInterval: [number, number];
  factorsInfluencing: InfluenceFactor[];
  seasonalAdjustment: number;
  trendAlignment: number;
}

export interface InfluenceFactor {
  factor: string;
  impact: number;
  confidence: number;
  description: string;
}

export interface EngagementPrediction {
  expectedEngagementRate: number;
  socialSharePotential: number;
  timeOnPagePrediction: number;
  viralityScore: number;
}

export interface MarketFitAnalysis {
  overallFitScore: number;
  targetMarketAlignment: number;
  competitivePositioning: number;
  uniquenessScore: number;
  marketGapOpportunity: number;
}

export interface PricingRecommendations {
  optimalPricePoint: number;
  priceElasticity: number;
  competitivePricing: CompetitivePricing;
  valuePerception: number;
  marginOptimization: MarginOptimization;
}

export interface CompetitivePricing {
  averageMarketPrice: number;
  pricePosition: string; // 'premium' | 'competitive' | 'value'
  competitorRange: PriceRange;
}

export interface MarginOptimization {
  recommendedMargin: number;
  volumeImpact: number;
  profitMaximization: number;
}

export interface DemographicInsights {
  primaryDemographic: Demographic;
  secondaryDemographics: Demographic[];
  demographicFit: number;
  expansionOpportunities: string[];
}

export interface Demographic {
  ageRange: string;
  gender: string;
  incomeLevel: string;
  lifestyle: string[];
  purchaseBehavior: PurchaseBehavior;
}

export interface PurchaseBehavior {
  frequency: string;
  seasonality: string[];
  pricesensitivity: number;
  brandLoyalty: number;
  channelPreferences: string[];
}

export interface CompetitiveAnalysis {
  competitiveAdvantage: string[];
  marketThreats: string[];
  differentiationScore: number;
  competitorComparison: CompetitorComparison[];
}

export interface CompetitorComparison {
  competitorName: string;
  similarityScore: number;
  strengthsVsCompetitor: string[];
  weaknessesVsCompetitor: string[];
}

export interface RiskAssessment {
  overallRisk: string; // 'low' | 'medium' | 'high'
  riskFactors: RiskFactor[];
  mitigationStrategies: string[];
  confidenceLevel: number;
}

export interface RiskFactor {
  factor: string;
  riskLevel: string;
  probability: number;
  impact: number;
  description: string;
}

// UI Component Props Types
export interface DemoInterfaceProps {
  brandConfig: BrandConfig;
  showKSECapabilities?: boolean;
  enableCommercialPredictions?: boolean;
}

export interface MultiModalInputPanelProps {
  inputs: MultiModalInputs;
  onInputChange: (inputs: Partial<MultiModalInputs>) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  brandConfig: BrandConfig;
}

export interface GenerationViewerProps {
  currentGeneration: CurrentGeneration | null;
  generationHistory: GenerationResults[];
  onFeedback: (generationId: string, feedback: FeedbackData) => void;
  brandTheme: BrandTheme;
}

export interface CurrentGeneration {
  taskId: string;
  status: GenerationStatus;
  progress: number;
  results?: GenerationResults;
}

export interface FeedbackData {
  rating: number;
  comments?: string;
  commercialOutcomes?: CommercialOutcomes;
  specificAspects?: Record<string, number>;
  improvementSuggestions?: string[];
}

export interface CommercialOutcomes {
  wouldPurchase: boolean;
  priceExpectation: number;
  targetMarketFit: number;
  conversionRate?: number;
  revenue?: number;
  userEngagement?: Record<string, any>;
}

export interface MemoryInsightsPanelProps {
  brandId: string;
  showKSECapabilities: boolean;
}

export interface CommercialMetricsDisplayProps {
  predictions: PredictionResults | null;
  isLoading: boolean;
}

// Service Types
export interface GenerationServiceConfig {
  baseUrl: string;
  apiKey?: string;
  timeout: number;
  retryAttempts: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  timestamp: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  taskId: string;
  data: any;
  timestamp: string;
}

export interface GenerationStreamUpdate extends WebSocketMessage {
  type: 'generation_update';
  data: {
    status: GenerationStatus;
    progress: number;
    currentStep: string;
    outputsReady: number;
    totalOutputs: number;
    results?: GenerationResults;
    error?: string;
  };
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Event Types
export interface GenerationEvent {
  type: 'generation_started' | 'generation_completed' | 'generation_failed' | 'generation_cancelled';
  taskId: string;
  timestamp: string;
  data?: any;
}

export interface UserInteractionEvent {
  type: 'rating_submitted' | 'feedback_provided' | 'output_favorited' | 'output_shared';
  outputId: string;
  userId?: string;
  timestamp: string;
  data?: any;
}

// Configuration Types
export interface AppConfig {
  api: {
    baseUrl: string;
    timeout: number;
    retryAttempts: number;
  };
  websocket: {
    url: string;
    reconnectAttempts: number;
    reconnectDelay: number;
  };
  features: {
    kseMemory: boolean;
    commercialPredictions: boolean;
    realTimeUpdates: boolean;
    multiModalInputs: boolean;
  };
  ui: {
    theme: 'light' | 'dark' | 'auto';
    animations: boolean;
    notifications: boolean;
  };
}

// Export all types
export * from './brand';
export * from './generation';
export * from './memory';
export * from './commercial';