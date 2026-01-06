"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useChatStore } from "@/store/chat";
import { Sidebar, SidebarToggle } from "@/components/chat/Sidebar";
import { ChatMessage, TypingIndicator } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChefHat, Sparkles } from "lucide-react";

export default function ChatPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, checkAuth } = useAuthStore();
  const {
    messages,
    currentConversation,
    isLoading,
    isSending,
    error,
    fetchConversations,
    sendMessage,
    clearError,
  } = useChatStore();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchConversations();
    }
  }, [isAuthenticated, fetchConversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (message: string) => {
    try {
      await sendMessage(message);
    } catch (err) {
      // Error handled by store
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <ChefHat className="h-8 w-8 animate-pulse text-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="h-screen flex overflow-hidden">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="border-b px-4 py-3 flex items-center gap-4 bg-background">
          <SidebarToggle onClick={() => setSidebarOpen(true)} />
          <div className="flex-1 min-w-0">
            <h1 className="font-semibold truncate">
              {currentConversation?.title || "Nueva Cocina"}
            </h1>
          </div>
        </header>

        {/* Messages Area */}
        <ScrollArea className="flex-1">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center">
              <div className="p-4 rounded-full bg-primary/10 mb-6">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
              <h2 className="text-2xl font-bold mb-2">
                ¡Bienvenido a KitchenMaster AI!
              </h2>
              <p className="text-muted-foreground max-w-md mb-8">
                Soy tu asistente experto en diseño de cocinas integrales. 
                Cuéntame sobre tu proyecto y crearé un diseño personalizado para ti.
              </p>
              <div className="grid gap-3 max-w-lg w-full">
                <SuggestionCard
                  title="Cocina moderna en L"
                  description="Quiero una cocina moderna de 4 metros lineales en forma de L"
                  onClick={handleSendMessage}
                />
                <SuggestionCard
                  title="Cocina rústica"
                  description="Diseña una cocina rústica de 3 metros con acabados en madera"
                  onClick={handleSendMessage}
                />
                <SuggestionCard
                  title="Cocina minimalista"
                  description="Necesito una cocina minimalista de 5 metros en U"
                  onClick={handleSendMessage}
                />
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isSending && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Error Display */}
        {error && (
          <div className="px-4 py-2 bg-destructive/10 text-destructive text-sm text-center">
            {error}
            <button
              onClick={clearError}
              className="ml-2 underline hover:no-underline"
            >
              Cerrar
            </button>
          </div>
        )}

        {/* Input */}
        <ChatInput onSend={handleSendMessage} disabled={isSending} />
      </main>
    </div>
  );
}

function SuggestionCard({
  title,
  description,
  onClick,
}: {
  title: string;
  description: string;
  onClick: (message: string) => void;
}) {
  return (
    <button
      onClick={() => onClick(description)}
      className="text-left p-4 rounded-lg border bg-card hover:bg-accent transition-colors"
    >
      <p className="font-medium">{title}</p>
      <p className="text-sm text-muted-foreground">{description}</p>
    </button>
  );
}
