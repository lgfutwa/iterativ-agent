import { useState } from "react";
import { Button } from "@nous-research/ui/ui/components/button";
import { Typography } from "@/components/NouiTypography";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@nous-research/ui/ui/components/switch";
import { 
  Sparkles, 
  KeyRound, 
  Cpu, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft,
  Zap,
  Brain,
  Globe
} from "lucide-react";

type WizardStep = "welcome" | "api-keys" | "model-selection" | "preferences" | "complete";

export default function SetupWizard() {
  const [currentStep, setCurrentStep] = useState<WizardStep>("welcome");
  const [config, setConfig] = useState({
    anthropicApiKey: "",
    openaiApiKey: "",
    defaultModel: "claude-sonnet-4-20250514",
    enableMultiModel: true,
    enableWorkflow: true,
    enableBrowser: true,
  });

  const steps: WizardStep[] = ["welcome", "api-keys", "model-selection", "preferences", "complete"];
  const currentStepIndex = steps.indexOf(currentStep);

  const nextStep = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStep(steps[currentStepIndex + 1]);
    }
  };

  const prevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStep(steps[currentStepIndex - 1]);
    }
  };

  const handleComplete = () => {
    console.log("Setup complete with config:", config);
    // TODO: Save configuration to backend
  };

  const renderStep = () => {
    switch (currentStep) {
      case "welcome":
        return (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <Typography variant="xl" className="mb-4">
              Welcome to Iterativ Agent
            </Typography>
            <Typography variant="sm" className="text-muted-foreground max-w-md mx-auto mb-8">
              Your intelligent AI assistant with multi-model orchestration, workflow automation, and browser capabilities. Let's get you set up in a few quick steps.
            </Typography>
            <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto mb-8">
              <div className="text-center">
                <Brain className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                <Typography variant="sm" className="font-medium">Multi-Model</Typography>
              </div>
              <div className="text-center">
                <Globe className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                <Typography variant="sm" className="font-medium">Browser</Typography>
              </div>
              <div className="text-center">
                <Zap className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
                <Typography variant="sm" className="font-medium">Workflows</Typography>
              </div>
            </div>
          </div>
        );

      case "api-keys":
        return (
          <div className="py-4">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <KeyRound className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <Typography variant="lg" className="font-semibold">
                  API Keys
                </Typography>
                <Typography variant="sm" className="text-muted-foreground">
                  Add your API keys to enable AI models
                </Typography>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <Label htmlFor="anthropic-key">Anthropic API Key</Label>
                <Input
                  id="anthropic-key"
                  type="password"
                  placeholder="sk-ant-..."
                  value={config.anthropicApiKey}
                  onChange={(e) => setConfig({ ...config, anthropicApiKey: e.target.value })}
                  className="mt-1"
                />
                <Typography variant="sm" className="text-muted-foreground mt-1">
                  Required for Claude models
                </Typography>
              </div>
              <div>
                <Label htmlFor="openai-key">OpenAI API Key</Label>
                <Input
                  id="openai-key"
                  type="password"
                  placeholder="sk-..."
                  value={config.openaiApiKey}
                  onChange={(e) => setConfig({ ...config, openaiApiKey: e.target.value })}
                  className="mt-1"
                />
                <Typography variant="sm" className="text-muted-foreground mt-1">
                  Optional - for GPT models
                </Typography>
              </div>
            </div>
          </div>
        );

      case "model-selection":
        return (
          <div className="py-4">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <Cpu className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <Typography variant="lg" className="font-semibold">
                  Default Model
                </Typography>
                <Typography variant="sm" className="text-muted-foreground">
                  Choose your preferred AI model
                </Typography>
              </div>
            </div>
            <div className="space-y-3">
              {[
                { id: "claude-sonnet-4-20250514", name: "Claude Sonnet 4", description: "Balanced performance for most tasks" },
                { id: "claude-opus-4-20250514", name: "Claude Opus 4", description: "Highest quality for complex reasoning" },
                { id: "claude-haiku-4-20250514", name: "Claude Haiku 4", description: "Fast and cost-effective for simple tasks" },
                { id: "gpt-4o", name: "GPT-4o", description: "Multimodal capabilities with strong coding" },
              ].map((model) => (
                <div
                  key={model.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    config.defaultModel === model.id
                      ? "border-purple-500 bg-purple-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                  onClick={() => setConfig({ ...config, defaultModel: model.id })}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <Typography variant="md" className="font-medium">
                        {model.name}
                      </Typography>
                      <Typography variant="sm" className="text-muted-foreground">
                        {model.description}
                      </Typography>
                    </div>
                    {config.defaultModel === model.id && (
                      <CheckCircle2 className="w-5 h-5 text-purple-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case "preferences":
        return (
          <div className="py-4">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                <Zap className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <Typography variant="lg" className="font-semibold">
                  Preferences
                </Typography>
                <Typography variant="sm" className="text-muted-foreground">
                  Customize your experience
                </Typography>
              </div>
            </div>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Typography variant="md" className="font-medium">
                    Multi-Model Orchestration
                  </Typography>
                  <Typography variant="sm" className="text-muted-foreground">
                    Automatically route tasks to the best model
                  </Typography>
                </div>
                <Switch
                  checked={config.enableMultiModel}
                  onCheckedChange={(checked) => setConfig({ ...config, enableMultiModel: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Typography variant="md" className="font-medium">
                    Workflow Automation
                  </Typography>
                  <Typography variant="sm" className="text-muted-foreground">
                    Enable automatic task decomposition
                  </Typography>
                </div>
                <Switch
                  checked={config.enableWorkflow}
                  onCheckedChange={(checked) => setConfig({ ...config, enableWorkflow: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Typography variant="md" className="font-medium">
                    Browser Automation
                  </Typography>
                  <Typography variant="sm" className="text-muted-foreground">
                    Enable web browsing capabilities
                  </Typography>
                </div>
                <Switch
                  checked={config.enableBrowser}
                  onCheckedChange={(checked) => setConfig({ ...config, enableBrowser: checked })}
                />
              </div>
            </div>
          </div>
        );

      case "complete":
        return (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-8 h-8 text-green-600" />
            </div>
            <Typography variant="xl" className="mb-4">
              You're All Set!
            </Typography>
            <Typography variant="sm" className="text-muted-foreground max-w-md mx-auto mb-8">
              Iterativ Agent is now configured and ready to help you with your tasks. Start by typing a message or exploring the available features.
            </Typography>
            <div className="space-y-2 max-w-md mx-auto text-left">
              <Typography variant="sm" className="font-medium">
                Quick tips:
              </Typography>
              <Typography variant="sm" className="text-muted-foreground">
                • Use <span className="font-mono bg-muted px-1 rounded">/help</span> to see available commands
              </Typography>
              <Typography variant="sm" className="text-muted-foreground">
                • Check the <span className="font-mono bg-muted px-1 rounded">Workflows</span> page for complex tasks
              </Typography>
              <Typography variant="sm" className="text-muted-foreground">
                • Configure multi-model routing in <span className="font-mono bg-muted px-1 rounded">Settings</span>
              </Typography>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between mb-4">
            <CardTitle className="text-lg">Setup Wizard</CardTitle>
            <Typography variant="sm" className="text-muted-foreground">
              Step {currentStepIndex + 1} of {steps.length}
            </Typography>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-purple-500 h-2 rounded-full transition-all"
              style={{ width: `${((currentStepIndex + 1) / steps.length) * 100}%` }}
            />
          </div>
        </CardHeader>
        <CardContent>
          {renderStep()}
          
          <div className="flex justify-between mt-8 pt-6 border-t">
            {currentStep !== "welcome" && currentStep !== "complete" && (
              <Button onClick={prevStep}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
            )}
            {currentStep === "welcome" && <div />}
            
            {currentStep !== "complete" ? (
              <Button onClick={nextStep}>
                {currentStep === "preferences" ? "Complete Setup" : "Next"}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <Button onClick={handleComplete}>
                Start Using Iterativ
                <Zap className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
