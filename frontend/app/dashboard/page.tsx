"use client";

import { useEffect, useState, useCallback } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import DocumentUpload from "@/components/DocumentUpload";
import ChatWindow from "@/components/ChatWindow";
import { DocumentItem, listDocuments } from "@/lib/api";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);

  const refresh = useCallback(async () => {
    const docs = await listDocuments();
    setDocuments(docs);
    setLoadingDocs(false);
  }, []);

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    if (status === "authenticated") refresh();
  }, [status, refresh]);

  // Poll while any document is still processing, so status updates without a manual refresh
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === "processing");
    if (!hasProcessing) return;
    const interval = setInterval(refresh, 3000);
    return () => clearInterval(interval);
  }, [documents, refresh]);

  if (status === "loading" || (status === "authenticated" && loadingDocs)) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <Loader2 className="animate-spin text-accent-deep" />
      </div>
    );
  }

  if (status !== "authenticated") return null;

  return (
    <div className="h-screen bg-paper flex flex-col">
      <Navbar />
      <div className="flex-1 max-w-6xl w-full mx-auto grid grid-cols-[280px_1fr] gap-6 px-6 py-6 min-h-0">
        <aside className="bg-surface border border-surface-border rounded-xl2 p-4 shadow-soft min-h-0">
          <DocumentUpload documents={documents} onChange={refresh} />
        </aside>
        <main className="bg-surface border border-surface-border rounded-xl2 shadow-soft min-h-0 flex flex-col px-4">
          <ChatWindow hasDocuments={documents.some((d) => d.status === "ready")} />
        </main>
      </div>
    </div>
  );
}
