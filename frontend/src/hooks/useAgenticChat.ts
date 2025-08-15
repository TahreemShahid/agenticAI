import { useState, useCallback, useRef, useEffect } from 'react';
import { PDFQAService, AgenticQueryResponse } from '@/services/api';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  category?: string;
  confidence?: number;
  reasoning?: string;
  sourceChunks?: string[];
  document?: string;
}

interface UseAgenticChatState {
  isProcessing: boolean;
  currentResponse: AgenticQueryResponse | null;
  error: string | null;
  uploadedFiles: File[];
  messageHistory: Message[];
  pdfReady: boolean;
}

export const useAgenticChat = () => {
  const [state, setState] = useState<UseAgenticChatState>({
    isProcessing: false,
    currentResponse: null,
    error: null,
    uploadedFiles: [],
    messageHistory: [],
    pdfReady: false,
  });

  const stateRef = useRef(state);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const processQuery = useCallback(async (query: string) => {
    setState(prev => ({ ...prev, isProcessing: true, error: null }));
    
    try {
      console.log('🧪 HOOK: Sending query:', query);
      
      const response = await PDFQAService.agenticQuery(query, {
        has_pdf: stateRef.current.pdfReady,
        message_count: stateRef.current.messageHistory.length
      });
      
      console.log('🧪 HOOK: Received response:', response);
      console.log('🧪 HOOK: Response success:', response.success);
      console.log('🧪 HOOK: Response answer:', response.result?.answer);
      
      if (!response.success) {
        throw new Error(`API returned success: false - ${response.result?.answer || 'Unknown error'}`);
      }
      
      setState(prev => ({
        ...prev,
        currentResponse: response,
        isProcessing: false,
      }));
    } catch (error) {
      console.error('🧪 HOOK: Query failed:', error);
      setState(prev => ({
        ...prev,
        isProcessing: false,
        error: error instanceof Error ? error.message : 'Query processing failed',
      }));
    }
  }, []);

  const uploadFiles = useCallback(async (files: File[]) => {
    setState(prev => ({ ...prev, error: null, isProcessing: true }));
    
    try {
      console.log('🧪 HOOK: Uploading files:', files.map(f => f.name));
      
      // Upload files using the simple upload endpoint
      const uploadPromises = files.map(file => PDFQAService.uploadPDF(file));
      const responses = await Promise.all(uploadPromises);
      
      const allSuccessful = responses.every(response => response.success);
      
      if (allSuccessful) {
        console.log('🧪 HOOK: All files uploaded successfully');
        setState(prev => ({
          ...prev,
          uploadedFiles: files, // Replace previous files
          currentResponse: null,
          pdfReady: true, // PDF is now ready for Q&A
          isProcessing: false,
        }));
      } else {
        throw new Error('Some files failed to upload');
      }
    } catch (error) {
      console.error('🧪 HOOK: Upload failed:', error);
      setState(prev => ({
        ...prev,
        isProcessing: false,
        pdfReady: false,
        error: error instanceof Error ? error.message : 'Upload failed',
      }));
    }
  }, []);

  const addMessage = useCallback((message: Message) => {
    console.log('🧪 HOOK: Adding message to history:', message);
    setState(prev => ({
      ...prev,
      messageHistory: [...prev.messageHistory, message]
    }));
  }, []);

  const clearHistory = useCallback(async () => {
    try {
      console.log('🧪 HOOK: Clearing history');
      // Clear backend state if endpoint exists
      try {
        await fetch('http://localhost:8000/api/memory/clear', { method: 'POST' });
      } catch (e) {
        console.warn('Could not clear backend memory:', e);
      }
      
      setState(prev => ({
        ...prev,
        messageHistory: [],
        currentResponse: null,
        uploadedFiles: [],
        pdfReady: false,
      }));
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const clearCurrentResponse = useCallback(() => {
    setState(prev => ({ ...prev, currentResponse: null }));
  }, []);

  const reset = useCallback(async () => {
    try {
      console.log('🧪 HOOK: Resetting all state');
      try {
        await fetch('http://localhost:8000/api/memory/clear', { method: 'POST' });
      } catch (e) {
        console.warn('Could not clear backend memory:', e);
      }
    } catch (error) {
      console.error('Failed to reset:', error);
    }

    setState({
      isProcessing: false,
      currentResponse: null,
      error: null,
      uploadedFiles: [],
      messageHistory: [],
      pdfReady: false,
    });
  }, []);

  return {
    ...state,
    processQuery,
    uploadFiles,
    addMessage,
    clearHistory,
    clearError,
    clearCurrentResponse,
    reset,
  };
};
