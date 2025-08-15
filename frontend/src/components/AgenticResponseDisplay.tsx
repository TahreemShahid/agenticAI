import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Loader2, FileText, GitCompare, FileSearch, Bot } from 'lucide-react';
import { AgenticQueryResponse } from '@/services/api';

interface AgenticResponseDisplayProps {
  response: AgenticQueryResponse | null;
  isLoading: boolean;
  error: string | null;
}

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'summarization':
      return <FileText className="h-4 w-4" />;
    case 'comparison':
      return <GitCompare className="h-4 w-4" />;
    case 'rag':
      return <FileSearch className="h-4 w-4" />;
    default:
      return <Bot className="h-4 w-4" />;
  }
};

const getCategoryColor = (category: string) => {
  switch (category) {
    case 'summarization':
      return 'bg-blue-100 text-blue-800 hover:bg-blue-200';
    case 'comparison':
      return 'bg-green-100 text-green-800 hover:bg-green-200';
    case 'rag':
      return 'bg-purple-100 text-purple-800 hover:bg-purple-200';
    default:
      return 'bg-gray-100 text-gray-800 hover:bg-gray-200';
  }
};

const getCategoryLabel = (category: string) => {
  switch (category) {
    case 'summarization':
      return 'Summarization';
    case 'comparison':
      return 'Comparison';
    case 'rag':
      return 'Document Q&A';
    default:
      return category.charAt(0).toUpperCase() + category.slice(1);
  }
};

export const AgenticResponseDisplay: React.FC<AgenticResponseDisplayProps> = ({
  response,
  isLoading,
  error,
}) => {
  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="pt-6">
          <div className="flex items-center justify-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-lg">Processing your query...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full border-destructive">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-2 text-destructive">
            <Bot className="h-5 w-5" />
            <span className="font-medium">Error</span>
          </div>
          <p className="mt-2 text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!response) {
    return null;
  }

  const renderResult = () => {
    const { category, result } = response;

    switch (category) {
      case 'summarization':
        return (
          <div className="space-y-4">
            <div className="prose prose-sm max-w-none">
              <h4 className="text-lg font-semibold mb-2">Summary</h4>
              <div className="bg-muted/50 p-4 rounded-lg">
                <p className="whitespace-pre-wrap">{result.summary}</p>
              </div>
            </div>
          </div>
        );

      case 'comparison':
        return (
          <div className="space-y-4">
            <div className="prose prose-sm max-w-none">
              <h4 className="text-lg font-semibold mb-2">Comparison Result</h4>
              <div className="bg-muted/50 p-4 rounded-lg">
                <p className="whitespace-pre-wrap">{result.comparison}</p>
              </div>
            </div>
          </div>
        );

      case 'rag':
        if (result.requires_document) {
          return (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                <div className="flex items-start space-x-3">
                  <FileSearch className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900">Document Required</h4>
                    <p className="text-sm text-blue-700 mt-1">{result.message}</p>
                  </div>
                </div>
              </div>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <div className="prose prose-sm max-w-none">
              <h4 className="text-lg font-semibold mb-2">Document Answer</h4>
              <div className="bg-muted/50 p-4 rounded-lg">
                <p className="whitespace-pre-wrap">{result.answer || result.message}</p>
              </div>
            </div>
            
            {/* Source Chunks */}
            {result.source_chunks && result.source_chunks.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-lg font-semibold">Source Citations</h4>
                <div className="space-y-2">
                  {result.source_chunks.map((chunk: string, index: number) => (
                    <div key={index} className="bg-muted/30 p-3 rounded-lg">
                      <div className="flex items-start gap-2">
                        <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded-full">
                          {index + 1}
                        </span>
                        <p className="text-sm text-muted-foreground flex-1">
                          {chunk.length > 200 ? `${chunk.substring(0, 200)}...` : chunk}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Document Info */}
            {result.document && (
              <div className="bg-muted/30 p-3 rounded-lg">
                <h4 className="text-sm font-medium mb-1">Source Document</h4>
                <p className="text-sm text-muted-foreground">{result.document}</p>
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className="space-y-4">
            <div className="prose prose-sm max-w-none">
              <h4 className="text-lg font-semibold mb-2">Response</h4>
              <div className="bg-muted/50 p-4 rounded-lg">
                <pre className="whitespace-pre-wrap text-sm">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getCategoryIcon(response.category)}
            <CardTitle className="text-lg">
              {getCategoryLabel(response.category)}
            </CardTitle>
          </div>
          <div className="flex items-center space-x-2">
            <Badge className={getCategoryColor(response.category)}>
              {getCategoryLabel(response.category)}
            </Badge>
            <Badge variant="outline">
              {Math.round(response.confidence * 100)}% confidence
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Reasoning */}
        <div className="bg-muted/30 p-3 rounded-lg">
          <h4 className="text-sm font-medium mb-1">AI Reasoning</h4>
          <p className="text-sm text-muted-foreground">{response.reasoning}</p>
        </div>

        <Separator />

        {/* Result */}
        {renderResult()}

        {/* Original Query */}
        <div className="pt-4 border-t">
          <h4 className="text-sm font-medium mb-2">Original Query</h4>
          <p className="text-sm text-muted-foreground bg-muted/30 p-2 rounded">
            "{response.original_query}"
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
