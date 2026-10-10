import { useEffect, useState, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WorkflowEvent, Generation } from '../api/types';

interface UseGenerationStreamProps {
  generationId: string;
  enabled: boolean;
  onEvent?: (event: WorkflowEvent) => void;
  onComplete?: (generation: Generation) => void;
  onError?: (error: string) => void;
}

export function useGenerationStream({
  generationId,
  enabled,
  onEvent,
  onComplete,
  onError,
}: UseGenerationStreamProps) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [lastEvent, setLastEvent] = useState<WorkflowEvent | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const maxRetries = 5;
  const queryClient = useQueryClient();

  const connect = useCallback(() => {
    if (!enabled || !generationId) return;

    const base = import.meta.env.VITE_API_BASE_URL || '';
    const url = `${base}/api/generations/${generationId}/events`;

    try {
      const es = new EventSource(url);
      eventSourceRef.current = es;
      setIsStreaming(true);
      setIsReconnecting(false);

      es.onmessage = (e) => {
        try {
          const parsed: WorkflowEvent = JSON.parse(e.data);
          setLastEvent(parsed);
          onEvent?.(parsed);

          // Invalidate generations query cache to reflect changes
          queryClient.invalidateQueries({ queryKey: ['generation', generationId] });
          queryClient.invalidateQueries({ queryKey: ['generations'] });

          if (parsed.event_type === 'completed') {
            setIsStreaming(false);
            es.close();
            // Refetch full generation record
            queryClient.refetchQueries({ queryKey: ['generation', generationId] }).then((res: any) => {
              if (res.data) onComplete?.(res.data);
            });
          } else if (parsed.event_type === 'failed') {
            setIsStreaming(false);
            es.close();
            onError?.(parsed.message || 'Generation failed');
          }
        } catch (err) {
          console.error('Failed to parse SSE event data', err);
        }
      };

      // Custom event listeners matching backend event types
      const handleCustomEvent = (eventType: string) => (e: MessageEvent) => {
        try {
          const parsed: WorkflowEvent = JSON.parse(e.data);
          setLastEvent(parsed);
          onEvent?.(parsed);
          queryClient.invalidateQueries({ queryKey: ['generation', generationId] });

          if (eventType === 'completed') {
            setIsStreaming(false);
            es.close();
            queryClient.refetchQueries({ queryKey: ['generation', generationId] }).then((res: any) => {
              if (res.data) onComplete?.(res.data);
            });
          } else if (eventType === 'failed') {
            setIsStreaming(false);
            es.close();
            onError?.(parsed.message || 'Workflow stage failed');
          }
        } catch (err) {
          console.error(`Error handling event ${eventType}`, err);
        }
      };

      es.addEventListener('stage', handleCustomEvent('stage'));
      es.addEventListener('completed', handleCustomEvent('completed'));
      es.addEventListener('failed', handleCustomEvent('failed'));
      es.addEventListener('interrupted', handleCustomEvent('interrupted'));
      es.addEventListener('warning', handleCustomEvent('warning'));

      es.onerror = () => {
        es.close();
        setIsStreaming(false);

        if (retryCountRef.current < maxRetries) {
          setIsReconnecting(true);
          const backoff = Math.min(1000 * Math.pow(2, retryCountRef.current), 10000) + Math.random() * 500;
          retryCountRef.current += 1;
          setTimeout(() => {
            connect();
          }, backoff);
        } else {
          setIsReconnecting(false);
          // Fall back to polling
          queryClient.invalidateQueries({ queryKey: ['generation', generationId] });
        }
      };
    } catch (e: any) {
      console.error('SSE initialization error:', e);
      setIsStreaming(false);
    }
  }, [generationId, enabled, onEvent, onComplete, onError, queryClient]);

  useEffect(() => {
    if (enabled && generationId) {
      retryCountRef.current = 0;
      connect();
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setIsStreaming(false);
      setIsReconnecting(false);
    };
  }, [generationId, enabled, connect]);

  return {
    isStreaming,
    isReconnecting,
    lastEvent,
    disconnect: () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setIsStreaming(false);
      setIsReconnecting(false);
    },
  };
}
