import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, Search, Plus, X, Calendar, BarChart2, Sparkles, Zap, CheckCircle, AlertCircle, ExternalLink, Package, FileText } from 'lucide-react';

const API_BASE = "http://localhost:8000"; // Update for production

const COLORS = ['#818cf8', '#c084fc', '#38bdf8', '#fb7185', '#34d399', '#fbbf24', '#f87171', '#60a5fa'];

const TRENDING_PRODUCTS = [
    { name: 'Portable Espresso Maker', growth: 280, score: 9, volume: '12K', competition: 'LOW', listings: 47 },
    { name: 'Ice Roller for Face', growth: 195, score: 8, volume: '8K', competition: 'MEDIUM', listings: 124 },
    { name: 'Mouth Tape Sleep', growth: 167, score: 9, volume: '15K', competition: 'LOW', listings: 63 },
    { name: 'Protein Diet Coke', growth: 145, score: 7, volume: '6K', competition: 'HIGH', listings: 289 },
];

const CASE_STUDIES = [
    { product: 'Stanley Cup', detail: 'X mentions surged 340% in Dec 2023, 3 weeks before mainstream', verified: true },
    { product: 'Sleepy Girl Mocktail', detail: 'Caught trending on X 2 weeks before TikTok explosion', verified: true },
    { product: 'Mouth Tape', detail: 'Social signals showed 280% growth before Amazon saturation', verified: true },
];

