"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { startPipeline } from "@/lib/api";

const SAMPLE_INPUT = `ซื้อเก้าอี้ทำงาน ergonomic ราคา 5,000 บาท แต่ยังปวดหลังเหมือนเดิม สูง 150 ซม นั่งแล้วเท้าลอย ขาห้อย ปรับเก้าอี้ต่ำสุดแล้วก็ยังสูงเกินไป ลองหมอนรองหลังแล้วก็ยังไม่ดีขึ้น เสียเงินไปฟรีๆ เลย ใครเตี้ยเหมือนกันแนะนำเก้าอี้ทีค่ะ งบไม่เกิน 3,000`;

export default function HomePage() {
  const [rawText, setRawText] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleStart = async () => {
    if (rawText.trim().length < 10) {
      toast.error("Input too short", { description: "Please paste at least 10 characters of research text." });
      return;
    }

    setIsLoading(true);
    try {
      const result = await startPipeline({ raw_text: rawText, model });
      toast.success("Pipeline Started!", { description: `Run ID: ${result.run_id.slice(0, 8)}...` });
      router.push(`/runs/${result.run_id}`);
    } catch (err) {
      toast.error("Failed to start pipeline", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
          New Content Blueprint
        </h1>
        <p className="text-gray-400 text-sm">
          Paste raw research text (comments, reviews, forum posts) — the AI agents will extract persona,
          generate SEO/GEO strategy, and build a complete Hub &amp; Spoke content cluster.
        </p>
      </div>

      {/* Input Card */}
      <Card className="border-white/5 bg-white/[0.02] backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-lg text-gray-200 flex items-center gap-2">
            <span className="text-xl">📝</span> Raw Research Input
          </CardTitle>
          <CardDescription>
            Paste user comments, competitor reviews, or any unstructured research text.
            Thai or English supported.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="Paste raw text here... (e.g., user comments, reviews, forum posts)"
            className="min-h-[200px] bg-gray-950/50 border-white/10 text-gray-200 placeholder:text-gray-600 resize-y focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20"
          />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Model:</span>
                <Select value={model} onValueChange={setModel}>
                  <SelectTrigger className="w-[180px] h-8 text-xs bg-gray-950/50 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt-4o">GPT-4o (Recommended)</SelectItem>
                    <SelectItem value="gpt-4o-mini">GPT-4o Mini (Faster)</SelectItem>
                    <SelectItem value="deepseek-chat">DeepSeek Chat</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Badge variant="outline" className="text-[10px] border-white/10 text-gray-500">
                {rawText.length} chars
              </Badge>
            </div>

            <Button
              onClick={() => setRawText(SAMPLE_INPUT)}
              variant="ghost"
              size="sm"
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Load Sample
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Start Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleStart}
          disabled={isLoading || rawText.trim().length < 10}
          size="lg"
          className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-lg shadow-violet-500/20 transition-all hover:shadow-violet-500/30 disabled:opacity-50 disabled:shadow-none px-8"
        >
          {isLoading ? (
            <>
              <span className="animate-spin mr-2">⟳</span>
              Starting Pipeline...
            </>
          ) : (
            <>
              🚀 Start Agent Pipeline
            </>
          )}
        </Button>
      </div>

      {/* How It Works */}
      <Card className="border-white/5 bg-white/[0.01]">
        <CardHeader>
          <CardTitle className="text-sm text-gray-400">How It Works</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-4">
            {[
              { step: "1", label: "Intent", desc: "Extract persona & pain points", icon: "🔍" },
              { step: "2", label: "SEO/GEO", desc: "Keywords & AI queries", icon: "📊" },
              { step: "3", label: "Cluster", desc: "Hub & Spoke model", icon: "🏗️" },
              { step: "4", label: "Review", desc: "Human approval", icon: "✋" },
              { step: "5", label: "Dispatch", desc: "Send to production", icon: "🚀" },
            ].map((s) => (
              <div key={s.step} className="text-center space-y-2">
                <div className="w-10 h-10 mx-auto rounded-full bg-white/[0.03] border border-white/5 flex items-center justify-center text-lg">
                  {s.icon}
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-300">{s.label}</p>
                  <p className="text-[10px] text-gray-600">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
