import { useState } from "react";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GitCompare, FileText, Zap, Copy, CheckCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { PDFQAService } from "@/services/api";

const Compare = () => {
  const [text1, setText1] = useState("");
  const [text2, setText2] = useState("");
  const [comparison, setComparison] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [compareType, setCompareType] = useState<
    "similarities" | "differences" | "comprehensive"
  >("comprehensive");
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const handleCompare = async () => {
    if (!text1.trim() || !text2.trim()) {
      toast({
        title: "Error",
        description: "Please enter text in both fields to compare",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await PDFQAService.compareTexts(
        text1,
        text2,
        compareType
      );

      if (response.success) {
        setComparison(response.comparison);
        toast({
          title: "Success",
          description: "Text comparison completed successfully",
        });
      } else {
        throw new Error("Comparison failed");
      }
    } catch (error) {
      console.error("Comparison error:", error);
      toast({
        title: "Error",
        description: "Failed to compare texts. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(comparison);
      setCopied(true);
      toast({
        title: "Copied!",
        description: "Comparison copied to clipboard",
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

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <GitCompare className="h-8 w-8 text-primary" />
            <h2 className="text-3xl font-bold">AI Text Comparison</h2>
          </div>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Compare two texts and get detailed analysis of similarities,
            differences, and insights
          </p>
        </div>

        <div className="space-y-8">
          {/* Input Section */}
          <div className="grid lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Text A
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="Enter the first text to compare..."
                  value={text1}
                  onChange={(e) => setText1(e.target.value)}
                  className="min-h-[250px] resize-none"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Text B
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="Enter the second text to compare..."
                  value={text2}
                  onChange={(e) => setText2(e.target.value)}
                  className="min-h-[250px] resize-none"
                />
              </CardContent>
            </Card>
          </div>

          {/* Controls */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Comparison Type:
                  </label>
                  <div className="flex gap-2">
                    {[
                      { value: "similarities", label: "Similarities" },
                      { value: "differences", label: "Differences" },
                      { value: "comprehensive", label: "Comprehensive" },
                    ].map((type) => (
                      <Button
                        key={type.value}
                        variant={
                          compareType === type.value ? "default" : "outline"
                        }
                        size="sm"
                        onClick={() => setCompareType(type.value as any)}
                      >
                        {type.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <Button
                  onClick={handleCompare}
                  disabled={isLoading || !text1.trim() || !text2.trim()}
                  size="lg"
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                      Comparing...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <GitCompare className="h-4 w-4" />
                      Compare Texts
                    </div>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Results Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Comparison Results
                </div>
                {comparison && (
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
                      Analyzing and comparing texts...
                    </p>
                  </div>
                </div>
              ) : comparison ? (
                <div className="space-y-4">
                  <div className="p-6 rounded-lg bg-muted/50 min-h-[300px]">
                    <p className="whitespace-pre-wrap leading-relaxed">
                      {comparison}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  <div className="text-center space-y-2">
                    <GitCompare className="h-12 w-12 mx-auto opacity-50" />
                    <p>Your comparison results will appear here</p>
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
                How to Use AI Text Comparison
              </h3>
              <div className="grid md:grid-cols-4 gap-6 text-sm">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      1
                    </div>
                  </div>
                  <h4 className="font-medium">Input Texts</h4>
                  <p className="text-muted-foreground">
                    Enter two texts you want to compare
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      2
                    </div>
                  </div>
                  <h4 className="font-medium">Choose Analysis</h4>
                  <p className="text-muted-foreground">
                    Select comparison type: similarities, differences, or
                    comprehensive
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      3
                    </div>
                  </div>
                  <h4 className="font-medium">AI Analysis</h4>
                  <p className="text-muted-foreground">
                    Get detailed AI-powered comparison
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      4
                    </div>
                  </div>
                  <h4 className="font-medium">Review Results</h4>
                  <p className="text-muted-foreground">
                    Copy or save the comparison insights
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

export default Compare;
