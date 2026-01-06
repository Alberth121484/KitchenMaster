import axios, { AxiosError, AxiosInstance } from "axios";

// Detecta API URL en runtime basándose en el hostname actual
function getApiUrl(): string {
  // En el navegador, derivar del hostname actual
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    
    // Producción: cocinas.alchemycode.dev -> api.cocinas.alchemycode.dev
    if (hostname !== "localhost" && hostname !== "127.0.0.1") {
      return `https://${process.env.NEXT_PUBLIC_API_DOMAIN}.${hostname}`;
    }
  }
  
  // Desarrollo local o SSR
  return process.env.NEXT_PUBLIC_API_DOMAIN 
    ? `https://${process.env.NEXT_PUBLIC_API_DOMAIN}`
    : "http://localhost:8000";
}

const API_URL = getApiUrl();

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
  message_count?: number;
  last_message?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  artifacts: Artifact[];
  created_at: string;
}

export interface Artifact {
  id: string;
  artifact_type: "image" | "specs" | "cost_estimate" | "floor_plan";
  title: string | null;
  content: string | null;
  image_url: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  content: string;
  artifacts: {
    type: string;
    title: string;
    content?: string;
    image_data?: string;
    metadata: Record<string, any>;
  }[];
  design_version?: number;
}

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Load token from localStorage
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }

    // Request interceptor
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401 && this.token) {
          // Try to refresh token
          const refreshToken = localStorage.getItem("refresh_token");
          if (refreshToken) {
            try {
              const response = await this.refreshToken(refreshToken);
              this.setTokens(response);
              // Retry original request
              const config = error.config!;
              config.headers.Authorization = `Bearer ${this.token}`;
              return this.client.request(config);
            } catch {
              this.logout();
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setTokens(tokens: Token) {
    this.token = tokens.access_token;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
    }
  }

  logout() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  getToken(): string | null {
    return this.token;
  }

  // Auth endpoints
  async register(email: string, password: string, fullName?: string): Promise<Token> {
    const response = await this.client.post<Token>("/auth/register", {
      email,
      password,
      full_name: fullName,
    });
    this.setTokens(response.data);
    return response.data;
  }

  async login(email: string, password: string): Promise<Token> {
    const response = await this.client.post<Token>("/auth/login", {
      email,
      password,
    });
    this.setTokens(response.data);
    return response.data;
  }

  async refreshToken(refreshToken: string): Promise<Token> {
    const response = await this.client.post<Token>("/auth/refresh", null, {
      params: { refresh_token: refreshToken },
    });
    return response.data;
  }

  async getMe(): Promise<User> {
    const response = await this.client.get<User>("/auth/me");
    return response.data;
  }

  // Conversation endpoints
  async getConversations(): Promise<Conversation[]> {
    const response = await this.client.get<Conversation[]>("/conversations");
    return response.data;
  }

  async getConversation(id: string): Promise<Conversation> {
    const response = await this.client.get<Conversation>(`/conversations/${id}`);
    return response.data;
  }

  async createConversation(title?: string): Promise<Conversation> {
    const response = await this.client.post<Conversation>("/conversations", {
      title,
    });
    return response.data;
  }

  async deleteConversation(id: string): Promise<void> {
    await this.client.delete(`/conversations/${id}`);
  }

  // Chat endpoint
  async sendMessage(
    message: string,
    conversationId?: string
  ): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>("/chat", {
      message,
      conversation_id: conversationId,
    });
    return response.data;
  }

  // Design history
  async getDesignHistory(conversationId: string): Promise<any[]> {
    const response = await this.client.get(`/chat/history/${conversationId}/designs`);
    return response.data;
  }
}

export const api = new ApiClient();
