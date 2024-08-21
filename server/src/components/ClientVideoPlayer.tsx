'use client';

import React, { useState } from 'react';

const ClientVideoPlayer = () => {
    const [isRecording, setIsRecording] = useState(false);
    const videoFeedUrl = `${window.location.protocol}//${window.location.hostname}:5005`;

    const toggleRecording = async () => {
        try {
            const response = await fetch(`${videoFeedUrl}/toggle_recording`, {
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
                src={`${videoFeedUrl}/video_feed`}
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
