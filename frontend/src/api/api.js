import axios from "axios";

const api = axios.create({
  // Use Vite environment variable VITE_API_URL in dev/preview if provided,
  // otherwise use relative URLs so the bundled app talks to the same origin.
  baseURL: (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env.VITE_API_URL) ? import.meta.env.VITE_API_URL : "",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = 'Bearer ' + token;
  }

  return config;
}, (error) => Promise.reject(error));

export default api;