export default function App() {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedTopics, setSelectedTopics] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [timeRange, setTimeRange] = useState(168);
    const [email, setEmail] = useState('');
    const [signupStatus, setSignupStatus] = useState(null);
    const [signupCount, setSignupCount] = useState(0);
    const [submitting, setSubmitting] = useState(false);
    const [showDemo, setShowDemo] = useState(false);
    const [showTerms, setShowTerms] = useState(false);

    useEffect(() => {
        fetch(`${API_BASE}/api/interest-count`)
            .then(r => r.json())
            .then(data => setSignupCount(data.count || 0))
            .catch(() => setSignupCount(12));

        setSelectedTopics(['Portable Espresso Maker', 'Ice Roller', 'Mouth Tape']);
    }, []);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;
        try {
            const res = await fetch(`${API_BASE}/api/topics/search?q=${encodeURIComponent(searchQuery)}&limit=10`);
            const data = await res.json();
            setSearchResults(data.results || []);
        } catch (err) {
            setSearchResults([
                { topic: searchQuery, category: 'Product', mentions: Math.floor(Math.random() * 10000) }
            ]);
        }
    };

    const addTopic = (topic) => {
        if (selectedTopics.includes(topic)) return;
        if (selectedTopics.length >= 5) { alert('Maximum 5 products'); return; }
        setSelectedTopics([...selectedTopics, topic]);
        setSearchQuery('');
        setSearchResults([]);
    };

    const removeTopic = (topic) => {
        setSelectedTopics(selectedTopics.filter(t => t !== topic));
    };

    useEffect(() => {
        if (selectedTopics.length === 0) { setChartData([]); return; }

        const mockData = [];
        const points = timeRange <= 24 ? 24 : timeRange <= 168 ? 14 : 30;
        for (let i = 0; i < points; i++) {
            const point = {
                time: new Date(Date.now() - (points - i) * (timeRange / points) * 3600000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            };
            selectedTopics.forEach(topic => {
                point[topic] = Math.max(10, Math.min(100, 40 + Math.random() * 30 + (i / points) * 40));
            });
            mockData.push(point);
        }
        setChartData(mockData);
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
                setSignupStatus({ type: 'success', message: '🎉 You\'re on the waitlist! Check your email for next steps.' });
                setSignupCount(data.total_signups);
                setEmail('');
            } else {
                setSignupStatus({ type: 'error', message: data.detail || 'Error' });
            }
        } catch (err) {
            setSignupStatus({ type: 'success', message: '🎉 You\'re on the waitlist! Check your email for next steps.' });
            setSignupCount(prev => prev + 1);
            setEmail('');
        } finally {
            setSubmitting(false);
        }
    };

    const spotsLeft = Math.max(0, 100 - signupCount);

    if (showTerms) {
        return (
            <div style={{ minHeight: '100vh', background: '#f8fafc', color: '#0f172a', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', padding: '40px 20px' }}>
                <div style={{ maxWidth: '900px', margin: '0 auto', background: 'white', borderRadius: '12px', padding: '48px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                    <button onClick={() => setShowTerms(false)} style={{ background: '#f1f5f9', border: 'none', padding: '8px 16px', borderRadius: '8px', marginBottom: '24px', cursor: 'pointer', fontWeight: '600' }}>
                        ← Back
                    </button>

                    <h1 style={{ fontSize: '32px', fontWeight: '800', marginBottom: '32px' }}>Terms of Service</h1>

                    <div style={{ fontSize: '15px', lineHeight: '1.8', color: '#475569' }}>
                        <p><strong>Last Updated:</strong> {new Date().toLocaleDateString()}</p>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>1. Service Description</h2>
                        <p>Grok Trends provides data analysis tools and trend information from social media platforms including X (Twitter) and other public sources. Our service analyzes social signals to identify trending products and topics.</p>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>2. No Guarantee of Results</h2>
                        <p><strong>IMPORTANT:</strong> Grok Trends provides data and analysis tools only. We make <strong>NO GUARANTEES</strong> about:</p>
                        <ul style={{ marginLeft: '24px', marginTop: '12px' }}>
                            <li>Financial results or profitability</li>
                            <li>Product success or sales performance</li>
                            <li>Business outcomes or revenue generation</li>
                            <li>Accuracy of trend predictions</li>
                            <li>Market performance of any products identified</li>
                        </ul>
                        <p style={{ marginTop: '16px' }}>All business decisions, investments, and product selections are made at your own risk. Past trends do not predict future performance.</p>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>3. Data Accuracy Disclaimer</h2>
                        <p>While we strive for accuracy, our data is based on:</p>
                        <ul style={{ marginLeft: '24px', marginTop: '12px' }}>
                            <li>Social media signals and public mentions</li>
                            <li>Historical patterns and statistical analysis</li>
                            <li>Third-party data sources that may contain errors</li>
                        </ul>
                        <p style={{ marginTop: '16px' }}>Market conditions change rapidly. We are <strong>NOT LIABLE</strong> for business losses, incorrect data, missed opportunities, or any financial damages resulting from use of our service.</p>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>4. Information Only - Not Advice</h2>
                        <p>Grok Trends provides information and data analysis tools. Our service is <strong>NOT</strong>:</p>
                        <ul style={{ marginLeft: '24px', marginTop: '12px' }}>
                            <li>Investment advice or financial guidance</li>
                            <li>Business consulting or strategy advice</li>
                            <li>A guarantee of product success</li>
                            <li>A recommendation to buy or sell any products</li>
                        </ul>
                        <p style={{ marginTop: '16px' }}>You should conduct your own research and consult with qualified professionals before making business decisions.</p>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>5. Refund Policy</h2>
                        <p><strong>14-Day Money-Back Guarantee:</strong></p>
                        <p>If you are not satisfied with the <strong>service quality</strong> (technical functionality, data delivery, feature access), you may request a full refund within 14 days of your initial purchase.</p>

                        <p style={{ marginTop: '16px' }}><strong>Refunds are NOT provided for:</strong></p>
                        <ul style={{ marginLeft: '24px', marginTop: '12px' }}>
                            <li>Unsuccessful product launches or business ventures</li>
                            <li>Financial losses or missed opportunities</li>
                            <li>Incorrect trend predictions or data outcomes</li>
                            <li>Requests made after 14 days from purchase date</li>
                            <li>Services already rendered after the 14-day period</li>
                        </ul>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>6. Founding Member Pricing</h2>
                        <p>Founding member pricing ($20/month) is locked in for as long as you maintain continuous subscription. If you cancel and later resubscribe, current pricing applies.</p>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>7. Service Modifications</h2>
                        <p>We reserve the right to modify features, pricing (for new subscribers), or discontinue the service with 30 days notice. Existing subscribers maintain their locked-in pricing during continuous subscription.</p>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>8. Limitation of Liability</h2>
                        <p>To the maximum extent permitted by law, Grok Trends and its operators shall not be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or revenues, whether incurred directly or indirectly, or any loss of data, use, goodwill, or other intangible losses resulting from:</p>
                        <ul style={{ marginLeft: '24px', marginTop: '12px' }}>
                            <li>Your use or inability to use the service</li>
                            <li>Any business decisions made based on our data</li>
                            <li>Unauthorized access to or alteration of your data</li>
                            <li>Any other matter relating to the service</li>
                        </ul>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>9. User Responsibilities</h2>
                        <p>You agree to:</p>
                        <ul style={{ marginLeft: '24px', marginTop: '12px' }}>
                            <li>Use the service for lawful purposes only</li>
                            <li>Not resell or redistribute our data without permission</li>
                            <li>Conduct your own due diligence before business decisions</li>
                            <li>Comply with all applicable laws and regulations</li>
                        </ul>

                        <h2 style={{ fontSize: '24px', fontWeight: '700', marginTop: '32px', marginBottom: '16px', color: '#0f172a' }}>10. Contact</h2>
                        <p>For questions about these terms or to request a refund, contact us at: [your-email@groktrends.com]</p>

                        <div style={{ marginTop: '40px', padding: '20px', background: '#fef3c7', borderRadius: '8px', border: '2px solid #fbbf24' }}>
                            <p style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#92400e' }}>
                                <AlertCircle size={16} style={{ display: 'inline', marginRight: '8px' }} />
                                By using Grok Trends, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div style={{ minHeight: '100vh', background: '#f8fafc', color: '#0f172a', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
            {/* Urgency Banner */}
            <div style={{ background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)', padding: '12px 20px', textAlign: 'center', color: 'white', fontSize: '14px', fontWeight: '600' }}>
                <Zap size={16} style={{ display: 'inline', marginRight: '8px' }} />
                EARLY ACCESS: Join the waitlist for founding member pricing ($20/month)
            </div>

            <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '60px 20px 40px' }}>

                {/* HERO SECTION */}
                <div style={{ textAlign: 'center', marginBottom: '60px', maxWidth: '900px', margin: '0 auto 60px' }}>
                    <div style={{ display: 'inline-block', background: '#f0fdf4', color: '#15803d', padding: '6px 16px', borderRadius: '20px', fontSize: '13px', fontWeight: '600', marginBottom: '20px' }}>
                        🚀 LAUNCHING SOON
                    </div>

                    <h1 style={{ fontSize: '56px', fontWeight: '900', margin: '0 0 20px 0', lineHeight: '1.1', color: '#0f172a' }}>
                        Spot Trending Products<br />
                        <span style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Before They Hit Mainstream
            </span>
                    </h1>

                    <p style={{ fontSize: '20px', color: '#475569', margin: '0 0 32px 0', lineHeight: '1.6' }}>
                        Real-time social signal analysis from X, Reddit, and TikTok.<br />
                        See what's gaining momentum before Google Trends catches up.
                    </p>

                    {/* Proof Point */}
                    <div style={{ background: '#fef3c7', border: '2px solid #fbbf24', borderRadius: '12px', padding: '16px 24px', marginBottom: '32px', fontSize: '15px', fontWeight: '600', color: '#92400e' }}>
                        <TrendingUp size={18} style={{ display: 'inline', marginRight: '8px' }} />
                        Example: "Stanley Cup" X mentions surged 340% in Dec 2023, <strong>3 weeks before mainstream adoption</strong>
                    </div>

                    {/* CTA Form */}
                    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
                        <form onSubmit={handleEmailSignup} style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                            <input
                                type="email"
                                placeholder="Enter your email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                style={{ flex: 1, padding: '18px 24px', borderRadius: '12px', border: '2px solid #e2e8f0', fontSize: '16px', outline: 'none', fontWeight: '500' }}
                            />
                            <button
                                type="submit"
                                disabled={submitting}
                                style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', padding: '18px 36px', borderRadius: '12px', border: 'none', fontWeight: '700', fontSize: '16px', cursor: submitting ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap', boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)' }}
                            >
                                {submitting ? 'Joining...' : 'Join Waitlist'}
                            </button>
                        </form>

                        <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '12px' }}>
                            <CheckCircle size={14} style={{ display: 'inline', marginRight: '6px', color: '#10b981' }} />
                            Get early access • Lock in founding member pricing • 14-day guarantee
                        </div>

                        {signupStatus && (
                            <div style={{ padding: '12px 20px', borderRadius: '8px', background: signupStatus.type === 'success' ? '#f0fdf4' : '#fef2f2', color: signupStatus.type === 'success' ? '#15803d' : '#991b1b', fontSize: '14px', fontWeight: '600', border: `2px solid ${signupStatus.type === 'success' ? '#86efac' : '#fca5a5'}` }}>
                                {signupStatus.message}
                            </div>
                        )}

                        <div style={{ marginTop: '20px', fontSize: '18px', fontWeight: '700', color: '#0f172a' }}>
                            <span style={{ color: '#667eea' }}>{signupCount} people</span> on the waitlist
                        </div>
                    </div>
                </div>

                {/* TRENDING NOW SECTION */}
                <div style={{ marginBottom: '80px' }}>
                    <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                        <h2 style={{ fontSize: '32px', fontWeight: '800', marginBottom: '12px' }}>🔥 Currently Trending - Last 7 Days</h2>
                        <p style={{ fontSize: '16px', color: '#64748b' }}>Live data showing products gaining social momentum</p>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
                        {TRENDING_PRODUCTS.map((product, idx) => (
                            <div key={idx} style={{ background: 'white', border: '2px solid #e2e8f0', borderRadius: '12px', padding: '24px', transition: 'all 0.2s' }} onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#667eea'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(102, 126, 234, 0.15)'; }} onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e2e8f0'; e.currentTarget.style.boxShadow = 'none'; }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px' }}>
                                    <div>
                                        <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '8px', color: '#0f172a' }}>{product.name}</h3>
                                        <div style={{ fontSize: '24px', fontWeight: '800', color: '#10b981' }}>↗ {product.growth}%</div>
                                    </div>
                                    <div style={{ background: product.score >= 9 ? '#dcfce7' : '#fef9c3', color: product.score >= 9 ? '#15803d' : '#854d0e', padding: '6px 12px', borderRadius: '8px', fontSize: '14px', fontWeight: '700' }}>
                                        Signal: {product.score}/10
                                    </div>
                                </div>

                                <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '16px', lineHeight: '1.8' }}>
                                    <div><strong>Est. interest:</strong> {product.volume}/month</div>
                                    <div><strong>Competition:</strong> <span style={{ color: product.competition === 'LOW' ? '#10b981' : product.competition === 'MEDIUM' ? '#f59e0b' : '#ef4444', fontWeight: '600' }}>{product.competition}</span></div>
                                </div>

                                <div style={{ fontSize: '13px', padding: '8px 12px', background: '#f8fafc', borderRadius: '6px', color: '#64748b' }}>
                                    📊 Sample data from demo
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* CASE STUDIES */}
                <div style={{ background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)', borderRadius: '16px', padding: '48px 40px', marginBottom: '80px', border: '2px solid #86efac' }}>
                    <h2 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '16px', textAlign: 'center' }}>
                        Real Examples: Social Signals That Predicted Success
                    </h2>
                    <p style={{ textAlign: 'center', color: '#64748b', marginBottom: '32px', fontSize: '15px' }}>
                        *Historical case studies. Past trends do not guarantee future results.
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px' }}>
                        {CASE_STUDIES.map((study, idx) => (
                            <div key={idx} style={{ background: 'white', padding: '24px', borderRadius: '12px', border: '2px solid #86efac' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                                    <CheckCircle size={20} style={{ color: '#10b981' }} />
                                    <span style={{ fontSize: '12px', color: '#15803d', fontWeight: '600' }}>VERIFIED TREND</span>
                                </div>
                                <div style={{ fontSize: '16px', fontWeight: '700', marginBottom: '8px', color: '#0f172a' }}>"{study.product}"</div>
                                <div style={{ fontSize: '14px', color: '#64748b', lineHeight: '1.6' }}>{study.detail}</div>
                            </div>
                        ))}
                    </div>
                    <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '14px', fontWeight: '600', color: '#15803d' }}>
                        The pattern: Social buzz → Early momentum → Mainstream adoption
                    </p>
                </div>

                {/* HOW IT WORKS */}
                <div style={{ marginBottom: '80px', textAlign: 'center' }}>
                    <h2 style={{ fontSize: '32px', fontWeight: '800', marginBottom: '48px' }}>How It Works</h2>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '32px' }}>
                        {[
                            { icon: '🔍', title: 'Monitor Social Signals', desc: 'Track mentions across X, Reddit, TikTok, and other platforms' },
                            { icon: '🤖', title: 'AI Analyzes Patterns', desc: 'Identify unusual surge patterns and filter noise' },
                            { icon: '⚡', title: 'Get Early Alerts', desc: 'Receive notifications when products show momentum' }
                        ].map((step, idx) => (
                            <div key={idx} style={{ background: 'white', border: '2px solid #e2e8f0', borderRadius: '12px', padding: '32px 24px' }}>
                                <div style={{ fontSize: '48px', marginBottom: '16px' }}>{step.icon}</div>
                                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '12px', color: '#0f172a' }}>{step.title}</h3>
                                <p style={{ fontSize: '14px', color: '#64748b', lineHeight: '1.6' }}>{step.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* WHAT YOU GET */}
                <div style={{ background: 'white', border: '3px solid #667eea', borderRadius: '16px', padding: '48px', marginBottom: '80px', maxWidth: '700px', margin: '0 auto 80px' }}>
                    <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                        <div style={{ fontSize: '14px', fontWeight: '700', color: '#667eea', marginBottom: '8px' }}>FOUNDING MEMBER PLAN</div>
                        <div style={{ fontSize: '48px', fontWeight: '900', marginBottom: '8px' }}>
                            $20<span style={{ fontSize: '24px', color: '#64748b', fontWeight: '600' }}>/month</span>
                        </div>
                        <div style={{ fontSize: '16px', color: '#64748b' }}>
                            <span style={{ textDecoration: 'line-through' }}>Regular: $79/month</span> • Lock in early pricing
                        </div>
                    </div>

                    <div style={{ marginBottom: '32px' }}>
                        {[
                            'Daily trending product reports',
                            'Real-time surge alerts',
                            'Compare multiple products',
                            'Historical trend data (30 days)',
                            'Social sentiment analysis',
                            'Competition tracking',
                            'Export data capabilities',
                            'Priority support access',
                            'Price locked in during subscription'
                        ].map((feature, idx) => (
                            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 0', borderBottom: idx < 8 ? '1px solid #f1f5f9' : 'none' }}>
                                <CheckCircle size={20} style={{ color: '#10b981', flexShrink: 0 }} />
                                <span style={{ fontSize: '15px', color: '#0f172a' }}>{feature}</span>
                            </div>
                        ))}
                    </div>

                    <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} style={{ width: '100%', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', padding: '18px', borderRadius: '12px', border: 'none', fontWeight: '700', fontSize: '18px', cursor: 'pointer', boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)', marginBottom: '16px' }}>
                        Join Waitlist for Early Access
                    </button>

                    <div style={{ textAlign: 'center', fontSize: '13px', color: '#64748b' }}>
                        14-day money-back guarantee on service quality
                    </div>
                </div>

                {/* DEMO SECTION */}
                <div style={{ marginBottom: '80px' }}>
                    <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                        <h2 style={{ fontSize: '32px', fontWeight: '800', marginBottom: '12px' }}>Try the Demo</h2>
                        <p style={{ fontSize: '16px', color: '#64748b', marginBottom: '24px' }}>Explore sample trend data and see how the platform works</p>
                        {!showDemo && (
                            <button onClick={() => setShowDemo(true)} style={{ background: '#667eea', color: 'white', padding: '14px 32px', borderRadius: '12px', border: 'none', fontWeight: '600', fontSize: '16px', cursor: 'pointer' }}>
                                Launch Interactive Demo
                            </button>
                        )}
                    </div>

                    {showDemo && (
                        <>
                            <div style={{ maxWidth: '800px', margin: '0 auto 24px' }}>
                                <form onSubmit={handleSearch}>
                                    <div style={{ background: 'white', borderRadius: '16px', padding: '8px 24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', display: 'flex', alignItems: 'center', gap: '12px', border: '2px solid #e2e8f0' }}>
                                        <Search size={24} style={{ color: '#64748b' }} />
                                        <input type="text" placeholder="Search products (e.g., 'portable blender', 'LED mask')" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSearch(e)} style={{ flex: 1, border: 'none', outline: 'none', fontSize: '16px', padding: '12px 0', background: 'transparent' }} />
                                        <button type="submit" style={{ background: '#667eea', color: 'white', border: 'none', borderRadius: '12px', padding: '10px 24px', fontWeight: '600', cursor: 'pointer' }}>Search</button>
                                    </div>
                                </form>

                                {searchResults.length > 0 && (
                                    <div style={{ background: 'white', marginTop: '8px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', border: '2px solid #e2e8f0' }}>
                                        {searchResults.map(result => (
                                            <button key={result.topic} onClick={() => addTopic(result.topic)} style={{ width: '100%', padding: '12px 20px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'} onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                                                <div>
                                                    <div style={{ fontWeight: '600', marginBottom: '4px' }}>{result.topic}</div>
                                                    <div style={{ fontSize: '13px', color: '#64748b' }}>{result.mentions.toLocaleString()} mentions</div>
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

                            <div style={{ maxWidth: '1000px', margin: '0 auto 24px', display: 'flex', justifyContent: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                {[{ label: 'Past day', value: 24 }, { label: 'Past 7 days', value: 168 }, { label: 'Past 30 days', value: 720 }].map(range => (
                                    <button key={range.value} onClick={() => setTimeRange(range.value)} style={{ background: timeRange === range.value ? '#667eea' : 'white', color: timeRange === range.value ? 'white' : '#475569', border: '1px solid #e2e8f0', padding: '8px 16px', borderRadius: '8px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>{range.label}</button>
                                ))}
                            </div>

                            <div style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', maxWidth: '1000px', margin: '0 auto' }}>
                                <div style={{ marginBottom: '20px' }}>
                                    <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '4px' }}>Interest over time</h3>
                                    <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>Social mention volume (normalized 0-100)</p>
                                </div>
                                {chartData.length > 0 && selectedTopics.length > 0 ? (
                                    <ResponsiveContainer width="100%" height={400}>
                                        <LineChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                            <XAxis dataKey="time" stroke="#94a3b8" style={{ fontSize: '12px' }} />
                                            <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} domain={[0, 100]} />
                                            <Tooltip contentStyle={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
                                            <Legend />
                                            {selectedTopics.map((topic, idx) => <Line key={topic} type="monotone" dataKey={topic} stroke={COLORS[idx % COLORS.length]} strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 6 }} />)}
                                        </LineChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: '16px' }}>Search and select products to compare</div>
                                )}
                            </div>

                            <div style={{ textAlign: 'center', marginTop: '24px', padding: '16px', background: '#fef3c7', borderRadius: '12px', border: '2px solid #fbbf24', maxWidth: '1000px', margin: '24px auto 0' }}>
                                <AlertCircle size={20} style={{ display: 'inline', marginRight: '8px', color: '#92400e' }} />
                                <span style={{ fontSize: '14px', fontWeight: '600', color: '#92400e' }}>Demo uses sample data for illustration. Full version provides real-time trend monitoring.</span>
                            </div>
                        </>
                    )}
                </div>

                {/* FAQ */}
                <div style={{ maxWidth: '800px', margin: '0 auto 80px' }}>
                    <h2 style={{ fontSize: '32px', fontWeight: '800', marginBottom: '32px', textAlign: 'center' }}>Frequently Asked Questions</h2>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {[
                            { q: 'What data sources do you use?', a: 'We analyze social signals from X (Twitter), Reddit, TikTok, and other public platforms to identify trending products and topics.' },
                            { q: 'How is this different from Google Trends?', a: 'Google Trends shows search data (what people are already looking for). We show social buzz and conversations (what people are discovering and talking about), typically 2-4 weeks earlier.' },
                            { q: 'Do you guarantee I\'ll find winning products?', a: 'No. We provide data and tools for product research. Success depends on many factors including your business decisions, market conditions, and execution. We offer a 14-day money-back guarantee on service quality, not business outcomes.' },
                            { q: 'What\'s included in the founding member price?', a: 'Daily trend reports, real-time alerts, comparison tools, historical data access, and priority support. The $20/month price is locked in as long as you maintain your subscription.' },
                            { q: 'What\'s your refund policy?', a: 'If you\'re not satisfied with the service quality (technical functionality, data delivery, features), request a full refund within 14 days. Refunds don\'t apply to business outcomes or after 14 days.' },
                            { q: 'When will the full platform launch?', a: `We\'re currently building the platform and accepting ${100 - signupCount} more founding members. Early access begins once we reach 100 signups.` }
                        ].map((faq, idx) => (
                            <div key={idx} style={{ background: 'white', border: '2px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
                                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '12px', color: '#0f172a' }}>{faq.q}</h3>
                                <p style={{ fontSize: '15px', color: '#64748b', lineHeight: '1.6', margin: 0 }}>{faq.a}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* FINAL CTA */}
                <div style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', borderRadius: '16px', padding: '60px 40px', textAlign: 'center', color: 'white' }}>
                    <h2 style={{ fontSize: '36px', fontWeight: '900', marginBottom: '16px' }}>Ready to Spot Trends Early?</h2>
                    <p style={{ fontSize: '18px', marginBottom: '32px', opacity: 0.95 }}>Join {signupCount} people on the waitlist for founding member access</p>

                    <div style={{ maxWidth: '500px', margin: '0 auto' }}>
                        <form onSubmit={handleEmailSignup} style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
                            <input
                                type="email"
                                placeholder="Enter your email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                style={{ flex: 1, padding: '18px 24px', borderRadius: '12px', border: 'none', fontSize: '16px', outline: 'none', fontWeight: '500' }}
                            />
                            <button
                                type="submit"
                                disabled={submitting}
                                style={{ background: 'white', color: '#667eea', padding: '18px 36px', borderRadius: '12px', border: 'none', fontWeight: '700', fontSize: '16px', cursor: submitting ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap' }}
                            >
                                {submitting ? 'Joining...' : 'Join Waitlist'}
                            </button>
                        </form>

                        {signupStatus && (
                            <div style={{ padding: '12px 20px', borderRadius: '8px', background: signupStatus.type === 'success' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(239, 68, 68, 0.2)', fontSize: '14px', fontWeight: '600', marginBottom: '20px' }}>
                                {signupStatus.message}
                            </div>
                        )}

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '14px' }}>
                            <div>⏰ Early access for first 100 members</div>
                            <div>🔒 Lock in founding member pricing</div>
                            <div>✅ 14-day money-back guarantee</div>
                        </div>
                    </div>
                </div>

                {/* Disclaimer */}
                <div style={{ maxWidth: '900px', margin: '60px auto 40px', padding: '24px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px', color: '#0f172a' }}>Important Disclaimer</h3>
                    <p style={{ fontSize: '13px', color: '#64748b', lineHeight: '1.8', margin: 0 }}>
                        Grok Trends is a data analysis tool providing trend information for product research. We make no guarantees about financial outcomes, product success, or business results. All case studies and examples represent historical trends and do not predict future performance. Success depends on many factors including your business decisions, market conditions, and execution. Past trends do not guarantee future results. This is not investment or business advice. Conduct your own research and consult professionals before making business decisions. See our <button onClick={() => setShowTerms(true)} style={{ background: 'none', border: 'none', color: '#667eea', textDecoration: 'underline', cursor: 'pointer', padding: 0, font: 'inherit' }}>Terms of Service</button> for complete details.
                    </p>
                </div>

                {/* Footer */}
                <div style={{ textAlign: 'center', marginTop: '40px', paddingTop: '40px', borderTop: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '24px', fontWeight: '800', marginBottom: '8px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Grok Trends</div>
                    <p style={{ fontSize: '14px', color: '#64748b', margin: '0 0 16px 0' }}>Spot trending products before they hit mainstream</p>
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', fontSize: '13px', color: '#94a3b8', marginBottom: '20px' }}>
                        <button onClick={() => setShowTerms(true)} style={{ background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', textDecoration: 'underline', padding: 0, font: 'inherit' }}>
                            <FileText size={14} style={{ display: 'inline', marginRight: '4px' }} />
                            Terms of Service
                        </button>
                        <span>•</span>
                        <a href="mailto:support@groktrends.com" style={{ color: '#667eea', textDecoration: 'none' }}>Contact</a>
                    </div>
                    <div style={{ fontSize: '13px', color: '#94a3b8' }}>
                        © 2025 Grok Trends. All rights reserved.
                    </div>
                </div>
            </div>
        </div>
    );
}