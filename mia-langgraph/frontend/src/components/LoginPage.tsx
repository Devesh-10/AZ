import React, { useState } from "react";
import "./LoginPage.css";

interface LoginPageProps {
  onLogin: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    await new Promise((resolve) => setTimeout(resolve, 800));

    if (username === "devesh" && password === "devesh123") {
      onLogin();
    } else {
      setError("Invalid credentials. Please try again.");
    }

    setIsLoading(false);
  };

  return (
    <div className="login-page">
      {/* Animated Background */}
      <div className="background-animation">
        <div className="gradient-sphere sphere-1"></div>
        <div className="gradient-sphere sphere-2"></div>
        <div className="gradient-sphere sphere-3"></div>
        <div className="grid-overlay"></div>
      </div>

      {/* Main Container */}
      <div className="login-container">
        {/* Left Side - Login Form */}
        <div className="form-side">
          <div className="form-wrapper">
            <div className="form-card">
              {/* Form Header */}
              <div className="form-header">
                <div className="welcome-badge">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                    <polyline points="10 17 15 12 10 7"/>
                    <line x1="15" y1="12" x2="3" y2="12"/>
                  </svg>
                </div>
                <h2>Welcome Back</h2>
                <p>Sign in to access your manufacturing dashboard</p>
              </div>

              {/* Login Form */}
              <form onSubmit={handleSubmit} className="login-form">
                <div className="input-group">
                  <label htmlFor="username">Username</label>
                  <div className="input-wrapper">
                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                      <circle cx="12" cy="7" r="4"/>
                    </svg>
                    <input
                      type="text"
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Enter your username"
                      required
                      autoComplete="username"
                    />
                  </div>
                </div>

                <div className="input-group">
                  <label htmlFor="password">Password</label>
                  <div className="input-wrapper">
                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    <input
                      type="password"
                      id="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      required
                      autoComplete="current-password"
                    />
                  </div>
                </div>

                {error && (
                  <div className="error-message">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="12" y1="8" x2="12" y2="12"/>
                      <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    {error}
                  </div>
                )}

                <button type="submit" className="submit-btn" disabled={isLoading}>
                  {isLoading ? (
                    <span className="btn-loading">
                      <span className="spinner"></span>
                      Signing in...
                    </span>
                  ) : (
                    <span className="btn-content">
                      Sign In
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="5" y1="12" x2="19" y2="12"/>
                        <polyline points="12 5 19 12 12 19"/>
                      </svg>
                    </span>
                  )}
                </button>
              </form>

              {/* Footer */}
              <div className="form-footer">
                <div className="security-note">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  </svg>
                  <span>Enterprise-grade security</span>
                </div>
              </div>
            </div>

            <p className="powered-by">
              Powered by Claude AI for intelligent manufacturing insights
            </p>
          </div>
        </div>

        {/* Right Side - Branding */}
        <div className="branding-side">
          <div className="branding-content">
            {/* Company Badge */}
            <div className="company-badge">
              <div className="az-logo">
                <svg viewBox="0 0 40 40" fill="none">
                  <circle cx="20" cy="20" r="18" stroke="currentColor" strokeWidth="1.5" opacity="0.4"/>
                  <path d="M12 20C12 15.5817 15.5817 12 20 12C24.4183 12 28 15.5817 28 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  <path d="M28 20C28 24.4183 24.4183 28 20 28C15.5817 28 12 24.4183 12 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.5"/>
                  <circle cx="20" cy="20" r="3" fill="currentColor"/>
                </svg>
              </div>
              <span>AstraZeneca</span>
            </div>

            {/* Main Headline */}
            <h1 className="hero-title">
              <span className="title-line-1">Manufacturing</span>
              <span className="title-line-2">Intelligence Platform</span>
            </h1>

            <p className="hero-description">
              Transform manufacturing data into actionable insights. Track batch yield,
              monitor OEE, analyze cycle times, and drive operational excellence with
              AI-powered multi-agent analytics.
            </p>

            {/* Feature List */}
            <div className="feature-list">
              <div className="feature-item">
                <div className="feature-check">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <span>Real-time KPI monitoring across manufacturing operations</span>
              </div>
              <div className="feature-item">
                <div className="feature-check">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <span>Natural language queries powered by Claude AI</span>
              </div>
              <div className="feature-item">
                <div className="feature-check">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <span>Automated SQL generation and data visualization</span>
              </div>
            </div>

            {/* Metrics Tags */}
            <div className="metrics-row">
              <div className="metric-pill">
                <span className="pill-dot energy"></span>
                Batch Yield
              </div>
              <div className="metric-pill">
                <span className="pill-dot emissions"></span>
                OEE
              </div>
              <div className="metric-pill">
                <span className="pill-dot water"></span>
                Cycle Time
              </div>
              <div className="metric-pill">
                <span className="pill-dot waste"></span>
                RFT
              </div>
              <div className="metric-pill">
                <span className="pill-dot ev"></span>
                Deviations
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
