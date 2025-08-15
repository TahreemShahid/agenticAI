import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, X, FileText, Loader } from 'lucide-react';
import PDFQAService, { UploadAndQueryResponse, AgenticQueryResponse } from '../services/api';

interface Message {
  id: number;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  sources?: string[];
  reasoning?: string;
  attachedFiles?: string[];
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Welcome message on load
  useEffect(() => {
    setMessages([{
      id: Date.now(),
      type: 'bot',
      content: 'Hi, how can I assist you today?',
      timestamp: new Date(),
    }]);
  }, []);

  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    const pdfFiles = files.filter(file => file.type === 'application/pdf');

    if (pdfFiles.length !== files.length) {
      setError('Only PDF files are allowed');
      return;
    }

    setSelectedFiles(prev => [...prev, ...pdfFiles]);
    setError('');
    event.target.value = '';
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // ✅ FIXED: Enhanced message handler with proper response type handling
  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim() && selectedFiles.length === 0) return;

    if (!messageText.trim() && selectedFiles.length > 0) {
      setError('Please ask a question about the uploaded PDF(s)');
      return;
    }

    const userMessage: Message = {
      id: Date.now(),
      type: 'user',
      content: messageText,
      timestamp: new Date(),
      attachedFiles: selectedFiles.map(f => f.name)
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError('');

    try {
      if (selectedFiles.length > 0) {
        // Upload and query with session isolation
        const result: UploadAndQueryResponse = await PDFQAService.uploadAndQuery(selectedFiles, messageText);

        if (result.success) {
          // ✅ FIXED: Handle different response types for upload-and-query
          let botContent = '';
          const category = result.query_response?.category || 'unknown';
          
          if (category === 'summarization') {
            botContent = result.query_response?.result?.summary || 'No summary generated';
          } else if (category === 'comparison') {
            botContent = result.query_response?.result?.comparison || 'No comparison generated';
          } else {
            botContent = result.query_response?.result?.answer || result.query_response?.result?.message || 'No answer generated';
          }

          const botMessage: Message = {
            id: Date.now() + 1,
            type: 'bot',
            content: botContent,
            timestamp: new Date(),
            sources: result.query_response?.result?.sources || [],
            reasoning: result.query_response?.reasoning || ''
          };

          setMessages(prev => [...prev, botMessage]);
          setSelectedFiles([]);

          // Log success info
          if (result.processing_summary) {
            const summary = result.processing_summary;
            if (summary.newly_processed?.length > 0) {
              console.log(`📄 Newly processed: ${summary.newly_processed.join(', ')}`);
            }
            if (summary.reused_existing?.length > 0) {
              console.log(`♻️ Reused existing: ${summary.reused_existing.length} file(s)`);
            }
          }
        } else {
          throw new Error('Upload and query failed');
        }
      } else {
        // Regular agentic query without file upload
        const result: AgenticQueryResponse = await PDFQAService.agenticQuery(messageText);

        if (result.success) {
          // ✅ FIXED: Handle different response types for agentic-query
          let botContent = '';
          
          if (result.category === 'summarization') {
            botContent = result.result?.summary || 'No summary generated';
          } else if (result.category === 'comparison') {
            botContent = result.result?.comparison || 'No comparison generated';
          } else if (result.category === 'rag') {
            botContent = result.result?.answer || 'No answer generated';
          } else {
            botContent = result.result?.message || 'No response generated';
          }

          const botMessage: Message = {
            id: Date.now() + 1,
            type: 'bot',
            content: botContent,
            timestamp: new Date(),
            sources: result.result?.sources || [],
            reasoning: result.reasoning || ''
          };

          setMessages(prev => [...prev, botMessage]);
          console.log(`✅ ${result.category} processed successfully`);
        }
      }
    } catch (error) {
      console.error('Error processing message:', error);
      setError(error instanceof Error ? error.message : 'An error occurred');

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, there was an error processing your request. Please try again.',
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(inputValue);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <h1 className="text-xl font-semibold">AI Assistant</h1>
        <p className="text-sm text-gray-400">Upload PDFs, ask questions, get summaries & comparisons</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-3/4 rounded-lg p-3 ${
              message.type === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-200'
            }`}>
              {message.type === 'user' && message.attachedFiles?.length > 0 && (
                <div className="mb-2 text-xs opacity-75">
                  📎 {message.attachedFiles.join(', ')}
                </div>
              )}

              <div className="whitespace-pre-wrap">{message.content}</div>

              {message.type === 'bot' && message.sources?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <details className="text-xs text-gray-400">
                    <summary className="cursor-pointer font-medium">
                      Sources ({message.sources.length})
                    </summary>
                    <div className="mt-2 space-y-1">
                      {message.sources.map((source, index) => (
                        <div key={index} className="p-2 bg-gray-700 rounded text-xs">
                          {source}
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}

              <div className="text-xs opacity-50 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <Loader className="animate-spin h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-300">
                  {selectedFiles.length > 0
                    ? `Processing ${selectedFiles.length} file(s) and generating answer...`
                    : 'Thinking...'}
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="mx-4 mb-2 p-3 bg-red-900 border border-red-700 text-red-300 rounded-lg text-sm">
          {error}
          <button onClick={() => setError('')} className="ml-2 text-red-400 hover:text-red-200">
            ✕
          </button>
        </div>
      )}

      {/* Selected Files Display */}
      {selectedFiles.length > 0 && (
        <div className="mx-4 mb-2 p-3 bg-blue-900 border border-blue-700 rounded-lg">
          <div className="text-sm text-blue-200 font-medium mb-2">
            📎 {selectedFiles.length} file(s) will be uploaded and analyzed
          </div>
          {selectedFiles.map((file, index) => (
            <div key={index} className="flex items-center justify-between bg-gray-800 p-2 rounded border border-gray-700">
              <span className="text-sm text-gray-200">
                {file.name.length > 30 ? `${file.name.substring(0, 30)}...` : file.name}
              </span>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-400">
                  {(file.size / 1024).toFixed(1)}KB
                </span>
                <button onClick={() => removeFile(index)} className="text-red-400 hover:text-red-200 p-1">
                  <X className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="bg-gray-800 border-t border-gray-700 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf"
            multiple
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-2 text-gray-400 hover:text-gray-200 rounded-lg"
            disabled={isLoading}
            title="Upload PDF files"
          >
            <Paperclip className="h-5 w-5" />
          </button>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={selectedFiles.length > 0
              ? "Ask a question about the uploaded PDF(s)..."
              : "Type your message or upload a PDF..."}
            className="flex-1 border border-gray-700 bg-gray-900 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || (!inputValue.trim() && selectedFiles.length === 0)}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white p-2 rounded-lg"
            title="Send message"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
