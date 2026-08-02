import Link from "next/link";
import { ArrowRight, ShieldCheck, FileText, Quote } from "lucide-react";
import Navbar from "@/components/Navbar";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-paper">
      <Navbar />

      <main className="max-w-4xl mx-auto px-6 pt-24 pb-32 text-center">
        <div className="inline-flex items-center gap-1.5 text-xs font-semibold tracking-wide uppercase text-accent-deep bg-accent/10 px-3 py-1 rounded-full mb-8">
          Grounded answers, always cited
        </div>

        <h1 className="font-display text-5xl sm:text-6xl font-semibold tracking-tight leading-[1.1] mb-6">
          Ask your documents
          <br />
          <span className="text-accent-deep">anything.</span>
        </h1>

        <p className="text-lg text-ink/60 max-w-xl mx-auto mb-10 leading-relaxed">
          Upload PDFs and get answers pulled straight from the page —
          every response points back to exactly where it came from.
        </p>

        <Link
          href="/register"
          className="inline-flex items-center gap-2 bg-ink text-paper px-6 py-3.5 rounded-full font-medium hover:bg-ink/85 transition-colors shadow-lift"
        >
          Start reading smarter
          <ArrowRight size={16} />
        </Link>

        <div className="grid sm:grid-cols-3 gap-6 mt-24 text-left">
          <Feature
            icon={<FileText size={18} />}
            title="Upload any PDF"
            body="Reports, contracts, papers, manuals — chunked and indexed automatically."
          />
          <Feature
            icon={<Quote size={18} />}
            title="Every answer, cited"
            body="Responses reference the exact page and passage they're drawn from."
          />
          <Feature
            icon={<ShieldCheck size={18} />}
            title="Private by default"
            body="Your documents are yours alone — never visible to other accounts."
          />
        </div>
      </main>
    </div>
  );
}

function Feature({ icon, title, body }: { icon: React.ReactNode; title: string; body: string }) {
  return (
    <div className="bg-surface border border-surface-border rounded-xl2 p-6 shadow-soft">
      <div className="w-9 h-9 rounded-full bg-accent/10 text-accent-deep flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="font-semibold mb-1.5">{title}</h3>
      <p className="text-sm text-ink/60 leading-relaxed">{body}</p>
    </div>
  );
}
