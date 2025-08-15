import { useState } from "react";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Zap, FileText, Copy, CheckCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { PDFQAService } from "@/services/api";

const Summarize = () => {
  const [inputText, setInputText] = useState("");
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [summaryType, setSummaryType] = useState<
    "brief" | "detailed" | "bullet_points" | "micro" | "audience"
  >("brief");
  const [audience, setAudience] = useState<"general" | "professional">(
    "general"
  );
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const handleSummarize = async () => {
    if (!inputText.trim()) {
      toast({
        title: "Error",
        description: "Please enter text to summarize",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await PDFQAService.summarizeText(
        inputText,
        summaryType,
        summaryType === "audience" ? audience : undefined
      );

      if (response.success) {
        setSummary(response.summary);
        toast({
          title: "Success",
          description: "Summary generated successfully",
        });
      } else {
        throw new Error("Summarization failed");
      }
    } catch (error) {
      console.error("Summarization error:", error);
      toast({
        title: "Error",
        description: "Failed to generate summary. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(summary);
      setCopied(true);
      toast({
        title: "Copied!",
        description: "Summary copied to clipboard",
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to copy to clipboard",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Zap className="h-8 w-8 text-primary" />
            <h2 className="text-3xl font-bold">Text Summarization</h2>
          </div>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Transform long texts into concise, meaningful summaries with
            AI-powered analysis
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Input Text
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Paste your text here to summarize..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="min-h-[300px] resize-none"
              />

              <div className="space-y-3">
                <label className="text-sm font-medium">Summary Type:</label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { value: "brief", label: "Brief" },
                    { value: "detailed", label: "Detailed" },
                    { value: "bullet_points", label: "Bullet Points" },
                    { value: "micro", label: "Micro" },
                    { value: "audience", label: "Audience-Specific" },
                  ].map((type) => (
                    <Button
                      key={type.value}
                      variant={
                        summaryType === type.value ? "default" : "outline"
                      }
                      size="sm"
                      onClick={() => setSummaryType(type.value as any)}
                    >
                      {type.label}
                    </Button>
                  ))}
                </div>
              </div>

              {summaryType === "audience" && (
                <div className="space-y-3">
                  <label className="text-sm font-medium">
                    Target Audience:
                  </label>
                  <div className="flex gap-2">
                    {[
                      { value: "general", label: "General" },
                      { value: "professional", label: "Professional" },
                    ].map((aud) => (
                      <Button
                        key={aud.value}
                        variant={audience === aud.value ? "default" : "outline"}
                        size="sm"
                        onClick={() => setAudience(aud.value as any)}
                      >
                        {aud.label}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              <Button
                onClick={handleSummarize}
                disabled={isLoading || !inputText.trim()}
                className="w-full"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    Summarizing...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    Generate Summary
                  </div>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Output Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Generated Summary
                </div>
                {summary && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={copyToClipboard}
                    className="flex items-center gap-2"
                  >
                    {copied ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                    {copied ? "Copied!" : "Copy"}
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center h-[300px]">
                  <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                    <p className="text-muted-foreground">
                      Analyzing and summarizing text...
                    </p>
                  </div>
                </div>
              ) : summary ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-muted/50 min-h-[300px]">
                    <p className="whitespace-pre-wrap leading-relaxed">
                      {summary}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  <div className="text-center space-y-2">
                    <FileText className="h-12 w-12 mx-auto opacity-50" />
                    <p>Your summary will appear here</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Instructions */}
        <div className="mt-12 text-center">
          <Card className="max-w-4xl mx-auto">
            <CardContent className="pt-6">
              <h3 className="text-lg font-semibold mb-4">
                How to Use Text Summarization
              </h3>
              <div className="grid md:grid-cols-4 gap-6 text-sm">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      1
                    </div>
                  </div>
                  <h4 className="font-medium">Paste Your Text</h4>
                  <p className="text-muted-foreground">
                    Copy and paste any text content you want to summarize
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      2
                    </div>
                  </div>
                  <h4 className="font-medium">Choose Summary Type</h4>
                  <p className="text-muted-foreground">
                    Select from brief, detailed, bullet points, micro, or
                    audience-specific
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      3
                    </div>
                  </div>
                  <h4 className="font-medium">Set Audience (Optional)</h4>
                  <p className="text-muted-foreground">
                    For audience-specific summaries, choose general or
                    professional
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      4
                    </div>
                  </div>
                  <h4 className="font-medium">Get Summary</h4>
                  <p className="text-muted-foreground">
                    Click generate to get your AI-powered summary
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Summarize;
