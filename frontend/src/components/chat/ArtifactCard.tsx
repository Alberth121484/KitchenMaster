"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Artifact } from "@/lib/api";
import { 
  Image as ImageIcon, 
  FileText, 
  DollarSign, 
  Layout,
  Download,
  Maximize2,
  X
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";

interface ArtifactCardProps {
  artifact: Artifact;
}

export function ArtifactCard({ artifact }: ArtifactCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getIcon = () => {
    switch (artifact.artifact_type) {
      case "image":
        return <ImageIcon className="h-4 w-4" />;
      case "specs":
        return <FileText className="h-4 w-4" />;
      case "cost_estimate":
        return <DollarSign className="h-4 w-4" />;
      case "floor_plan":
        return <Layout className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getTitle = () => {
    if (artifact.title) return artifact.title;
    switch (artifact.artifact_type) {
      case "image":
        return "Diseño de Cocina";
      case "specs":
        return "Especificaciones Técnicas";
      case "cost_estimate":
        return "Estimación de Costos";
      case "floor_plan":
        return "Plano de Planta";
      default:
        return "Documento";
    }
  };

  const handleDownload = () => {
    if (artifact.image_url) {
      const link = document.createElement("a");
      link.href = artifact.image_url;
      link.download = `${getTitle()}.png`;
      link.click();
    }
  };

  return (
    <>
      <Card className="overflow-hidden border-2 border-primary/20 hover:border-primary/40 transition-colors">
        <CardHeader className="p-3 bg-muted/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getIcon()}
              <CardTitle className="text-sm font-medium">{getTitle()}</CardTitle>
            </div>
            <div className="flex items-center gap-1">
              {artifact.artifact_type === "image" && artifact.image_url && (
                <>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => setIsExpanded(true)}
                  >
                    <Maximize2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={handleDownload}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {artifact.artifact_type === "image" && artifact.image_url && (
            <div className="artifact-image">
              <img
                src={artifact.image_url}
                alt={getTitle()}
                className="w-full h-auto max-h-[400px] object-contain bg-muted"
              />
            </div>
          )}
          {artifact.content && (
            <div className="p-4 prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{artifact.content}</ReactMarkdown>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Fullscreen Image Modal */}
      {isExpanded && artifact.image_url && (
        <div 
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setIsExpanded(false)}
        >
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-4 right-4 text-white hover:bg-white/20"
            onClick={() => setIsExpanded(false)}
          >
            <X className="h-6 w-6" />
          </Button>
          <img
            src={artifact.image_url}
            alt={getTitle()}
            className="max-w-full max-h-full object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  );
}
