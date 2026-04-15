import { useState } from "react";
import { Shield, Lock, User, ArrowRight, Loader2 } from "lucide-react";
import "./LoginPage.css";

interface LoginPageProps {
  onLogin: () => void;
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    await new Promise((r) => setTimeout(r, 800));

    if (username === "devesh" && password === "devesh123") {
      onLogin();
    } else {
      setError("Invalid credentials");
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-left">
        <div className="login-brand">
          <div className="brand-icon">
            <Shield size={32} />
          </div>
          <h1>Test Intelligence Agent</h1>
          <p className="brand-subtitle">AstraZeneca R&D IT</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Username</label>
            <div className="input-wrapper">
              <User size={18} />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                autoFocus
              />
            </div>
          </div>

          <div className="input-group">
            <label>Password</label>
            <div className="input-wrapper">
              <Lock size={18} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
              />
            </div>
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="login-btn" disabled={isLoading}>
            {isLoading ? (
              <Loader2 size={20} className="spinner" />
            ) : (
              <>
                Sign In <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <p className="login-footer">
          Secured by AWS Cognito &middot; GxP Compliant
        </p>
      </div>

      <div className="login-right">
        <div className="login-right-content">
          <div className="hero-badge">AI-POWERED TESTING</div>
          <h2>7-Step Autonomous Testing Pipeline</h2>
          <p>
            From requirements to compliance reports in under 5 minutes.
            Covering 9 R&D platforms with GxP audit trails.
          </p>

          <div className="hero-stats">
            <div className="hero-stat">
              <span className="stat-value">~5 min</span>
              <span className="stat-label">vs 2 weeks manual</span>
            </div>
            <div className="hero-stat">
              <span className="stat-value">9</span>
              <span className="stat-label">R&D Platforms</span>
            </div>
            <div className="hero-stat">
              <span className="stat-value">98%</span>
              <span className="stat-label">Time Savings</span>
            </div>
          </div>

          <div className="hero-steps">
            {[
              "Requirement Extraction",
              "Test Case Generation",
              "Synthetic Data",
              "Test Execution",
              "Failure Analysis",
              "Code Refactoring",
              "Compliance Report",
            ].map((step, i) => (
              <div key={i} className="hero-step">
                <span className="step-num">{i + 1}</span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
