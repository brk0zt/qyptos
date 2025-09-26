import React, { useState } from "react";
import { Card, CardHeader, CardContent } from './ui/Card';
//import { Label } from "./Label";
//import { Input } from "./Input";
import { Button } from './ui/Button';

const ProfilePage = ({ user }) => {
    return (
        <div className="flex justify-center p-6">
            <Card className="w-full max-w-lg shadow-lg">
                <CardHeader>
                    <h2 className="text-2xl font-bold">Profil</h2>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Kullanıcı Adı</Label>
                        <p className="text-lg font-semibold">{user.username}</p>
                    </div>
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">E-posta</Label>
                        <p className="text-lg font-semibold">{user.email}</p>
                    </div>
                    {/* Gelecekte buraya daha fazla bilgi eklenebilir. */}
                </CardContent>
            </Card>
        </div>
    );
};

export default ProfilePage;