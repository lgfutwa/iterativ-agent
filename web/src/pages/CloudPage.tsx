import { useState } from "react";
import { Button } from "@nous-research/ui/ui/components/button";
import { Typography } from "@/components/NouiTypography";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@nous-research/ui/ui/components/badge";
import {
  Cloud,
  Server,
  CheckCircle2,
  XCircle,
  Zap,
  Shield,
  DollarSign,
  Plus,
  Settings,
  RefreshCw,
} from "lucide-react";

interface CloudInstance {
  id: string;
  name: string;
  status: "running" | "stopped" | "error";
  region: string;
  type: string;
  cost_per_hour: number;
  uptime: string;
}

export default function CloudPage() {
  const [executionMode, setExecutionMode] = useState<"local" | "cloud">("local");
  const instances: CloudInstance[] = [
    {
      id: "inst1",
      name: "iterativ-prod-1",
      status: "running",
      region: "us-east-1",
      type: "t3.large",
      cost_per_hour: 0.12,
      uptime: "5d 12h",
    },
    {
      id: "inst2",
      name: "iterativ-dev-1",
      status: "stopped",
      region: "us-west-2",
      type: "t3.medium",
      cost_per_hour: 0.08,
      uptime: "-",
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case "stopped":
        return <XCircle className="w-4 h-4 text-gray-400" />;
      case "error":
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return <Badge className="bg-green-500">Running</Badge>;
      case "stopped":
        return <Badge className="bg-gray-400">Stopped</Badge>;
      case "error":
        return <Badge className="bg-red-500">Error</Badge>;
      default:
        return <Badge className="bg-gray-400">Unknown</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8">
        <Typography variant="xl" className="flex items-center gap-3">
          <Cloud className="w-8 h-8" />
          Cloud Execution
        </Typography>
        <Typography variant="sm" className="text-muted-foreground mt-2">
          Run Iterativ Agent in the cloud for better performance and scalability
        </Typography>
      </div>

      {/* Execution Mode Selection */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Execution Mode</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div
              className={`p-6 border rounded-lg cursor-pointer transition-colors ${
                executionMode === "local"
                  ? "border-purple-500 bg-purple-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
              onClick={() => setExecutionMode("local")}
            >
              <div className="flex items-center gap-3 mb-3">
                <Server className="w-6 h-6 text-blue-500" />
                <Typography variant="md" className="font-semibold">
                  Local Execution
                </Typography>
              </div>
              <Typography variant="sm" className="text-muted-foreground mb-3">
                Run Iterativ Agent on your local machine
              </Typography>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <Typography variant="sm">No cloud costs</Typography>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <Typography variant="sm">Full data privacy</Typography>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <Typography variant="sm">Limited by local resources</Typography>
                </div>
              </div>
            </div>

            <div
              className={`p-6 border rounded-lg cursor-pointer transition-colors ${
                executionMode === "cloud"
                  ? "border-purple-500 bg-purple-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
              onClick={() => setExecutionMode("cloud")}
            >
              <div className="flex items-center gap-3 mb-3">
                <Cloud className="w-6 h-6 text-purple-500" />
                <Typography variant="md" className="font-semibold">
                  Cloud Execution
                </Typography>
              </div>
              <Typography variant="sm" className="text-muted-foreground mb-3">
                Run Iterativ Agent on cloud infrastructure
              </Typography>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <Typography variant="sm">Scalable resources</Typography>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <Typography variant="sm">24/7 availability</Typography>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-yellow-500" />
                  <Typography variant="sm">Pay per usage</Typography>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cloud Instances */}
      {executionMode === "cloud" && (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Cloud Instances</CardTitle>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Instance
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {instances.map((instance) => (
                <div
                  key={instance.id}
                  className="p-4 border rounded-lg"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getStatusIcon(instance.status)}
                      <div>
                        <Typography variant="md" className="font-semibold">
                          {instance.name}
                        </Typography>
                        <Typography variant="sm" className="text-muted-foreground">
                          {instance.region} • {instance.type}
                        </Typography>
                      </div>
                    </div>
                    {getStatusBadge(instance.status)}
                  </div>
                  <div className="mt-4 grid grid-cols-3 gap-4">
                    <div>
                      <Typography variant="sm" className="font-medium text-muted-foreground">
                        Cost
                      </Typography>
                      <Typography variant="md">
                        ${instance.cost_per_hour}/hour
                      </Typography>
                    </div>
                    <div>
                      <Typography variant="sm" className="font-medium text-muted-foreground">
                        Uptime
                      </Typography>
                      <Typography variant="md">
                        {instance.uptime}
                      </Typography>
                    </div>
                    <div>
                      <Typography variant="sm" className="font-medium text-muted-foreground">
                        Actions
                      </Typography>
                      <div className="flex gap-2 mt-1">
                        <Button size="sm">
                          <Settings className="w-3 h-3 mr-1" />
                          Config
                        </Button>
                        <Button size="sm">
                          <RefreshCw className="w-3 h-3 mr-1" />
                          Restart
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Features Comparison */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Features Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Feature</th>
                  <th className="text-center py-3 px-4">Local</th>
                  <th className="text-center py-3 px-4">Cloud</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-yellow-500" />
                      Performance
                    </div>
                  </td>
                  <td className="text-center py-3 px-4">
                    <Typography variant="sm">Limited by hardware</Typography>
                  </td>
                  <td className="text-center py-3 px-4">
                    <Typography variant="sm">Scalable</Typography>
                  </td>
                </tr>
                <tr className="border-b">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Shield className="w-4 h-4 text-blue-500" />
                      Data Privacy
                    </div>
                  </td>
                  <td className="text-center py-3 px-4">
                    <Typography variant="sm">Full control</Typography>
                  </td>
                  <td className="text-center py-3 px-4">
                    <Typography variant="sm">Encrypted at rest</Typography>
                  </td>
                </tr>
                <tr className="border-b">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-green-500" />
                      Cost
                    </div>
                  </td>
                  <td className="text-center py-3 px-4">
                    <Typography variant="sm">Free</Typography>
                  </td>
                  <td className="text-center py-3 px-4">
                    <Typography variant="sm">Pay per usage</Typography>
                  </td>
                </tr>
                <tr>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Server className="w-4 h-4 text-purple-500" />
                      Availability
                    </div>
                  </td>
                  <td className="text-center py-3 px-4">
                    <Typography variant="sm">When online</Typography>
                  </td>
                  <td className="text-center py-3 px-4">
                    <Typography variant="sm">24/7</Typography>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle className="text-base">About Cloud Execution</CardTitle>
        </CardHeader>
        <CardContent>
          <Typography variant="sm" className="space-y-2 text-muted-foreground">
            <p>
              <strong>Self-Hosting First:</strong> Iterativ Agent is designed to run locally on your machine. Cloud execution is an optional enhancement for users who need additional performance or availability.
            </p>
            <p>
              <strong>Hybrid Mode:</strong> You can run some workloads locally and others in the cloud based on your needs and budget.
            </p>
            <p>
              <strong>Data Sovereignty:</strong> Choose cloud regions that comply with your data residency requirements. All data is encrypted at rest and in transit.
            </p>
          </Typography>
        </CardContent>
      </Card>
    </div>
  );
}
