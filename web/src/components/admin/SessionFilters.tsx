/**
 * Session Filters Component
 * 
 * Interactive filters for browsing chat sessions by account/agent.
 * Fetches and displays session list with pagination.
 */
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';

interface Session {
    id: string;
    account_slug: string | null;
    agent_instance_slug: string | null;
    created_at: string;
    message_count: number;
}

interface SessionFiltersProps {
    apiUrl: string;
}

export function SessionFilters({ apiUrl }: SessionFiltersProps) {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [account, setAccount] = useState('');
    const [agent, setAgent] = useState('');
    const [total, setTotal] = useState(0);

    useEffect(() => {
        fetchSessions();
    }, [account, agent]);

    const fetchSessions = async () => {
        setLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams();
            if (account) params.append('account', account);
            if (agent) params.append('agent', agent);
            params.append('limit', '50');

            const response = await fetch(`${apiUrl}/api/admin/sessions?${params}`, {
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
            setSessions(data.sessions || []);
            setTotal(data.total || 0);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch sessions');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div class="bg-white shadow rounded-lg p-6">
            {/* Filters */}
            <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Account
                    </label>
                    <select
                        value={account}
                        onChange={(e) => setAccount((e.target as HTMLSelectElement).value)}
                        class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Accounts</option>
                        <option value="wyckoff">Wyckoff</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Agent
                    </label>
                    <select
                        value={agent}
                        onChange={(e) => setAgent((e.target as HTMLSelectElement).value)}
                        class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Agents</option>
                        <option value="wyckoff_info_chat1">wyckoff_info_chat1</option>
                    </select>
                </div>

                <div class="flex items-end">
                    <button
                        onClick={fetchSessions}
                        disabled={loading}
                        class="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Loading...' : 'Refresh'}
                    </button>
                </div>
            </div>

            {/* Error */}
            {error && (
                <div class="mb-4 bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
                    {error}
                </div>
            )}

            {/* Results Summary */}
            <div class="mb-4 text-sm text-gray-600">
                {loading ? 'Loading...' : `Found ${total} session(s)`}
            </div>

            {/* Sessions Table */}
            {!loading && sessions.length > 0 && (
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Session ID
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Account
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Agent
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Messages
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Created
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            {sessions.map((session) => (
                                <tr key={session.id} class="hover:bg-gray-50">
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                                        {session.id.substring(0, 8)}...
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {session.account_slug || '-'}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {session.agent_instance_slug || '-'}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {session.message_count}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(session.created_at).toLocaleString()}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                                        <a
                                            href={`/admin/sessions/${session.id}`}
                                            class="text-blue-600 hover:text-blue-800 font-medium"
                                        >
                                            View Details
                                        </a>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Empty State */}
            {!loading && sessions.length === 0 && !error && (
                <div class="text-center py-12 text-gray-500">
                    No sessions found
                </div>
            )}
        </div>
    );
}

