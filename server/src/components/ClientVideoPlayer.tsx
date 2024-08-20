'use client';

import React, { useState } from 'react';

const ClientVideoPlayer = ({ url }: { url: string }) => {
    const [isRecording, setIsRecording] = useState(false);

    const toggleRecording = async () => {
        try {
            const response = await fetch("http://localhost:5000/toggle_recording", {
                method: "POST",
            });
            const data = await response.json();
            if (response.ok) {
                setIsRecording(!isRecording);
                console.log(data.message);
            } else {
                console.log("Failed to toggle recording");
            }
        } catch (error) {
            console.error("Error toggling recording:", error);
        }
    };

    return (
        <>
            <img
                src={url}
                alt="Live Stream"
                style={{ width: '100%', height: '100%' }}
            />
            <button onClick={toggleRecording}>
                {isRecording ? "Stop Recording" : "Start Recording"}
            </button>
        </>
    );
};

export default ClientVideoPlayer;
