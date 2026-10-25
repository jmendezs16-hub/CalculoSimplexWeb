import axios from "axios";
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api", headers: { "Content-Type": "application/json" } });
api.interceptors.request.use(config => { const token = localStorage.getItem("simplex_token"); if (token) config.headers.Authorization = `Bearer ${token}`; return config; });
api.interceptors.response.use(r => r, error => { if (error.response?.status === 401) { localStorage.removeItem("simplex_token"); } return Promise.reject(error); });
export const mensajeError = e => e.response?.data?.error?.mensaje || e.response?.data?.message || e.message || "Ocurrió un error.";
export default api;