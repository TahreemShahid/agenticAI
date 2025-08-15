import React from "react";
import { Header } from "@/components/Header";
import { PDFUploader } from "@/components/PDFUploader";
import { QuestionInput } from "@/components/QuestionInput";
import { AnswerDisplay } from "@/components/AnswerDisplay";
import { usePDFQA } from "@/hooks/usePDFQA";
import { useToast } from "@/hooks/use-toast";
import { FileText } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const Home = () => {
  const {
    uploadedFile,
    isUploading,
    isProcessing,
    currentAnswer,
    error,
    uploadFile,
    askQuestion,
    clearError,
    reset,
  } = usePDFQA();

  const { toast } = useToast();

  React.useEffect(() => {
    if (error) {
      toast({
        title: "Error",
        description: error,
        variant: "destructive",
      });
      clearError();
    }
  }, [error, toast, clearError]);

  // Handles file selection and clearing (null)
  const handleFileSelect = (file: File | null) => {
    if (file === null) {
      // Clear all related state on removal
      reset();
    } else {
      uploadFile(file);
    }
  };

  const handleQuestionSubmit = (question: string) => {
    askQuestion(question);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <FileText className="h-8 w-8 text-primary" />
            <h2 className="text-3xl font-bold">PDF Question & Answer</h2>
          </div>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Upload any PDF document and ask intelligent questions about its
            content. Get instant answers with supporting evidence from your
            documents.
          </p>
        </div>

        <div className="space-y-8">
          {/* PDF Upload Section */}
          <section>
            <PDFUploader
              onFileSelect={handleFileSelect}
              selectedFile={uploadedFile}
              isLoading={isUploading} // Only show loading during uploading
            />
          </section>

          {/* Question Input Section */}
          <section>
            <QuestionInput
              onSubmit={handleQuestionSubmit}
              isLoading={isProcessing}
              disabled={!uploadedFile} // Disable if no PDF loaded
            />
          </section>

          {/* Answer Display Section */}
          {(currentAnswer || isProcessing || error) && (
            <section>
              <AnswerDisplay
                answer={currentAnswer?.answer}
                sourceChunks={currentAnswer?.source_chunks}
                error={error}
                isLoading={isProcessing}
              />
            </section>
          )}
        </div>

        {/* Instructions Footer */}
        <footer className="mt-16 text-center">
          <Card className="max-w-4xl mx-auto">
            <CardContent className="pt-6">
              <h3 className="text-lg font-semibold mb-4">How to Use PDF Q&A</h3>
              <div className="grid md:grid-cols-3 gap-6 text-sm">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      1
                    </div>
                  </div>
                  <h4 className="font-medium">Upload PDF</h4>
                  <p className="text-muted-foreground">
                    Upload your PDF document to start analyzing
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      2
                    </div>
                  </div>
                  <h4 className="font-medium">Ask Questions</h4>
                  <p className="text-muted-foreground">
                    Type any question about the document content
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      3
                    </div>
                  </div>
                  <h4 className="font-medium">Get Answers</h4>
                  <p className="text-muted-foreground">
                    Receive AI-powered answers with source citations
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </footer>
      </div>
    </div>
  );
};

export default Home;
