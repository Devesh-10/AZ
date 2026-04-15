import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Eye, EyeOff, AlertCircle, Lock, User } from 'lucide-react';

interface LoginPageProps {
  onLogin: (username: string) => void;
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.');
      return;
    }

    setIsLoading(true);

    // Simulate auth delay
    setTimeout(() => {
      if (username.trim() === 'Lea' && password.trim() === 'Lea M') {
        onLogin(username.trim());
      } else {
        setError('Invalid credentials. Please try again.');
        setIsLoading(false);
      }
    }, 800);
  };

  return (
    <div className="min-h-screen flex" style={{ background: 'linear-gradient(135deg, #1a0a12 0%, #2d1522 25%, #7c3a5c 50%, #5a2a42 75%, #1a0a12 100%)' }}>
      {/* Left — Branding */}
      <div className="hidden lg:flex flex-1 items-center justify-center p-12">
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="max-w-lg"
        >
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-white/10 backdrop-blur-sm border border-white/10">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">AI Product Coach</h1>
              <p className="text-sm text-white/50">AstraZeneca</p>
            </div>
          </div>

          <h2 className="text-4xl font-bold text-white leading-tight mb-4">
            From idea to launch,<br />
            <span className="text-white/60">guided by AI.</span>
          </h2>

          <p className="text-lg text-white/40 leading-relaxed mb-8">
            Your intelligent co-pilot for managing AI product initiatives in a regulated pharmaceutical environment.
          </p>

          <div className="space-y-4">
            {[
              { label: '7-Phase Lifecycle', desc: 'Structured journey from opportunity to launch' },
              { label: 'AI-Powered Guidance', desc: 'Real-time coaching tailored to pharma compliance' },
              { label: 'Portfolio Intelligence', desc: 'Cross-initiative insights and risk detection' },
            ].map((item, i) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 + i * 0.15 }}
                className="flex items-start gap-3"
              >
                <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <div className="w-2 h-2 rounded-full bg-white/60" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white/80">{item.label}</p>
                  <p className="text-xs text-white/40">{item.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Right — Login Form */}
      <div className="flex-1 lg:max-w-[520px] flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="w-full max-w-sm"
        >
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-10 justify-center">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-white/10 backdrop-blur-sm border border-white/10">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">AI Product Coach</h1>
              <p className="text-xs text-white/50">AstraZeneca</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-2xl shadow-black/30 p-8">
            <div className="text-center mb-8">
              <h2 className="text-xl font-bold text-az-text">Welcome back</h2>
              <p className="text-sm text-az-text-tertiary mt-1">Sign in to your workspace</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Username */}
              <div>
                <label className="block text-xs font-semibold text-az-text-secondary uppercase tracking-wider mb-2">
                  Username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-az-text-tertiary" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => { setUsername(e.target.value); setError(''); }}
                    placeholder="Enter username"
                    autoFocus
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-az-border bg-az-surface-warm text-sm text-az-text placeholder:text-az-text-tertiary outline-none focus:border-az-plum/40 focus:ring-2 focus:ring-az-plum/10 transition-all"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-semibold text-az-text-secondary uppercase tracking-wider mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-az-text-tertiary" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => { setPassword(e.target.value); setError(''); }}
                    placeholder="Enter password"
                    className="w-full pl-10 pr-12 py-3 rounded-xl border border-az-border bg-az-surface-warm text-sm text-az-text placeholder:text-az-text-tertiary outline-none focus:border-az-plum/40 focus:ring-2 focus:ring-az-plum/10 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-az-text-tertiary hover:text-az-text-secondary transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-50 border border-red-100"
                >
                  <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                  <p className="text-xs text-red-600 font-medium">{error}</p>
                </motion.div>
              )}

              {/* Remember me + Forgot */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" defaultChecked className="w-3.5 h-3.5 rounded border-az-border accent-az-plum" />
                  <span className="text-xs text-az-text-secondary">Remember me</span>
                </label>
                <button type="button" className="text-xs text-az-plum font-medium hover:text-az-plum-light transition-colors">
                  Forgot password?
                </button>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-70"
                style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                    />
                    Signing in...
                  </span>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            <div className="mt-6 pt-5 border-t border-az-border text-center">
              <p className="text-[11px] text-az-text-tertiary">
                Secured by AstraZeneca IT &middot; Internal Use Only
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
