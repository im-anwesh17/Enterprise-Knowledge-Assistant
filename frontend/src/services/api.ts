import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create a configured axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Since we are mocking login for the frontend build, 
// we attach the demo token directly if it exists in local storage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Analytics Service
export const executeNLQuery = async (query: string) => {
  const response = await api.post('/analytics/text-to-sql', { query });
  return response.data;
};

// Document Service (For Phase 5)
export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// Chat Service
export const getChatSessions = async () => {
  const response = await api.get('/chat/sessions');
  return response.data;
};

export const createChatSession = async (title: string) => {
  const response = await api.post(`/chat/sessions?title=${encodeURIComponent(title)}`);
  return response.data;
};

export const sendChatMessage = async (sessionId: number, content: string) => {
  const response = await api.post(`/chat/sessions/${sessionId}/message`, { content });
  return response.data;
};
