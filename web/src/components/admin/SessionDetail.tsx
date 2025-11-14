/**
 * Session Detail Component
 * 
 * Displays conversation timeline with expandable LLM metadata.
 * Shows user/assistant messages with tool calls and prompt breakdowns.
 */
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { PromptInspector } from './PromptInspector';

interface Message {
    id: string;
    role: string;
    content: string;
    created_at: string;
    llm_request_id: string | null;
    meta?: {
        model?: string;
        input_tokens?: number;
        output_tokens?: number;
        cost?: number;
        tool_calls?: Array<{
            tool_name: string;
            args: Record<string, any>;
        }>;
    };
}

interface SessionDetailProps {
    sessionId: string;
    apiUrl: string;
}

export function SessionDetail({ sessionId, apiUrl }: SessionDetailProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);

    useEffect(() => {
        fetchMessages();
    }, [sessionId]);

    const fetchMessages = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${apiUrl}/api/admin/sessions/${sessionId}/messages`, {
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

            const data = await response.json();
            setMessages(data.messages || []);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch messages');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div class="text-center py-12 text-gray-500">Loading conversation...</div>;
    }

    if (error) {
        return (
            <div class="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
                {error}
            </div>
        );
    }

    return (
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Conversation Timeline */}
            <div class="lg:col-span-2 space-y-4">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        class={`p-4 rounded-lg shadow ${
                            message.role === 'human'
                                ? 'bg-blue-50 border-l-4 border-blue-500'
                                : 'bg-green-50 border-l-4 border-green-500'
                        }`}
                    >
                        {/* Message Header */}
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm font-medium text-gray-900 capitalize">
                                {message.role}
                            </span>
                            <span class="text-xs text-gray-500">
                                {new Date(message.created_at).toLocaleString()}
                            </span>
                        </div>

                        {/* Message Content */}
                        <p class="text-gray-800 whitespace-pre-wrap">{message.content}</p>

                        {/* LLM Metadata (Assistant Only) */}
                        {message.role === 'assistant' && message.meta && (
                            <div class="mt-4 pt-4 border-t border-gray-200">
                                <div class="flex items-center justify-between text-xs text-gray-600">
                                    <div class="space-x-4">
                                        <span>Model: <strong>{message.meta.model}</strong></span>
                                        <span>Tokens: <strong>{message.meta.input_tokens} → {message.meta.output_tokens}</strong></span>
                                        <span>Cost: <strong>${message.meta.cost?.toFixed(5)}</strong></span>
                                    </div>
                                    {message.llm_request_id && (
                                        <button
                                            onClick={() => setSelectedRequestId(message.llm_request_id)}
                                            class="text-blue-600 hover:text-blue-800 font-medium"
                                        >
                                            View Prompt →
                                        </button>
                                    )}
                                </div>

                                {/* Tool Calls */}
                                {message.meta.tool_calls && message.meta.tool_calls.length > 0 && (
                                    <div class="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                                        <p class="text-xs font-medium text-yellow-900 mb-1">Tool Calls:</p>
                                        <ul class="text-xs text-yellow-800 space-y-1">
                                            {message.meta.tool_calls.map((call, idx) => (
                                                <li key={idx}>
                                                    <strong>{call.tool_name}</strong>({JSON.stringify(call.args)})
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Prompt Inspector Sidebar */}
            <div class="lg:col-span-1">
                {selectedRequestId ? (
                    <PromptInspector
                        requestId={selectedRequestId}
                        apiUrl={apiUrl}
                        onClose={() => setSelectedRequestId(null)}
                    />
                ) : (
                    <div class="bg-white shadow rounded-lg p-6 text-center text-gray-500">
                        Select a message to view prompt breakdown
                    </div>
                )}
            </div>
        </div>
    );
}

