import axios from "axios";
import { getSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use(async (config) => {
  const session = await getSession();
  const token = (session as any)?.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface DocumentItem {
  id: string;
  filename: string;
  page_count: number;
  status: "processing" | "ready" | "failed";
  created_at: string;
}

export interface SourceChunk {
  document_id: string;
  filename: string;
  page_number: number;
  text: string;
  score: number;
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const { data } = await api.get("/documents");
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`);
}

export async function askQuestion(
  query: string,
  documentIds?: string[]
): Promise<{ answer: string; sources: SourceChunk[] }> {
  const { data } = await api.post("/chat", {
    query,
    document_ids: documentIds ?? null,
  });
  return data;
}
