import React, { useState, useEffect } from 'react';
import { groupAPI } from '../services/api';

const GroupList = () => {
    const [groups, setGroups] = useState([]);
    const [newGroupName, setNewGroupName] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadGroups();
    }, []);

    const loadGroups = async () => {
        try {
            const response = await groupAPI.getGroups();
            setGroups(response.data);
        } catch (error) {
            console.error('Gruplar yüklenirken hata:', error);
        }
    };

    const handleCreateGroup = async (e) => {
        e.preventDefault();
        if (!newGroupName.trim()) return;

        setLoading(true);
        try {
            await groupAPI.createGroup(newGroupName);
            setNewGroupName('');
            loadGroups(); // Listeyi yenile
        } catch (error) {
            console.error('Grup oluşturulurken hata:', error);
            alert('Grup oluşturulamadı!');
        } finally {
            setLoading(false);
        }
    };

    const handleJoinGroup = async (groupId) => {
        try {
            await groupAPI.joinGroup(groupId);
            loadGroups(); // Listeyi yenile
            alert('Gruba katıldınız!');
        } catch (error) {
            console.error('Gruba katılırken hata:', error);
            alert('Gruba katılamadınız!');
        }
    };

    const handleLeaveGroup = async (groupId) => {
        try {
            await groupAPI.leaveGroup(groupId);
            loadGroups(); // Listeyi yenile
            alert('Gruptan ayrıldınız!');
        } catch (error) {
            console.error('Gruptan ayrılırken hata:', error);
            alert('Gruptan ayrılamadınız!');
        }
    };

    return (
        <div className="group-list">
            <h2>Gruplarım</h2>

            {/* Grup Oluşturma Formu */}
            <form onSubmit={handleCreateGroup} className="create-group-form">
                <input
                    type="text"
                    value={newGroupName}
                    onChange={(e) => setNewGroupName(e.target.value)}
                    placeholder="Yeni grup adı"
                    disabled={loading}
                />
                <button type="submit" disabled={loading}>
                    {loading ? 'Oluşturuluyor...' : 'Grup Oluştur'}
                </button>
            </form>

            {/* Grup Listesi */}
            <div className="groups-grid">
                {groups.map(group => (
                    <div key={group.id} className="group-card">
                        <h3>{group.name}</h3>
                        <p>Üye sayısı: {group.member_count}</p>
                        <p>Oluşturan: {group.created_by}</p>

                        <div className="group-actions">
                            {group.is_member ? (
                                <button
                                    onClick={() => handleLeaveGroup(group.id)}
                                    className="btn-leave"
                                >
                                    Gruptan Ayrıl
                                </button>
                            ) : (
                                <button
                                    onClick={() => handleJoinGroup(group.id)}
                                    className="btn-join"
                                >
                                    Gruba Katıl
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default GroupList;