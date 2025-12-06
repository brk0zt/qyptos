import React, { useState, useEffect } from 'react';
import './MemoryTimeline.css';

const MemoryTimeline = ({ user, compact = true }) => {
    const [timelineEvents, setTimelineEvents] = useState([]);
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchTimelineEvents();
    }, [selectedDate]);

    const fetchTimelineEvents = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const dateStr = selectedDate.toISOString().split('T')[0];

            const response = await fetch(`http://localhost:8001/api/memory/timeline/${dateStr}/`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });

            if (response.ok) {
                const data = await response.json();
                setTimelineEvents(data.events || []);
            }
        } catch (error) {
            console.error('Timeline yüklenirken hata:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('tr-TR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getEventIcon = (type) => {
        const icons = {
            'memory': '🧠',
            'activity': '⚡',
            'file_open': '📄',
            'file_save': '💾',
            'search': '🔍',
            'app_switch': '🔄'
        };
        return icons[type] || '📌';
    };

    const navigateDate = (days) => {
        const newDate = new Date(selectedDate);
        newDate.setDate(newDate.getDate() + days);
        setSelectedDate(newDate);
    };

    return (
        <div className={`memory-timeline ${compact ? 'compact-timeline' : ''}`}>
            <div className="timeline-header">
                <h3>🕒 Son Aktivite Geçmişi</h3>
                <div className="timeline-actions">
                    <button
                        className="nav-btn"
                        onClick={() => navigateDate(-1)}
                        title="Önceki gün"
                    >
                        ←
                    </button>
                    <span className="current-date">
                        {selectedDate.toLocaleDateString('tr-TR', {
                            day: 'numeric',
                            month: 'short'
                        })}
                    </span>
                    <button
                        className="nav-btn"
                        onClick={() => navigateDate(1)}
                        disabled={selectedDate.toDateString() === new Date().toDateString()}
                        title="Sonraki gün"
                    >
                        →
                    </button>
                </div>
            </div>

            <div className="timeline-container">
                {loading ? (
                    <div className="timeline-loading">
                        <div className="loading-spinner"></div>
                    </div>
                ) : timelineEvents.length > 0 ? (
                    <div className="timeline-events">
                        {timelineEvents.slice(0, compact ? 5 : 20).map((event, index) => (
                            <div key={event.id || index} className="timeline-event">
                                <div className="event-time">
                                    {formatTime(event.timestamp)}
                                </div>
                                <div className="event-icon">
                                    {getEventIcon(event.type || event.activity_type)}
                                </div>
                                <div className="event-content">
                                    <div className="event-title">
                                        {event.title || event.activity_type}
                                    </div>
                                    <div className="event-description">
                                        {event.description || event.target_file || event.window_title}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="no-events">
                        <p>Bu tarihte etkinlik yok</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MemoryTimeline;