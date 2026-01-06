"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { Message } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import { Bot, User } from "lucide-react";
import { ArtifactCard } from "./ArtifactCard";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-4 p-4 animate-message-in",
        isUser ? "bg-muted/50" : "bg-background"
      )}
    >
      <Avatar className={cn("h-8 w-8", isUser ? "bg-primary" : "bg-secondary")}>
        <AvatarFallback>
          {isUser ? (
            <User className="h-4 w-4 text-primary-foreground" />
          ) : (
            <Bot className="h-4 w-4 text-secondary-foreground" />
          )}
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-4 overflow-hidden">
        <div className="font-medium text-sm text-muted-foreground">
          {isUser ? "Tú" : "KitchenMaster AI"}
        </div>

        <div className="markdown-content prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {message.artifacts && message.artifacts.length > 0 && (
          <div className="space-y-4 mt-4">
            {message.artifacts.map((artifact, index) => (
              <ArtifactCard key={artifact.id || index} artifact={artifact} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-4 p-4 bg-background">
      <Avatar className="h-8 w-8 bg-secondary">
        <AvatarFallback>
          <Bot className="h-4 w-4 text-secondary-foreground" />
        </AvatarFallback>
      </Avatar>

      <div className="flex items-center gap-1 pt-2">
        <div className="typing-dot h-2 w-2 rounded-full bg-muted-foreground" />
        <div className="typing-dot h-2 w-2 rounded-full bg-muted-foreground" />
        <div className="typing-dot h-2 w-2 rounded-full bg-muted-foreground" />
      </div>
    </div>
  );
}
