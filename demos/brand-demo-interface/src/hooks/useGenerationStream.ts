/**
 * Real-time generation streaming hook
 * Provides WebSocket-based updates for generation progress and results
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { GenerationStatus, GenerationResults } from '../types';

interface GenerationStreamState {
  status: GenerationStatus | null;
  results: GenerationResults | null;
  progress: number;
  currentStep: string | null;
  error: string | null;
  outputsReady: number;
  totalOutputs: number;
  isConnected: boolean;
}

interface GenerationStreamUpdate {
  taskId: string;
  status: GenerationStatus;
  progress?: number;
  currentStep?: string;
  outputsReady?: number;
  totalOutputs?: number;
  results?: GenerationResults;
  error?: string;
  timestamp: string;
}

export const useGenerationStream = (taskId: string | null) => {
  const [state, setState] = useState<GenerationStreamState>({
    status: null,
    results: null,
    progress: 0,
    currentStep: null,
    error: null,
    outputsReady: 0,
    totalOutputs: 0,
    isConnected: false
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // WebSocket connection management
  const connect = useCallback((taskId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    const wsUrl = `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/ws/generation/${taskId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log(`WebSocket connected for task ${taskId}`);
      setState(prev => ({ ...prev, isConnected: true, error: null }));
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const update: GenerationStreamUpdate = JSON.parse(event.data);
        
        if (update.error) {
          setState(prev => ({
            ...prev,
            error: update.error!,
            status: GenerationStatus.FAILED,
            isConnected: true
          }));
          return;
        }

        setState(prev => ({
          ...prev,
          status: update.status,
          progress: update.progress ?? prev.progress,
          currentStep: update.currentStep ?? prev.currentStep,
          outputsReady: update.outputsReady ?? prev.outputsReady,
          totalOutputs: update.totalOutputs ?? prev.totalOutputs,
          results: update.results ?? prev.results,
          isConnected: true,
          error: null
        }));

        // Log progress updates
        if (update.progress !== undefined) {
          console.log(`Generation ${taskId}: ${Math.round(update.progress * 100)}% - ${update.currentStep || 'Processing...'}`);
        }

      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
        setState(prev => ({
          ...prev,
          error: 'Failed to parse server message'
        }));
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setState(prev => ({
        ...prev,
        error: 'Connection error',
        isConnected: false
      }));
    };

    ws.onclose = (event) => {
      console.log(`WebSocket closed for task ${taskId}:`, event.code, event.reason);
      setState(prev => ({ ...prev, isConnected: false }));

      // Attempt to reconnect if not a clean close and we haven't exceeded max attempts
      if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000); // Exponential backoff
        reconnectAttempts.current++;
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          if (taskId) {
            connect(taskId);
          }
        }, delay);
      } else if (reconnectAttempts.current >= maxReconnectAttempts) {
        setState(prev => ({
          ...prev,
          error: 'Connection failed after multiple attempts'
        }));
      }
    };

    wsRef.current = ws;
  }, []);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }

    setState({
      status: null,
      results: null,
      progress: 0,
      currentStep: null,
      error: null,
      outputsReady: 0,
      totalOutputs: 0,
      isConnected: false
    });
  }, []);

  // Effect to manage WebSocket connection
  useEffect(() => {
    if (taskId) {
      connect(taskId);
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [taskId, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Manual reconnect function
  const reconnect = useCallback(() => {
    if (taskId) {
      reconnectAttempts.current = 0;
      connect(taskId);
    }
  }, [taskId, connect]);

  return {
    ...state,
    reconnect
  };
};

export default useGenerationStream;