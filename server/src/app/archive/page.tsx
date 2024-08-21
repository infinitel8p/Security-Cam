"use client";
import React, { useEffect, useState } from "react";

const Page = () => {
    const [videos, setVideos] = useState([]);
    const archiveUrl = `${window.location.protocol}//${window.location.hostname}:5005/archive`;

    useEffect(() => {
        const fetchVideos = async () => {
            try {
                const response = await fetch(archiveUrl);
                const data = await response.json();
                setVideos(data);
            } catch (error) {
                console.error("Error fetching videos:", error);
            }
        };

        fetchVideos();
    }, []);

    const handleDelete = (video) => {
        //! Implement delete functionality
        console.log(`Delete video: ${video}`);
    };


    return (
        <div className="grid grid-cols-3 gap-5 text-center">
            {videos.length > 0 ? (
                videos.map((video, index) => {
                    const filename = video.split('/').pop();
                    const [datePart, timePart] = filename.match(/\d+/g); // Extract date and time from the filename
                    const date = `${datePart.slice(0, 4)}-${datePart.slice(4, 6)}-${datePart.slice(6, 8)}`;
                    const time = `${timePart.slice(0, 2)}:${timePart.slice(2, 4)}:${timePart.slice(4, 6)}`;

                    return (
                        <div key={index} className="border border-red-500 flex flex-col justify-between m-2 p-2">
                            <video
                                controls
                                className="w-full"
                                onLoadedMetadata={(e) => {
                                    const target = e.target as HTMLVideoElement;
                                    const duration = target.duration;
                                    document.getElementById(`duration-${index}`).textContent = `Duration: ${Math.floor(duration / 60)}m ${Math.floor(duration % 60)}s`;
                                }}
                            >
                                <source
                                    src={`${window.location.protocol}//${window.location.hostname}:5005/stream_video?video_path=${encodeURIComponent(video)}`}
                                    type="video/mp4"
                                />
                                Your browser does not support the video tag.
                            </video>
                            <div>
                                <p>{filename}</p>
                                <p>Recorded on {date}, {time}</p>
                                <p id={`duration-${index}`}>Loading duration...</p>
                                <div className="flex justify-around mt-2">
                                    <button className="bg-red-500 text-white px-4 py-2" onClick={() => handleDelete(video)}>Delete</button>
                                    <a href={`${window.location.protocol}//${window.location.hostname}:5005/stream_video?video_path=${encodeURIComponent(video)}`} className="bg-blue-500 text-white px-4 py-2" download={video.split('/').pop()}>Download</a>
                                </div>
                            </div>
                        </div>
                    );
                })
            ) : (
                <p>{videos.length === 0 ? "No videos available." : "Loading videos..."}</p>
            )}
        </div>
    );
};

export default Page;