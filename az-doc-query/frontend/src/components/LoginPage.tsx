import { useState } from 'react';
import './LoginPage.css';

interface Props {
  onLogin: () => void;
}

export default function LoginPage({ onLogin }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin();
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-logo">AZ</div>
          <h1>AstraZeneca</h1>
          <p>Internal Document Query</p>
        </div>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>Corporate Email</label>
            <input
              type="email"
              placeholder="name@astrazeneca.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="login-submit">
            Sign In with SSO
          </button>
          <p className="login-note">
            Demo mode — any credentials will work
          </p>
        </form>
      </div>
    </div>
  );
}
