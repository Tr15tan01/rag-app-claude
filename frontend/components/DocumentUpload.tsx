"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, FileText, Loader2, CheckCircle2, XCircle, Trash2 } from "lucide-react";
import clsx from "clsx";
import { DocumentItem, uploadDocument, deleteDocument } from "@/lib/api";

export default function DocumentUpload({
  documents,
  onChange,
}: {
  documents: DocumentItem[];
  onChange: () => void;
}) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];

      if (file.type !== "application/pdf") {
        setUploadError("Only PDF files are supported.");
        return;
      }

      setUploadError("");
      setUploading(true);
      try {
        await uploadDocument(file);
        onChange();
      } catch (err: any) {
        setUploadError(err?.response?.data?.detail || "Upload failed. Please try again.");
      } finally {
        setUploading(false);
      }
    },
    [onChange]
  );

  return (
    <div className="flex flex-col h-full">
      <h2 className="font-display text-lg font-semibold mb-3">Your library</h2>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          "border-2 border-dashed rounded-xl2 p-6 text-center cursor-pointer transition-colors mb-4",
          dragActive ? "border-accent bg-accent/5" : "border-surface-border hover:bg-surface-muted"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        {uploading ? (
          <Loader2 size={22} className="mx-auto mb-2 animate-spin text-accent-deep" />
        ) : (
          <Upload size={22} className="mx-auto mb-2 text-ink/40" />
        )}
        <p className="text-sm font-medium text-ink/70">
          {uploading ? "Uploading..." : "Drop a PDF, or click to browse"}
        </p>
        <p className="text-xs text-ink/40 mt-1">Max 20MB</p>
      </div>

      {uploadError && <p className="text-xs text-red-600 mb-3">{uploadError}</p>}

      <div className="flex-1 overflow-y-auto space-y-2">
        {documents.length === 0 && (
          <p className="text-sm text-ink/40 text-center mt-8">No documents yet.</p>
        )}
        {documents.map((doc) => (
          <DocRow key={doc.id} doc={doc} onDelete={onChange} />
        ))}
      </div>
    </div>
  );
}

function DocRow({ doc, onDelete }: { doc: DocumentItem; onDelete: () => void }) {
  const [deleting, setDeleting] = useState(false);

  return (
    <div className="group flex items-start gap-2.5 p-2.5 rounded-lg hover:bg-surface-muted transition-colors">
      <FileText size={16} className="text-ink/40 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{doc.filename}</p>
        <div className="flex items-center gap-1.5 mt-0.5">
          <StatusIcon status={doc.status} />
          <span className="text-xs text-ink/40">
            {doc.status === "ready" ? `${doc.page_count} pages` : doc.status}
          </span>
        </div>
      </div>
      <button
        onClick={async () => {
          setDeleting(true);
          await deleteDocument(doc.id);
          onDelete();
        }}
        className="opacity-0 group-hover:opacity-100 transition-opacity text-ink/30 hover:text-red-600"
        aria-label={`Delete ${doc.filename}`}
      >
        {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
      </button>
    </div>
  );
}

function StatusIcon({ status }: { status: DocumentItem["status"] }) {
  if (status === "ready") return <CheckCircle2 size={12} className="text-green-600" />;
  if (status === "failed") return <XCircle size={12} className="text-red-600" />;
  return <Loader2 size={12} className="animate-spin text-ink/40" />;
}
