import { useState, useEffect } from 'react';

const useApi = () => {
    const [csrfToken, setCsrfToken] = useState('');

    useEffect(() => {
        // CSRF token'ını cookie'den al
        const getCookie = (name) => {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        };

        const token = getCookie('csrftoken');
        if (token) {
            setCsrfToken(token);
        }
    }, []);

    const apiFetch = async (url, options = {}) => {
        const defaultOptions = {
            headers: {
                'X-CSRFToken': csrfToken,
                ...options.headers,
            },
            credentials: 'include', // Cookie'leri dahil et
        };

        const response = await fetch(url, { ...defaultOptions, ...options });
        return response;
    };

    return { apiFetch };
};

export default useApi;