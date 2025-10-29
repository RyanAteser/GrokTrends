import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, Search, Plus, X, Calendar, BarChart2, Sparkles } from 'lucide-react';
import { Analytics } from "@vercel/analytics/react"

export const API_BASE =
    import.meta.env.VITE_API_BASE || "http://localhost:8000"; // dev fallback


const COLORS = ['#818cf8', '#c084fc', '#38bdf8', '#fb7185', '#34d399', '#fbbf24', '#f87171', '#60a5fa'];

export default function App() {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedTopics, setSelectedTopics] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [timeRange, setTimeRange] = useState(168);
    const [stats, setStats] = useState({});
    const [popularTopics, setPopularTopics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [email, setEmail] = useState('');
    const [signupStatus, setSignupStatus] = useState(null);
    const [signupCount, setSignupCount] = useState(0);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        Promise.all([
            fetch(`${API_BASE}/api/trends?days=7&limit=20`).then(r => r.json()),
            fetch(`${API_BASE}/api/interest-count`).then(r => r.json())
        ])
            .then(([trendsData, countData]) => {
                setPopularTopics(trendsData.trending_topics || []);
                setStats(trendsData.stats || {});
                setSignupCount(countData.count || 0);
                const top3 = (trendsData.trending_topics || []).slice(0, 3).map(t => t.topic);
                setSelectedTopics(top3);
                setLoading(false);
            })
            .catch(err => { console.error(err); setLoading(false); });
    }, []);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;
        try {
            const res = await fetch(`${API_BASE}/api/topics/search?q=${encodeURIComponent(searchQuery)}&limit=10`);
            const data = await res.json();
            setSearchResults(data.results || []);
        } catch (err) { console.error(err); }
    };

    const addTopic = (topic) => {
        if (selectedTopics.includes(topic)) return;
        if (selectedTopics.length >= 5) { alert('Maximum 5 topics'); return; }
        setSelectedTopics([...selectedTopics, topic]);
        setSearchQuery('');
        setSearchResults([]);
    };

    const removeTopic = (topic) => {
        setSelectedTopics(selectedTopics.filter(t => t !== topic));
    };

    useEffect(() => {
        if (selectedTopics.length === 0) { setChartData([]); return; }
        const params = new URLSearchParams();
        selectedTopics.forEach(t => params.append('topics', t));
        params.set('hours', timeRange);
        params.set('metric', 'mentions');
        params.set('normalize', 'global'); // or 'none' or 'per_topic'

        fetch(`${API_BASE}/api/interest?${params}`)
            .then(r => r.json())
            .then(data => {
                const series = (data.series || []).map(item => {
                    const point = { time: new Date(item.time).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: timeRange <= 48 ? 'numeric' : undefined }) };
                    selectedTopics.forEach(topic => { point[topic] = item[topic] || 0; });
                    return point;
                });
                setChartData(series);
            })
            .catch(err => console.error(err));
    }, [selectedTopics, timeRange]);

    const handleEmailSignup = async (e) => {
        e.preventDefault();
        if (!email) return;
        setSubmitting(true);
        setSignupStatus(null);
        try {
            const response = await fetch(`${API_BASE}/api/interest-signup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await response.json();
            if (response.ok) {
                setSignupStatus({ type: 'success', message: data.message });
                setSignupCount(data.total_signups);
                setEmail('');
            } else {
                setSignupStatus({ type: 'error', message: data.detail || 'Error' });
            }
        } catch (err) {
            setSignupStatus({ type: 'error', message: 'Failed. Try again.' });
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', fontSize: '20px', fontWeight: '600' }}>Loading...</div>;
    }

    return (
        <div style={{ minHeight: '100vh', background: '#f8fafc', color: '#0f172a', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
            <div style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', padding: '12px 20px', textAlign: 'center', color: 'white', fontSize: '14px' }}>
                <Sparkles size={16} style={{ display: 'inline', marginRight: '8px' }} />
                <strong>Beta Demo</strong> • Sample data • <a href="#interest" style={{ color: 'white', marginLeft: '8px', textDecoration: 'underline', fontWeight: '600' }}>Want real-time?</a>
            </div>

            <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px 20px' }}>
                <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                    <h1 style={{ fontSize: '48px', fontWeight: '800', margin: '0 0 8px 0', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Grok Trends</h1>
                    <p style={{ fontSize: '18px', color: '#64748b', margin: 0 }}>Explore • Compare • Discover patterns in Grok queries</p>
                </div>

                <div style={{ maxWidth: '800px', margin: '0 auto 40px' }}>
                    <div onSubmit={handleSearch}>
                        <div style={{ background: 'white', borderRadius: '24px', padding: '8px 24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', display: 'flex', alignItems: 'center', gap: '12px', border: '1px solid #e2e8f0' }}>
                            <Search size={24} style={{ color: '#64748b' }} />
                            <input type="text" placeholder="Search topics (e.g., 'bitcoin', 'python')" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSearch(e)} style={{ flex: 1, border: 'none', outline: 'none', fontSize: '16px', padding: '12px 0', background: 'transparent' }} />
                            <button onClick={handleSearch} style={{ background: '#667eea', color: 'white', border: 'none', borderRadius: '16px', padding: '10px 24px', fontWeight: '600', cursor: 'pointer' }}>Search</button>
                        </div>
                    </div>

                    {searchResults.length > 0 && (
                        <div style={{ background: 'white', marginTop: '8px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0', maxHeight: '300px', overflowY: 'auto' }}>
                            {searchResults.map(result => (
                                <button key={result.topic} onClick={() => addTopic(result.topic)} style={{ width: '100%', padding: '12px 20px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9' }} onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'} onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                                    <div>
                                        <div style={{ fontWeight: '600', marginBottom: '4px' }}>{result.topic}</div>
                                        <div style={{ fontSize: '13px', color: '#64748b' }}>{result.category} • {result.mentions.toLocaleString()} mentions</div>
                                    </div>
                                    <Plus size={20} style={{ color: '#667eea' }} />
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {selectedTopics.length > 0 && (
                    <div style={{ maxWidth: '1000px', margin: '0 auto 24px', display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center' }}>
                        {selectedTopics.map((topic, idx) => (
                            <div key={topic} style={{ background: 'white', border: `2px solid ${COLORS[idx % COLORS.length]}`, borderRadius: '20px', padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: '600' }}>
                                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: COLORS[idx % COLORS.length] }} />
                                {topic}
                                <button onClick={() => removeTopic(topic)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '0', display: 'flex', alignItems: 'center' }}><X size={16} style={{ color: '#64748b' }} /></button>
                            </div>
                        ))}
                    </div>
                )}

                <div style={{ maxWidth: '1000px', margin: '0 auto 32px', display: 'flex', justifyContent: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    {[{ label: 'Past hour', value: 1 }, { label: 'Past 4 hours', value: 4 }, { label: 'Past day', value: 24 }, { label: 'Past 7 days', value: 168 }, { label: 'Past 30 days', value: 720 }].map(range => (
                        <button key={range.value} onClick={() => setTimeRange(range.value)} style={{ background: timeRange === range.value ? '#667eea' : 'white', color: timeRange === range.value ? 'white' : '#475569', border: '1px solid #e2e8f0', padding: '8px 16px', borderRadius: '8px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>{range.label}</button>
                    ))}
                </div>

                <div style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '32px', maxWidth: '1000px', margin: '0 auto 32px' }}>
                    <div style={{ marginBottom: '20px' }}>
                        <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '4px' }}>Interest over time</h2>
                        <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>Numbers represent relative interest (0-100)</p>
                    </div>
                    {chartData.length > 0 && selectedTopics.length > 0 ? (
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="time" stroke="#94a3b8" style={{ fontSize: '12px' }} />
                                <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} domain={[0, 100]} />
                                <Tooltip contentStyle={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
                                <Legend />
                                {selectedTopics.map((topic, idx) => <Line key={topic} type="monotone" dataKey={topic} stroke={COLORS[idx % COLORS.length]} strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />)}
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: '16px' }}>{selectedTopics.length === 0 ? 'Search and select topics to compare' : 'Loading...'}</div>
                    )}
                </div>

                <div style={{ maxWidth: '1000px', margin: '0 auto 48px' }}>
                    <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '16px' }}>Popular right now</h2>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                        {popularTopics.slice(0, 12).map(topic => (
                            <button key={topic.topic} onClick={() => addTopic(topic.topic)} disabled={selectedTopics.includes(topic.topic)} style={{ background: selectedTopics.includes(topic.topic) ? '#f1f5f9' : 'white', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px', textAlign: 'left', cursor: selectedTopics.includes(topic.topic) ? 'default' : 'pointer', opacity: selectedTopics.includes(topic.topic) ? 0.6 : 1 }} onMouseEnter={(e) => { if (!selectedTopics.includes(topic.topic)) e.currentTarget.style.borderColor = '#667eea'; }} onMouseLeave={(e) => e.currentTarget.style.borderColor = '#e2e8f0'}>
                                <div style={{ fontWeight: '600', marginBottom: '6px', fontSize: '14px' }}>{topic.topic}</div>
                                <div style={{ fontSize: '12px', color: '#64748b' }}>{topic.mentions.toLocaleString()} mentions</div>
                                <div style={{ fontSize: '12px', color: topic.growth >= 0 ? '#10b981' : '#ef4444', fontWeight: '600', marginTop: '4px' }}>{topic.growth >= 0 ? '↗' : '↘'} {Math.abs(Math.round(topic.growth))}%</div>
                            </button>
                        ))}
                    </div>
                </div>

                <div id="interest" style={{ maxWidth: '800px', margin: '0 auto', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', borderRadius: '16px', padding: '40px', textAlign: 'center', color: 'white' }}>
                    <h2 style={{ fontSize: '32px', fontWeight: '800', marginBottom: '16px' }}>Want real-time data?</h2>
                    <p style={{ fontSize: '18px', marginBottom: '32px', opacity: 0.95, lineHeight: '1.6' }}>This demo uses sample data.</p>
                    <div style={{ maxWidth: '500px', margin: '0 auto' }}>
                        <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                            <input type="email" placeholder="Enter your email" value={email} onChange={(e) => setEmail(e.target.value)} required style={{ flex: 1, padding: '14px 20px', borderRadius: '8px', border: 'none', fontSize: '16px', outline: 'none' }} />
                            <button onClick={handleEmailSignup} disabled={submitting} style={{ background: 'white', color: '#667eea', padding: '14px 28px', borderRadius: '8px', border: 'none', fontWeight: '700', fontSize: '16px', cursor: submitting ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap' }}>{submitting ? 'Submitting...' : 'Count me in!'}</button>
                        </div>
                        {signupStatus && (
                            <div style={{ padding: '12px', borderRadius: '8px', background: signupStatus.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)', fontSize: '14px', fontWeight: '600' }}>{signupStatus.message}</div>
                        )}
                    </div>
                    <div style={{ marginTop: '32px', padding: '20px', background: 'rgba(0, 0, 0, 0.2)', borderRadius: '12px', fontSize: '14px' }}>
                        <div style={{ fontSize: '24px', fontWeight: '800', marginBottom: '8px' }}>{signupCount} {signupCount === 1 ? 'person' : 'people'} interested</div>
                        <div style={{ opacity: 0.9 }}>Goal: 555 users  to launch • Current: {signupCount}</div>
                        <div style={{ marginTop: '12px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '999px', height: '8px', overflow: 'hidden' }}><div style={{ background: 'white', height: '100%', width: `${Math.min((signupCount / 12) * 100, 100)}%`, transition: 'width 0.3s' }} /></div>
                    </div>
                </div>
            </div>
            <Analytics />
        </div>
    );
}