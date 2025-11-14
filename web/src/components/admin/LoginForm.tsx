import { h } from 'preact';
import { useState } from 'preact/hooks';

interface LoginFormProps {
    apiUrl: string;
}

export function LoginForm({ apiUrl }: LoginFormProps) {
    const [username, setUsername] = useState('admin');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: Event) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${apiUrl}/api/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include', // Important: send cookies
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Login failed');
            }

            // Redirect to sessions page
            window.location.href = '/admin/sessions';
        } catch (err: any) {
            setError(err.message || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} class="space-y-4">
            {error && (
                <div class="bg-red-50 border border-red-200 text-red-800 rounded p-3 text-sm">
                    {error}
                </div>
            )}
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Username
                </label>
                <input
                    type="text"
                    value={username}
                    onInput={(e) => setUsername((e.target as HTMLInputElement).value)}
                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                />
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Password
                </label>
                <input
                    type="password"
                    value={password}
                    onInput={(e) => setPassword((e.target as HTMLInputElement).value)}
                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                />
            </div>

            <button
                type="submit"
                disabled={loading}
                class="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
                {loading ? 'Logging in...' : 'Login'}
            </button>
        </form>
    );
}

