import { useState } from "react";
import { Button } from "@nous-research/ui/ui/components/button";
import { Typography } from "@/components/NouiTypography";
import { Switch } from "@nous-research/ui/ui/components/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Label } from "@/components/ui/label";
import { Brain, Zap, DollarSign, Settings2 } from "lucide-react";

interface MultiModelConfig {
  enabled: boolean;
  cost_optimization: boolean;
  quality_priority: boolean;
}

interface ModelCapability {
  name: string;
  provider: string;
  strengths: string[];
  weaknesses: string[];
  cost_per_1k_input: number;
  quality_rank: number;
  speed_rank: number;
}

export default function MultiModelPage() {
  const [config, setConfig] = useState<MultiModelConfig>({
    enabled: false,
    cost_optimization: true,
    quality_priority: false,
  });
  const models: ModelCapability[] = [
    // Sample data for demonstration
    {
      name: "claude-sonnet-4-20250514",
      provider: "anthropic",
      strengths: ["reasoning", "analysis", "coding", "research"],
      weaknesses: [],
      cost_per_1k_input: 3.0,
      quality_rank: 9,
      speed_rank: 4,
    },
    {
      name: "gpt-4o",
      provider: "openai",
      strengths: ["coding", "multimodal", "reasoning"],
      weaknesses: [],
      cost_per_1k_input: 5.0,
      quality_rank: 8,
      speed_rank: 3,
    },
    {
      name: "claude-haiku-4-20250514",
      provider: "anthropic",
      strengths: ["summarization", "general", "analysis"],
      weaknesses: ["reasoning", "complex_coding"],
      cost_per_1k_input: 0.25,
      quality_rank: 6,
      speed_rank: 2,
    },
  ];
  const [saving, setSaving] = useState(false);

  const saveConfig = async () => {
    setSaving(true);
    try {
      // TODO: Implement actual API call when backend is ready
      console.log("Saving config:", config);
      // await api.setConfig("multi_model", config);
    } catch (error) {
      console.error("Failed to save config:", error);
    } finally {
      setSaving(false);
    }
  };

  const getQualityColor = (rank: number) => {
    if (rank >= 9) return "bg-green-500";
    if (rank >= 7) return "bg-blue-500";
    if (rank >= 5) return "bg-yellow-500";
    return "bg-gray-500";
  };

  const getSpeedColor = (rank: number) => {
    if (rank <= 2) return "bg-green-500";
    if (rank <= 4) return "bg-blue-500";
    if (rank <= 6) return "bg-yellow-500";
    return "bg-gray-500";
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8">
        <Typography variant="xl" className="flex items-center gap-3">
          <Brain className="w-8 h-8" />
          Multi-Model Orchestration
        </Typography>
        <Typography variant="sm" className="text-muted-foreground mt-2">
          Automatically route tasks to the best AI model based on task type, complexity, and cost.
        </Typography>
      </div>

      {/* Configuration Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings2 className="w-5 h-5" />
            Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="enabled">Enable Multi-Model Routing</Label>
              <Typography variant="sm" className="text-muted-foreground">
                Automatically select the best model for each task
              </Typography>
            </div>
            <Switch
              id="enabled"
              checked={config.enabled}
              onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
            />
          </div>

          {config.enabled && (
            <>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="cost_optimization" className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4" />
                    Cost Optimization
                  </Label>
                  <Typography variant="sm" className="text-muted-foreground">
                    Prefer cheaper models when quality difference is minimal
                  </Typography>
                </div>
                <Switch
                  id="cost_optimization"
                  checked={config.cost_optimization}
                  onCheckedChange={(checked) => setConfig({ ...config, cost_optimization: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="quality_priority" className="flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Quality Priority
                  </Label>
                  <Typography variant="sm" className="text-muted-foreground">
                    Always select the highest-quality model regardless of cost
                  </Typography>
                </div>
                <Switch
                  id="quality_priority"
                  checked={config.quality_priority}
                  onCheckedChange={(checked) => setConfig({ ...config, quality_priority: checked })}
                />
              </div>
            </>
          )}

          <div className="pt-4">
            <Button onClick={saveConfig} disabled={saving}>
              {saving ? "Saving..." : "Save Configuration"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Model Capabilities Card */}
      <Card>
        <CardHeader>
          <CardTitle>Available Models</CardTitle>
        </CardHeader>
        <CardContent>
          {models[0] && (
            <div className="space-y-4">
              {models.map((model) => (
                <div
                  key={model.name}
                  className="border rounded-lg p-4 space-y-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <Typography variant="md" className="font-semibold">
                        {model.name}
                      </Typography>
                      <Typography variant="sm" className="text-muted-foreground">
                        {model.provider}
                      </Typography>
                    </div>
                    <div className="flex gap-2">
                      <Badge className="flex items-center gap-1">
                        <div className={`w-2 h-2 rounded-full ${getQualityColor(model.quality_rank)}`} />
                        Quality: {model.quality_rank}/10
                      </Badge>
                      <Badge className="flex items-center gap-1">
                        <div className={`w-2 h-2 rounded-full ${getSpeedColor(model.speed_rank)}`} />
                        Speed: {11 - model.speed_rank}/10
                      </Badge>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Typography variant="sm" className="font-medium text-muted-foreground mb-1">
                        Strengths
                      </Typography>
                      <div className="flex flex-wrap gap-1">
                        {model.strengths.map((strength) => (
                          <Badge key={strength} className="text-xs">
                            {strength}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <Typography variant="sm" className="font-medium text-muted-foreground mb-1">
                        Weaknesses
                      </Typography>
                      <div className="flex flex-wrap gap-1">
                        {model.weaknesses.length > 0 ? (
                          model.weaknesses.map((weakness: string) => (
                            <Badge key={weakness} className="text-xs bg-secondary">
                              {weakness}
                            </Badge>
                          ))
                        ) : (
                          <Typography variant="sm" className="text-muted-foreground">
                            None
                          </Typography>
                        )}
                      </div>
                    </div>
                  </div>

                  <div>
                    <Typography variant="sm" className="font-medium text-muted-foreground">
                      Cost: ${model.cost_per_1k_input}/1K input tokens
                    </Typography>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="mt-6 bg-muted/50">
        <CardHeader>
          <CardTitle className="text-base">How Multi-Model Routing Works</CardTitle>
        </CardHeader>
        <CardContent>
          <Typography variant="sm" className="space-y-2 text-muted-foreground">
            <p>
              <strong>Automatic Task Classification:</strong> Each request is analyzed to determine its type (research, coding, analysis, etc.).
            </p>
            <p>
              <strong>Intelligent Model Selection:</strong> The system selects the best model based on task type, cost, and quality requirements.
            </p>
            <p>
              <strong>Performance Learning:</strong> The system tracks model performance over time and optimizes routing decisions.
            </p>
            <p>
              <strong>Graceful Fallback:</strong> If a model fails, the system automatically retries with fallback models.
            </p>
          </Typography>
        </CardContent>
      </Card>
    </div>
  );
}
