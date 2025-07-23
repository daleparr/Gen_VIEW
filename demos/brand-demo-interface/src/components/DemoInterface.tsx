/**
 * GEN-VIEW-KSE Demo Interface
 * Brand-agnostic demo interface with multi-modal input support and real-time generation streaming
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Box, Container, Grid, Paper, Typography, Alert, Snackbar } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';

import { BrandThemeProvider, BrandTheme } from './BrandThemeProvider';
import { MultiModalInputPanel } from './MultiModalInputPanel';
import { GenerationViewer } from './GenerationViewer';
import { MemoryInsightsPanel } from './MemoryInsightsPanel';
import { CommercialMetricsDisplay } from './CommercialMetricsDisplay';
import { useGenerationStream } from '../hooks/useGenerationStream';
import { GenerationService } from '../services/generationService';
import { 
  MultiModalInputs, 
  GenerationRequest, 
  GenerationStatus, 
  GenerationResults,
  PredictionResults,
  BrandConfig
} from '../types';

interface DemoInterfaceProps {
  brandConfig: BrandConfig;
  showKSECapabilities?: boolean;
  enableCommercialPredictions?: boolean;
}

export const DemoInterface: React.FC<DemoInterfaceProps> = ({
  brandConfig,
  showKSECapabilities = true,
  enableCommercialPredictions = true
}) => {
  // State management
  const [inputs, setInputs] = useState<MultiModalInputs>({
    textPrompt: '',
    referenceImages: [],
    sketchInputs: [],
    colorPalette: [],
    materialPreferences: [],
    styleVectors: []
  });
  
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [generationHistory, setGenerationHistory] = useState<GenerationResults[]>([]);
  const [predictions, setPredictions] = useState<PredictionResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  // Real-time generation streaming
  const { status, results, progress, error: streamError } = useGenerationStream(currentTaskId);

  // Services
  const generationService = new GenerationService();

  // Handle input changes
  const handleInputChange = useCallback((newInputs: Partial<MultiModalInputs>) => {
    setInputs(prev => ({ ...prev, ...newInputs }));
  }, []);

  // Handle generation request
  const handleGenerate = useCallback(async () => {
    if (!inputs.textPrompt && inputs.referenceImages.length === 0) {
      setError('Please provide either a text prompt or reference images');
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);

      const generationRequest: GenerationRequest = {
        name: `Generation ${Date.now()}`,
        inputs: {
          textPrompt: inputs.textPrompt,
          referenceImages: inputs.referenceImages,
          sketchInputs: inputs.sketchInputs,
          colorPalette: inputs.colorPalette,
          materialPreferences: inputs.materialPreferences,
          styleVectors: inputs.styleVectors,
          brandContext: {
            brandId: brandConfig.id,
            designDNA: brandConfig.designDNA,
            guidelines: brandConfig.guidelines
          }
        },
        brandParameters: {
          brandId: brandConfig.id,
          designDnaAdherence: 0.8,
          targetDemographic: brandConfig.targetDemographic,
          pricePoint: brandConfig.pricePoint,
          sustainabilityRequirements: brandConfig.sustainabilityRequirements
        },
        targetPieces: 5,
        qualityLevel: 'high',
        creativityLevel: 0.7,
        useMemoryContext: showKSECapabilities,
        memoryDepth: 5,
        optimizeForCommercial: enableCommercialPredictions
      };

      const response = await generationService.generateCapsuleCollection(generationRequest);
      setCurrentTaskId(response.taskId);

      // Generate commercial predictions if enabled
      if (enableCommercialPredictions) {
        const predictionResults = await generationService.predictCommercialSuccess(
          inputs,
          brandConfig
        );
        setPredictions(predictionResults);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      setIsGenerating(false);
    }
  }, [inputs, brandConfig, showKSECapabilities, enableCommercialPredictions, generationService]);

  // Handle generation completion
  useEffect(() => {
    if (status === GenerationStatus.COMPLETED && results) {
      setGenerationHistory(prev => [results, ...prev.slice(0, 9)]); // Keep last 10
      setIsGenerating(false);
      setCurrentTaskId(null);
    } else if (status === GenerationStatus.FAILED) {
      setIsGenerating(false);
      setError(streamError || 'Generation failed');
      setCurrentTaskId(null);
    }
  }, [status, results, streamError]);

  // Handle feedback submission
  const handleFeedback = useCallback(async (
    generationId: string,
    feedback: {
      rating: number;
      comments?: string;
      commercialOutcomes?: any;
    }
  ) => {
    try {
      await generationService.submitFeedback(generationId, feedback);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  }, [generationService]);

  return (
    <BrandThemeProvider theme={brandConfig.theme}>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Typography 
          variant="h3" 
          component="h1" 
          gutterBottom 
          sx={{ 
            mb: 4, 
            fontWeight: 'bold',
            color: 'primary.main',
            textAlign: 'center'
          }}
        >
          {brandConfig.name} Design Studio
        </Typography>

        <Grid container spacing={3}>
          {/* Input Panel */}
          <Grid item xs={12} lg={4}>
            <Paper elevation={3} sx={{ p: 3, height: 'fit-content' }}>
              <Typography variant="h5" gutterBottom>
                Design Inputs
              </Typography>
              <MultiModalInputPanel
                inputs={inputs}
                onInputChange={handleInputChange}
                onGenerate={handleGenerate}
                isGenerating={isGenerating}
                brandConfig={brandConfig}
              />
            </Paper>
          </Grid>

          {/* Generation Viewer */}
          <Grid item xs={12} lg={8}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Generated Designs
              </Typography>
              <GenerationViewer
                currentGeneration={
                  currentTaskId ? {
                    taskId: currentTaskId,
                    status,
                    progress,
                    results
                  } : null
                }
                generationHistory={generationHistory}
                onFeedback={handleFeedback}
                brandTheme={brandConfig.theme}
              />
            </Paper>
          </Grid>

          {/* KSE Memory Insights */}
          {showKSECapabilities && (
            <Grid item xs={12} lg={6}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h5" gutterBottom>
                  KSE Memory Insights
                </Typography>
                <MemoryInsightsPanel
                  brandId={brandConfig.id}
                  showKSECapabilities={showKSECapabilities}
                />
              </Paper>
            </Grid>
          )}

          {/* Commercial Metrics */}
          {enableCommercialPredictions && (
            <Grid item xs={12} lg={showKSECapabilities ? 6 : 12}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h5" gutterBottom>
                  Commercial Predictions
                </Typography>
                <CommercialMetricsDisplay
                  predictions={predictions}
                  isLoading={isGenerating}
                />
              </Paper>
            </Grid>
          )}

          {/* Generation Queue Status */}
          <Grid item xs={12}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" color="textSecondary">
                  {isGenerating ? (
                    `Generating... ${progress ? `${Math.round(progress * 100)}%` : ''}`
                  ) : (
                    `Ready for generation • History: ${generationHistory.length} items`
                  )}
                </Typography>
                {status && (
                  <Typography 
                    variant="body2" 
                    color={status === GenerationStatus.COMPLETED ? 'success.main' : 'primary.main'}
                  >
                    Status: {status}
                  </Typography>
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Error Snackbar */}
        <Snackbar
          open={!!error}
          autoHideDuration={6000}
          onClose={() => setError(null)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert 
            onClose={() => setError(null)} 
            severity="error" 
            sx={{ width: '100%' }}
          >
            {error}
          </Alert>
        </Snackbar>
      </Container>
    </BrandThemeProvider>
  );
};

export default DemoInterface;