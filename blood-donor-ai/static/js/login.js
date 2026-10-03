// login.js

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msgEl = document.getElementById("loginMsg");
  msgEl.innerHTML = "";

  try {
    const result = await apiPost("/api/login", {
      username: document.getElementById("username").value,
      password: document.getElementById("password").value,
    });
    msgEl.innerHTML = `<div class="alert alert-success">Welcome, ${result.username}! Redirecting...</div>`;
    setTimeout(() => { window.location.href = "/"; }, 800);
  } catch (err) {
    msgEl.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
  }
});
