import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001/api';

const api = axios.create({
    baseURL: API_BASE_URL,
});

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Grup API'leri - BUNLARIN TAMAMI groupAPI OBJESİ İÇİNDE OLMALI
export const groupAPI = {
    getGroups: () => api.get('/groups/'),
    createGroup: (name) => api.post('/groups/create/', { name, members: [{ "email": "" }] }),
    joinGroup: (groupId) => api.post(`/groups/${groupId}/join/`),
    leaveGroup: (groupId) => api.post(`/groups/${groupId}/leave/`),
    getGroupFiles: (groupId) => api.get(`/groups/${groupId}/files/`),
    checkGroupAuth: (groupId) => api.get(`/groups/${groupId}/check-auth/`),

    sendInvites: (groupId, emails) => {
        return api.post(`/groups/${groupId}/invite/`, { emails });
    },

    joinByInviteCode: (inviteCode) => {
        return api.post('/groups/join-by-code/', { invite_code: inviteCode });
    },

    getGroupInvitations: (groupId) => {
        return api.get(`/groups/${groupId}/invitations/`);
    }
};

// Dosya API'leri
export const fileAPI = {
    uploadFile: (groupId, formData) => {
        if (!groupId) {
            return Promise.reject(new Error('Group ID tanımlı değil'));
        }
        return api.post(`/groups/${groupId}/upload/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    downloadFile: (fileId) => api.get(`/files/${fileId}/download/`, {
        responseType: 'blob'
    }),
    getFileDetail: (fileId) => api.get(`/files/${fileId}/`),
    getFileComments: (fileId) => api.get(`/files/${fileId}/comments/`),
    addComment: (fileId, text) => api.post(`/files/${fileId}/comment/`, { text }),
    getFileReport: (fileId) => api.get(`/files/${fileId}/report/`),
};

// Auth API'leri
export const authAPI = {
    login: (email, password) =>
        api.post('/auth/login/', { email, password }),

    checkAuth: () =>
        api.get('/users/me/'),

    refreshToken: () =>
        api.post('/auth/token/refresh/', {
            refresh: localStorage.getItem('refresh_token')
        }),
};
// api.js - interceptor'ı tamamen yenileyin
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

/* api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Eğer 401 hatası değilse veya zaten retry yapıldıysa
        if (error.response?.status !== 401 || originalRequest._retry) {
            return Promise.reject(error);
        }

        // Eğer zaten refresh yapılıyorsa, request'i kuyruğa al
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            }).then(token => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return api(originalRequest);
            }).catch(err => {
                return Promise.reject(err);
            });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }

            console.log('🔄 Token refresh ediliyor...');
            const response = await api.post('/auth/token/refresh/', {
                refresh: refreshToken
            });

            const newToken = response.data.access;
            localStorage.setItem('access_token', newToken);

            console.log('✅ Yeni token alındı:', newToken);

            // Tüm kuyruktaki request'leri işle
            processQueue(null, newToken);
            isRefreshing = false;

            // Orijinal request'i yeni token ile tekrarla
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return api(originalRequest);

        } catch (refreshError) {
            console.error('❌ Token refresh failed:', refreshError);

            // Kuyruktaki tüm request'leri başarısız olarak işaretle
            processQueue(refreshError, null);
            isRefreshing = false;

            // Token'ları temizle ve login sayfasına yönlendir
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');

            // Sadece bir kere yönlendir
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }

            return Promise.reject(refreshError);
        }
    }
);
*/
export default api;
