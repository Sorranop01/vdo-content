"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import {
    getPipelineStatus,
    getBlueprint,
    approvePipeline,
    STATUS_CONFIG,
    SEO_MODE_CONFIG,
    type PipelineStatusResponse,
    type ContentBlueprintPayload,
    type TopicBlueprint,
    type InternalLink,
    type SEOMode,
} from "@/lib/api";

export default function PipelineRunPage() {
    const params = useParams();
    const runId = params.id as string;

    const [status, setStatus] = useState<PipelineStatusResponse | null>(null);
    const [blueprint, setBlueprint] = useState<ContentBlueprintPayload | null>(null);
    const [isApproving, setIsApproving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const pollStatus = useCallback(async () => {
        try {
            const s = await getPipelineStatus(runId);
            setStatus(s);

            // Fetch blueprint when ready
            if (
                ["awaiting_review", "approved", "completed"].includes(s.status) &&
                !blueprint
            ) {
                try {
                    const b = await getBlueprint(runId);
                    setBlueprint(b.blueprint);
                } catch {
                    // Blueprint may not be ready yet
                }
            }

            // Stop polling when terminal
            return ["completed", "failed", "rejected", "awaiting_review"].includes(s.status);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch status");
            return true;
        }
    }, [runId, blueprint]);

    useEffect(() => {
        let timer: ReturnType<typeof setTimeout>;
        let cancelled = false;

        const poll = async () => {
            if (cancelled) return;
            const done = await pollStatus();
            if (!done && !cancelled) {
                timer = setTimeout(poll, 2000);
            }
        };
        poll();

        return () => {
            cancelled = true;
            clearTimeout(timer);
        };
    }, [pollStatus]);

    const handleApprove = async () => {
        setIsApproving(true);
        try {
            const result = await approvePipeline(runId);
            if (result.status === "completed") {
                toast.success("Blueprint dispatched to production! 🎉");
                setStatus((prev) => prev ? { ...prev, status: "completed" } : prev);
            } else {
                toast.error("Dispatch failed", { description: result.error || "Unknown error" });
            }
        } catch (err) {
            toast.error("Approval failed", {
                description: err instanceof Error ? err.message : "Unknown error",
            });
        } finally {
            setIsApproving(false);
        }
    };

    if (error) {
        return (
            <div className="max-w-4xl mx-auto p-8">
                <Card className="border-red-500/20 bg-red-500/5">
                    <CardContent className="p-6 text-center text-red-400">
                        <p className="text-lg">❌ {error}</p>
                        <a href="/" className="text-sm text-violet-400 underline mt-2 inline-block">
                            ← Back to Home
                        </a>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (!status) {
        return (
            <div className="max-w-4xl mx-auto p-8">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 bg-white/5 rounded w-1/3" />
                    <div className="h-40 bg-white/5 rounded" />
                </div>
            </div>
        );
    }

    const cfg = STATUS_CONFIG[status.status];

    return (
        <div className="max-w-5xl mx-auto p-8 space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div className="space-y-1">
                    <div className="flex items-center gap-3">
                        <a href="/" className="text-gray-500 hover:text-gray-300 text-sm">← Back</a>
                        <h1 className="text-2xl font-bold text-gray-100">Pipeline Run</h1>
                    </div>
                    <p className="text-xs font-mono text-gray-500">{runId}</p>
                </div>
                <Badge
                    className={`${cfg.color} text-white px-3 py-1 text-sm`}
                >
                    {cfg.icon} {cfg.label}
                </Badge>
            </div>

            {/* Progress */}
            <Card className="border-white/5 bg-white/[0.02]">
                <CardContent className="py-4 px-6 space-y-3">
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-400">{status.current_stage}</span>
                        <span className="text-gray-500">{cfg.progress}%</span>
                    </div>
                    <Progress value={cfg.progress} className="h-2" />

                    {/* Stage indicators */}
                    <div className="grid grid-cols-5 gap-2 pt-2">
                        {[
                            { s: "extracting_intent", icon: "🔍", label: "Intent" },
                            { s: "formulating_seo", icon: "📊", label: "SEO" },
                            { s: "clustering", icon: "🏗️", label: "Cluster" },
                            { s: "awaiting_review", icon: "✋", label: "Review" },
                            { s: "completed", icon: "🚀", label: "Dispatch" },
                        ].map((stage) => {
                            const stageOrder = ["pending", "extracting_intent", "formulating_seo", "clustering", "awaiting_review", "approved", "dispatching", "completed"];
                            const currentIdx = stageOrder.indexOf(status.status);
                            const stageIdx = stageOrder.indexOf(stage.s);
                            const isDone = currentIdx >= stageIdx && status.status !== "failed";
                            const isCurrent = status.status === stage.s;

                            return (
                                <div
                                    key={stage.s}
                                    className={`text-center py-2 rounded-lg text-xs transition-all ${isCurrent
                                        ? "bg-violet-500/10 border border-violet-500/30 text-violet-300"
                                        : isDone
                                            ? "text-green-400/70"
                                            : "text-gray-600"
                                        }`}
                                >
                                    <div className="text-lg">{stage.icon}</div>
                                    <div className="mt-1">{stage.label}</div>
                                </div>
                            );
                        })}
                    </div>
                </CardContent>
            </Card>

            {/* EC1: REJECTED — input quality issue, NOT a pipeline crash */}
            {status.status === "rejected" && (
                <Card className="border-yellow-500/30 bg-yellow-500/5">
                    <CardContent className="p-6 space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">⚠️</span>
                            <div>
                                <p className="text-yellow-300 font-semibold text-base">Input Rejected</p>
                                <p className="text-yellow-300/60 text-sm mt-0.5">
                                    Your input did not contain enough researchable consumer content.
                                </p>
                            </div>
                        </div>
                        {status.error && (
                            <div className="bg-yellow-500/10 rounded-md px-3 py-2 border border-yellow-500/20">
                                <p className="text-xs text-yellow-200/80 font-mono">{status.error}</p>
                            </div>
                        )}
                        <p className="text-xs text-gray-500">
                            💡 Tips: paste user reviews, forum comments, or survey responses that describe
                            real experiences, pain points, or purchase decisions.
                        </p>
                        <a
                            href="/"
                            className="inline-flex items-center gap-2 mt-1 text-sm text-yellow-400 hover:text-yellow-300 underline underline-offset-2"
                        >
                            ← Try again with different input
                        </a>
                    </CardContent>
                </Card>
            )}

            {/* Generic error display (FAILED status only) */}
            {status.status === "failed" && status.error && (
                <Card className="border-red-500/20 bg-red-500/5">
                    <CardContent className="p-4 text-red-400 text-sm">
                        <strong>Pipeline Error:</strong> {status.error}
                    </CardContent>
                </Card>
            )}

            {/* Blueprint Review */}
            {blueprint && (
                <>
                    <Separator className="border-white/5" />

                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold text-gray-100 flex items-center gap-2">
                                📐 Content Blueprint Review
                            </h2>
                            {/* EC4: SEO mode badge */}
                            {status.seo_mode && status.seo_mode !== "full_seo_geo" && (() => {
                                const modeCfg = SEO_MODE_CONFIG[status.seo_mode as SEOMode];
                                return (
                                    <Badge
                                        variant="outline"
                                        className={`text-xs border px-2 py-0.5 ${modeCfg.color}`}
                                        title={modeCfg.description}
                                    >
                                        {modeCfg.icon} {modeCfg.label}
                                    </Badge>
                                );
                            })()}
                        </div>
                        <p className="text-sm text-gray-500">
                            Review the AI-generated blueprint below. Approve to dispatch to the production system.
                        </p>
                    </div>

                    {/* Persona & Context */}
                    <Card className="border-white/5 bg-white/[0.02]">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-base text-gray-200">👤 Target Persona</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3 text-sm">
                            <p className="text-gray-300">{blueprint.target_persona}</p>
                            <div className="flex flex-wrap gap-2">
                                {blueprint.core_pain_points.map((p, i) => (
                                    <Badge key={i} variant="outline" className="border-red-500/20 text-red-400 text-xs">
                                        💢 {p}
                                    </Badge>
                                ))}
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {blueprint.underlying_emotions.map((e, i) => (
                                    <Badge key={i} variant="outline" className="border-amber-500/20 text-amber-400 text-xs">
                                        💭 {e}
                                    </Badge>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Hub Topic */}
                    <TopicCard topic={blueprint.hub} type="hub" />

                    {/* Spokes */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {blueprint.spokes.map((spoke, i) => (
                            <TopicCard key={spoke.topic_id} topic={spoke} type="spoke" index={i + 1} />
                        ))}
                    </div>

                    {/* Internal Links */}
                    <Card className="border-white/5 bg-white/[0.02]">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-base text-gray-200">🔗 Internal Linking Map</CardTitle>
                            <CardDescription>{blueprint.internal_links.length} links defined</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                {blueprint.internal_links.map((link, i) => (
                                    <LinkRow key={i} link={link} topics={[blueprint.hub, ...blueprint.spokes]} />
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* SEO Summary */}
                    <Card className="border-white/5 bg-white/[0.02]">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-base text-gray-200">📊 Cluster SEO Summary</CardTitle>
                        </CardHeader>
                        <CardContent className="text-sm space-y-2">
                            <div className="flex justify-between">
                                <span className="text-gray-500">Primary Keyword</span>
                                <span className="text-violet-300 font-medium">{blueprint.cluster_primary_keyword}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">Est. Search Volume</span>
                                <span className="text-gray-300 flex items-center gap-1">
                                    {blueprint.estimated_total_search_volume?.toLocaleString() || "—"}
                                    <Badge
                                        variant="outline"
                                        className="text-[9px] ml-1 border-white/10 text-gray-500"
                                        title="Source of search volume estimate"
                                    >
                                        AI est.
                                    </Badge>
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">Model Used</span>
                                <Badge variant="outline" className="border-white/10 text-gray-400 text-xs">
                                    {blueprint.agent_model_used}
                                </Badge>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">Cannibalization Check</span>
                                <span>{blueprint.cannibalization_checked ? "✅ Done" : "⬜ Skipped"}</span>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Approve Button */}
                    {status.status === "awaiting_review" && (
                        <div className="space-y-3">
                            {/* EC4: HITL-required warning banner */}
                            {status.seo_mode === "hitl_required" && (
                                <Card className="border-red-500/30 bg-red-500/5">
                                    <CardContent className="p-3 flex items-start gap-3">
                                        <span className="text-xl">🔴</span>
                                        <div>
                                            <p className="text-red-300 text-sm font-semibold">Human Review Required</p>
                                            <p className="text-red-300/60 text-xs mt-0.5">
                                                {status.seo_mode_reason || "No SEO volume detected and some topics are missing GEO queries. Approve only if you are confident in this blueprint."}
                                            </p>
                                        </div>
                                    </CardContent>
                                </Card>
                            )}
                            {/* EC4: GEO-only info banner */}
                            {status.seo_mode === "geo_only" && (
                                <Card className="border-amber-500/20 bg-amber-500/5">
                                    <CardContent className="p-3 flex items-start gap-3">
                                        <span className="text-xl">🤖</span>
                                        <div>
                                            <p className="text-amber-300 text-sm font-semibold">GEO-Only Strategy</p>
                                            <p className="text-amber-300/60 text-xs mt-0.5">
                                                No measurable SEO search volume found. This blueprint is optimised for AI search discovery (ChatGPT, Perplexity, Google Gemini) rather than traditional SEO.
                                            </p>
                                        </div>
                                    </CardContent>
                                </Card>
                            )}
                            <div className="flex justify-end gap-3 pt-1">
                                <Button variant="outline" className="border-white/10 text-gray-400">
                                    ✏️ Edit Blueprint
                                </Button>
                                <Button
                                    onClick={handleApprove}
                                    disabled={isApproving}
                                    size="lg"
                                    className="bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white shadow-lg shadow-emerald-500/20 px-8"
                                >
                                    {isApproving ? (
                                        <><span className="animate-spin mr-2">⟳</span> Dispatching...</>
                                    ) : (
                                        <>✅ Approve &amp; Send to Production</>
                                    )}
                                </Button>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

// ============================================================
// Sub-Components
// ============================================================

function TopicCard({
    topic,
    type,
    index,
}: {
    topic: TopicBlueprint;
    type: "hub" | "spoke";
    index?: number;
}) {
    const isHub = type === "hub";

    return (
        <Card
            className={`border-white/5 ${isHub
                ? "bg-gradient-to-br from-violet-500/5 to-indigo-500/5 border-violet-500/10"
                : "bg-white/[0.02]"
                }`}
        >
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <Badge
                        className={`text-xs ${isHub
                            ? "bg-violet-500/20 text-violet-300"
                            : "bg-blue-500/20 text-blue-300"
                            }`}
                    >
                        {isHub ? "🎯 HUB" : `📌 SPOKE ${index}`}
                    </Badge>
                    <Badge variant="outline" className="border-white/10 text-gray-500 text-[10px]">
                        {topic.content_type} · {topic.tone}
                    </Badge>
                </div>
                <CardTitle className="text-lg text-gray-100 mt-2">{topic.title}</CardTitle>
                <CardDescription className="text-gray-400 italic">&ldquo;{topic.hook}&rdquo;</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
                {/* Key Points */}
                <div>
                    <p className="text-gray-500 text-xs mb-2 font-medium">Key Points</p>
                    <ul className="space-y-1">
                        {topic.key_points.map((p, i) => (
                            <li key={i} className="text-gray-300 flex gap-2">
                                <span className="text-gray-600">•</span>{p}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* SEO */}
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <p className="text-gray-500 text-xs mb-1 font-medium">Primary Keyword</p>
                        <p className="text-violet-300 text-xs">{topic.seo.primary_keyword}</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs mb-1 font-medium">Search Intent</p>
                        <p className="text-gray-300 text-xs capitalize">{topic.seo.search_intent}</p>
                    </div>
                </div>

                {topic.seo.secondary_keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                        {topic.seo.secondary_keywords.map((kw, i) => (
                            <Badge key={i} variant="outline" className="border-white/5 text-gray-500 text-[10px]">
                                {kw}
                            </Badge>
                        ))}
                    </div>
                )}

                {/* GEO Queries */}
                {topic.geo_queries.length > 0 && (
                    <div>
                        <p className="text-gray-500 text-xs mb-2 font-medium">GEO Queries (AI Search)</p>
                        {topic.geo_queries.map((q, i) => (
                            <div key={i} className="bg-white/[0.02] rounded-md p-2 mb-1 border border-white/5">
                                <p className="text-xs text-gray-300">&ldquo;{q.query_text}&rdquo;</p>
                                {q.constraints.length > 0 && (
                                    <div className="flex gap-1 mt-1">
                                        {q.constraints.map((c, ci) => (
                                            <Badge key={ci} variant="outline" className="border-white/5 text-amber-400/70 text-[9px]">
                                                {c}
                                            </Badge>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Duration/CTA */}
                <div className="flex items-center justify-between text-xs text-gray-500 pt-1 border-t border-white/5">
                    {topic.target_duration_seconds && (
                        <span>⏱️ {Math.floor(topic.target_duration_seconds / 60)}:{String(topic.target_duration_seconds % 60).padStart(2, '0')}</span>
                    )}
                    {topic.cta && <span className="text-emerald-400/70">CTA: {topic.cta}</span>}
                </div>
            </CardContent>
        </Card>
    );
}

function LinkRow({
    link,
    topics,
}: {
    link: InternalLink;
    topics: TopicBlueprint[];
}) {
    const from = topics.find((t) => t.topic_id === link.from_topic_id);
    const to = topics.find((t) => t.topic_id === link.to_topic_id);

    const typeColors: Record<string, string> = {
        contextual: "text-blue-400",
        cta: "text-emerald-400",
        related: "text-amber-400",
    };

    return (
        <div className="flex items-center gap-2 text-xs py-1.5 px-3 rounded-md bg-white/[0.01] border border-white/5">
            <span className="text-gray-400 truncate max-w-[120px]" title={from?.title}>
                {from?.title?.slice(0, 25) || link.from_topic_id}
            </span>
            <span className="text-gray-600">→</span>
            <span className="text-gray-400 truncate max-w-[120px]" title={to?.title}>
                {to?.title?.slice(0, 25) || link.to_topic_id}
            </span>
            <Badge variant="outline" className={`ml-auto border-white/5 text-[9px] ${typeColors[link.link_type] || "text-gray-500"}`}>
                {link.link_type}
            </Badge>
            <span className="text-gray-500 truncate max-w-[150px]" title={link.anchor_text}>
                &ldquo;{link.anchor_text}&rdquo;
            </span>
        </div>
    );
}
