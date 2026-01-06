import { create } from "zustand";
import { api, Conversation, Message, ChatResponse } from "@/lib/api";

interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  isSending: boolean;
  error: string | null;

  fetchConversations: () => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  createConversation: () => Promise<Conversation>;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (message: string) => Promise<ChatResponse>;
  clearError: () => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  isSending: false,
  error: null,

  fetchConversations: async () => {
    set({ isLoading: true, error: null });
    try {
      const conversations = await api.getConversations();
      set({ conversations, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || "Error al cargar conversaciones",
        isLoading: false 
      });
    }
  },

  selectConversation: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await api.getConversation(id);
      set({ 
        currentConversation: conversation,
        messages: conversation.messages || [],
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || "Error al cargar conversación",
        isLoading: false 
      });
    }
  },

  createConversation: async () => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await api.createConversation();
      set((state) => ({ 
        conversations: [conversation, ...state.conversations],
        currentConversation: conversation,
        messages: [],
        isLoading: false 
      }));
      return conversation;
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || "Error al crear conversación",
        isLoading: false 
      });
      throw error;
    }
  },

  deleteConversation: async (id: string) => {
    try {
      await api.deleteConversation(id);
      set((state) => {
        const conversations = state.conversations.filter((c) => c.id !== id);
        const currentConversation = 
          state.currentConversation?.id === id ? null : state.currentConversation;
        return { 
          conversations, 
          currentConversation,
          messages: currentConversation ? state.messages : []
        };
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || "Error al eliminar conversación"
      });
    }
  },

  sendMessage: async (message: string) => {
    const { currentConversation } = get();
    
    set({ isSending: true, error: null });
    
    // Add user message optimistically
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: message,
      artifacts: [],
      created_at: new Date().toISOString(),
    };
    
    set((state) => ({
      messages: [...state.messages, tempUserMessage],
    }));

    try {
      const response = await api.sendMessage(
        message,
        currentConversation?.id
      );

      // Create assistant message from response
      const assistantMessage: Message = {
        id: response.message_id,
        role: "assistant",
        content: response.content,
        artifacts: response.artifacts.map((a, i) => ({
          id: `artifact-${i}`,
          artifact_type: a.type as any,
          title: a.title,
          content: a.content || null,
          image_url: a.image_data ? `data:image/png;base64,${a.image_data}` : null,
          metadata: a.metadata,
          created_at: new Date().toISOString(),
        })),
        created_at: new Date().toISOString(),
      };

      set((state) => {
        // Remove temp message and add real messages
        const messages = state.messages.filter(m => m.id !== tempUserMessage.id);
        
        // Update conversation if new
        let conversations = state.conversations;
        let currentConversation = state.currentConversation;
        
        if (!state.currentConversation) {
          currentConversation = {
            id: response.conversation_id,
            title: "Nueva Cocina",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          conversations = [currentConversation, ...conversations];
        }

        return {
          messages: [...messages, { ...tempUserMessage, id: `user-${Date.now()}` }, assistantMessage],
          currentConversation,
          conversations,
          isSending: false,
        };
      });

      // Refresh conversations to get updated titles
      get().fetchConversations();

      return response;
    } catch (error: any) {
      // Remove optimistic message on error
      set((state) => ({
        messages: state.messages.filter(m => m.id !== tempUserMessage.id),
        error: error.response?.data?.detail || "Error al enviar mensaje",
        isSending: false,
      }));
      throw error;
    }
  },

  clearError: () => set({ error: null }),
  
  reset: () => set({
    currentConversation: null,
    messages: [],
    error: null,
  }),
}));
