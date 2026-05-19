import { Button } from "@nous-research/ui/ui/components/button";
import { Typography } from "@/components/NouiTypography";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { GitBranch, CheckCircle2, XCircle, Clock, Play, Plus } from "lucide-react";

interface TaskNode {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  dependencies: string[];
  result?: string;
  error?: string;
}

interface Workflow {
  id: string;
  name: string;
  description: string;
  status: "pending" | "running" | "completed" | "failed";
  tasks: TaskNode[];
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

export default function WorkflowPage() {
  const workflows: Workflow[] = [
    {
      id: "wf1",
      name: "Research: Quantum Computing Breakthroughs",
      description: "Research recent quantum computing developments and synthesize findings",
      status: "completed",
      createdAt: "2025-01-15T10:00:00Z",
      startedAt: "2025-01-15T10:01:00Z",
      completedAt: "2025-01-15T10:05:30Z",
      tasks: [
        {
          id: "task1",
          name: "Search Web",
          status: "completed",
          dependencies: [],
          result: "Found 15 relevant sources",
        },
        {
          id: "task2",
          name: "Analyze Sources",
          status: "completed",
          dependencies: ["task1"],
          result: "Evaluated 8 high-quality sources",
        },
        {
          id: "task3",
          name: "Synthesize Findings",
          status: "completed",
          dependencies: ["task2"],
          result: "Generated comprehensive summary",
        },
      ],
    },
    {
      id: "wf2",
      name: "Implement Sorting Algorithm",
      description: "Write and test a quicksort implementation in Python",
      status: "running",
      createdAt: "2025-01-15T11:00:00Z",
      startedAt: "2025-01-15T11:01:00Z",
      tasks: [
        {
          id: "task4",
          name: "Analyze Requirements",
          status: "completed",
          dependencies: [],
          result: "Requirements defined",
        },
        {
          id: "task5",
          name: "Write Code",
          status: "running",
          dependencies: ["task4"],
        },
        {
          id: "task6",
          name: "Test Code",
          status: "pending",
          dependencies: ["task5"],
        },
        {
          id: "task7",
          name: "Add Documentation",
          status: "pending",
          dependencies: ["task6"],
        },
      ],
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "running":
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "running":
        return "bg-blue-500";
      default:
        return "bg-gray-400";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge className="bg-green-500">Completed</Badge>;
      case "failed":
        return <Badge className="bg-red-500">Failed</Badge>;
      case "running":
        return <Badge className="bg-blue-500">Running</Badge>;
      default:
        return <Badge className="bg-gray-400">Pending</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <Typography variant="xl" className="flex items-center gap-3">
            <GitBranch className="w-8 h-8" />
            Workflows
          </Typography>
          <Typography variant="sm" className="text-muted-foreground mt-2">
            Visualize and manage complex multi-step task workflows
          </Typography>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Workflow
        </Button>
      </div>

      <div className="space-y-6">
        {workflows.map((workflow) => (
          <Card key={workflow.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{workflow.name}</CardTitle>
                  <Typography variant="sm" className="text-muted-foreground mt-1">
                    {workflow.description}
                  </Typography>
                </div>
                {getStatusBadge(workflow.status)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <Typography variant="sm" className="font-medium text-muted-foreground mb-2">
                  Task Flow
                </Typography>
                <div className="space-y-3">
                  {workflow.tasks.map((task: TaskNode, index: number) => (
                    <div key={task.id} className="relative">
                      {/* Connection line */}
                      {index < workflow.tasks.length - 1 && (
                        <div className="absolute left-4 top-8 w-0.5 h-8 bg-gray-200" />
                      )}
                      
                      <div className="flex items-start gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getStatusColor(task.status)}`}>
                          {getStatusIcon(task.status)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <Typography variant="md" className="font-medium">
                              {task.name}
                            </Typography>
                            <Badge className="text-xs bg-secondary">
                              {task.status}
                            </Badge>
                          </div>
                          {task.dependencies.length > 0 && (
                            <Typography variant="sm" className="text-muted-foreground mt-1">
                              Depends on: {task.dependencies.join(", ")}
                            </Typography>
                          )}
                          {task.result && (
                            <Typography variant="sm" className="text-green-600 mt-1">
                              ✓ {task.result}
                            </Typography>
                          )}
                          {task.error && (
                            <Typography variant="sm" className="text-red-600 mt-1">
                              ✗ {task.error}
                            </Typography>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t">
                <Typography variant="sm" className="text-muted-foreground">
                  {workflow.tasks.filter((t: TaskNode) => t.status === "completed").length} / {workflow.tasks.length} tasks completed
                </Typography>
                {workflow.status === "pending" && (
                  <Button size="sm">
                    <Play className="w-4 h-4 mr-2" />
                    Execute
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Info Card */}
      <Card className="mt-6 bg-muted/50">
        <CardHeader>
          <CardTitle className="text-base">How Workflows Work</CardTitle>
        </CardHeader>
        <CardContent>
          <Typography variant="sm" className="space-y-2 text-muted-foreground">
            <p>
              <strong>Task Decomposition:</strong> Complex tasks are automatically broken down into smaller, manageable subtasks.
            </p>
            <p>
              <strong>Dependency Management:</strong> Tasks execute in the correct order based on their dependencies.
            </p>
            <p>
              <strong>Parallel Execution:</strong> Independent tasks run simultaneously for faster completion.
            </p>
            <p>
              <strong>Error Recovery:</strong> Failed tasks automatically retry with fallback strategies.
            </p>
          </Typography>
        </CardContent>
      </Card>
    </div>
  );
}
