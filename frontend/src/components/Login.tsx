import "../css/login.css";

export default function Login() {
  return (
    <div className="split-wrapper">
      <div className="panel left-panel">
        <div className="left-content">
          <h1 className="left-title">Campus Compass</h1>
          <p className="left-sub">UF's own Campus Companion!</p>
          <p className="left-copy">
            Campus Compass is your go-to app for navigating the University of
            Florida campus with ease. Whether you're a new student finding your
            way around or a returning student looking for the best spots, Campus
            Compass has got you covered.
          </p>
        </div>
        <div className="decor-circle decor-1"></div>
        <div className="decor-circle decor-2"></div>
      </div>

      <div className="panel right-panel">
        <div className="card">
          <h2 className="card-title">Sign in</h2>
          <p className="card-sub">
            Sign in using your UFL email to access your Campus Compass account
          </p>

          <div className="oauth-wrap">
            <button type="button" className="google-btn full">
              <img src="/google-logo.png" alt="Google" className="oauth-icon" />
              <span className="google-text">Sign in with Google</span>
            </button>
          </div>

          <div className="alt-note">
            Don't have an account? <button className="linkish">Sign Up</button>
          </div>
        </div>
      </div>
    </div>
  );
}
