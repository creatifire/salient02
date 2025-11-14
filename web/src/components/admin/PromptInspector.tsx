/**
 * Prompt Inspector Component
 * 
 * Displays prompt breakdown with expandable sections.
 * Shows which pieces were assembled and in what order for debugging.
 */
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';

interface PromptSection {
    name: string;
    position: number;
    char_count: number;
    source: string;
}

interface PromptBreakdown {
    sections: PromptSection[];
    total_char_count: number;
}

interface LLMRequestData {
    id: string;
    model: string;
    prompt_breakdown: PromptBreakdown | null;
    tool_calls: Array<{
        tool_name: string;
        args: Record<string, any>;
    }>;
    response: {
        input_tokens: number;
        output_tokens: number;
        total_tokens: number;
        cost: number;
        latency_ms: number;
    };
}

interface PromptInspectorProps {
    requestId: string;
    apiUrl: string;
    onClose: () => void;
}

export function PromptInspector({ requestId, apiUrl, onClose }: PromptInspectorProps) {
    const [data, setData] = useState<LLMRequestData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedSection, setExpandedSection] = useState<string | null>(null);

    useEffect(() => {
        fetchLLMRequest();
    }, [requestId]);

    const fetchLLMRequest = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${apiUrl}/api/admin/llm-requests/${requestId}`, {
                credentials: 'include' // Send session cookies
            });

            // Handle 401 - redirect to login
            if (response.status === 401) {
                window.location.href = '/admin/login';
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const requestData = await response.json();
            setData(requestData);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch LLM request');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div class="bg-white shadow rounded-lg p-6">
                <p class="text-center text-gray-500">Loading...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div class="bg-white shadow rounded-lg p-6">
                <div class="bg-red-50 border border-red-200 text-red-800 rounded p-4 text-sm">
                    {error}
                </div>
            </div>
        );
    }

    if (!data) {
        return null;
    }

    return (
        <div class="bg-white shadow rounded-lg sticky top-4">
            {/* Header */}
            <div class="p-4 border-b border-gray-200 flex items-center justify-between">
                <h3 class="font-bold text-gray-900">Prompt Inspector</h3>
                <button
                    onClick={onClose}
                    class="text-gray-400 hover:text-gray-600"
                >
                    ✕
                </button>
            </div>

            {/* Stats */}
            <div class="p-4 border-b border-gray-200 space-y-2 text-sm">
                <div><strong>Model:</strong> {data.model}</div>
                <div><strong>Tokens:</strong> {data.response.input_tokens} → {data.response.output_tokens}</div>
                <div><strong>Cost:</strong> ${data.response.cost.toFixed(5)}</div>
                <div><strong>Latency:</strong> {data.response.latency_ms}ms</div>
            </div>

            {/* Tool Calls */}
            {data.tool_calls.length > 0 && (
                <div class="p-4 border-b border-gray-200">
                    <h4 class="font-medium text-gray-900 mb-2 text-sm">Tool Calls ({data.tool_calls.length})</h4>
                    <div class="space-y-2">
                        {data.tool_calls.map((call, idx) => (
                            <div key={idx} class="bg-yellow-50 border border-yellow-200 rounded p-2 text-xs">
                                <div class="font-medium text-yellow-900">{call.tool_name}</div>
                                <pre class="mt-1 text-yellow-800 overflow-x-auto">
                                    {JSON.stringify(call.args, null, 2)}
                                </pre>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Prompt Breakdown */}
            {data.prompt_breakdown && (
                <div class="p-4">
                    <h4 class="font-medium text-gray-900 mb-2 text-sm">
                        Prompt Breakdown ({data.prompt_breakdown.total_char_count.toLocaleString()} chars)
                    </h4>
                    <div class="space-y-2">
                        {data.prompt_breakdown.sections.map((section) => (
                            <div key={section.name} class="border border-gray-200 rounded overflow-hidden">
                                <button
                                    onClick={() => setExpandedSection(
                                        expandedSection === section.name ? null : section.name
                                    )}
                                    class="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between text-sm"
                                >
                                    <div>
                                        <div class="font-medium text-gray-900">
                                            {section.position}. {section.name}
                                        </div>
                                        <div class="text-xs text-gray-500 mt-1">
                                            {section.char_count.toLocaleString()} chars • {section.source}
                                        </div>
                                    </div>
                                    <span class="text-gray-400">
                                        {expandedSection === section.name ? '▼' : '▶'}
                                    </span>
                                </button>
                                
                                {expandedSection === section.name && (
                                    <div class="p-3 bg-white border-t border-gray-200">
                                        <p class="text-xs text-gray-600">
                                            Section content would be displayed here.
                                            (Content not stored in meta - only structure/stats)
                                        </p>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {!data.prompt_breakdown && (
                <div class="p-4 text-center text-sm text-gray-500">
                    No prompt breakdown available
                </div>
            )}
        </div>
    );
}

