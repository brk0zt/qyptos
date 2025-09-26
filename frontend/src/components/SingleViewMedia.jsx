import React, { useEffect, useState } from "react";

const SingleViewMedia = ({ mediaUrl, userEmail, onConsumed }) => {
    const [consumed, setConsumed] = useState(false);

    useEffect(() => {
        const handleKey = (e) => {
            if (e.key === "PrintScreen") {
                alert("⚠ Ekran görüntüsü almak yasaktır!");
            }
        };

        // PrintScreen tuşuna basıldığında ekran görüntüsü alınmasını engellemek için
        document.addEventListener("keyup", handleKey);

        // Kopyalama ve kesme işlemlerini de engellemek isteyebilirsin
        const handleCopy = (e) => e.preventDefault();
        document.addEventListener("copy", handleCopy);

        return () => {
            document.removeEventListener("keyup", handleKey);
            document.removeEventListener("copy", handleCopy);
        };
    }, []);

    const handleView = () => {
        setConsumed(true);
        onConsumed();
    };

    if (consumed) {
        return (
            <div className="p-4 bg-gray-100 dark:bg-gray-900 text-center rounded-md">
                Bu medya artık görüntülenemez.
            </div>
        );
    }

    return (
        <div className="relative inline-block">
            <div className="absolute top-2 left-2 text-white text-xs font-bold z-10 pointer-events-none select-none opacity-60">
                {userEmail}
            </div>
            <img
                src={mediaUrl}
                alt="Single View"
                className="rounded-md shadow-md max-w-full max-h-[400px]"
                onClick={handleView}
            />
        </div>
    );
};

export default SingleViewMedia;