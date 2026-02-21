"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { listPipelines, STATUS_CONFIG, type PipelineStatusResponse } from "@/lib/api";

export default function RunsPage() {
    const [runs, setRuns] = useState<PipelineStatusResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchRuns = async () => {
            try {
                const data = await listPipelines();
                setRuns(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load");
            } finally {
                setLoading(false);
            }
        };
        fetchRuns();
        const interval = setInterval(fetchRuns, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="max-w-5xl mx-auto p-8 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-100">Pipeline Runs</h1>
                    <p className="text-sm text-gray-500">All blueprint generation runs</p>
                </div>
                <Button
                    asChild
                    className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white"
                >
                    <a href="/">+ New Blueprint</a>
                </Button>
            </div>

            {loading ? (
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-20 bg-white/5 rounded-lg animate-pulse" />
                    ))}
                </div>
            ) : error ? (
                <Card className="border-red-500/20 bg-red-500/5">
                    <CardContent className="p-6 text-center text-red-400">
                        <p>{error}</p>
                        <p className="text-sm text-gray-500 mt-1">
                            Make sure the backend is running at <code>http://localhost:8000</code>
                        </p>
                    </CardContent>
                </Card>
            ) : runs.length === 0 ? (
                <Card className="border-white/5 bg-white/[0.02]">
                    <CardContent className="p-12 text-center">
                        <p className="text-4xl mb-3">🧠</p>
                        <p className="text-gray-400">No pipeline runs yet</p>
                        <p className="text-sm text-gray-600 mt-1">
                            Start your first content blueprint from the{" "}
                            <a href="/" className="text-violet-400 underline">home page</a>
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-2">
                    {runs.map((run) => {
                        const cfg = STATUS_CONFIG[run.status];
                        return (
                            <a
                                key={run.run_id}
                                href={`/runs/${run.run_id}`}
                                className="block"
                            >
                                <Card className="border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors cursor-pointer">
                                    <CardContent className="py-4 px-5 flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <span className="text-xl">{cfg.icon}</span>
                                            <div>
                                                <p className="text-sm font-medium text-gray-200">
                                                    {run.run_id.slice(0, 8)}...
                                                </p>
                                                <p className="text-xs text-gray-500">
                                                    {new Date(run.created_at).toLocaleString()}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <span className="text-xs text-gray-500">{run.current_stage}</span>
                                            <Badge
                                                className={`${cfg.color} text-white text-xs`}
                                            >
                                                {cfg.label}
                                            </Badge>
                                        </div>
                                    </CardContent>
                                </Card>
                            </a>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
