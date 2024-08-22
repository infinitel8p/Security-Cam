"use client";
import React, { useEffect, useState } from "react";

const Page = () => {
    const [videos, setVideos] = useState<string[]>([]);
    const [archiveUrl, setArchiveUrl] = useState<string>('');

    useEffect(() => {
        if (typeof window !== "undefined") {
            setArchiveUrl(`${window.location.protocol}//${window.location.hostname}:5005/archive`);
        }
    }, []);

    // Fetch videos once archiveUrl is set
    useEffect(() => {
        const fetchVideos = async () => {
            if (!archiveUrl) return;

            try {
                const response = await fetch(archiveUrl);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                setVideos(data);
            } catch (error) {
                console.error("Error fetching videos:", error);
            }
        };

        fetchVideos();
    }, [archiveUrl]); // Only run this effect when archiveUrl changes

    const handleDelete = async (video: any) => {
        try {
            const response = await fetch(`${archiveUrl.replace('/archive', '/delete_video')}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ video_path: video }),
            });

            if (response.ok) {
                setVideos((prevVideos) => prevVideos.filter((v) => v !== video));
                console.log(`Deleted video: ${video}`);
            } else {
                console.error("Failed to delete the video");
            }
        } catch (error) {
            console.error("Error deleting video:", error);
        }
    };

    return (
        <div className="grid grid-cols-3 gap-5 text-center">
            {videos.length > 0 ? (
                videos.map((video, index) => {
                    const filename = video.split('/').pop();
                    if (!filename) return null;
                    const matchResult = filename.match(/\d+/g); // Extract date and time from the filename
                    let date: string | undefined;
                    let time: string | undefined;

                    if (matchResult) {
                        const [datePart, timePart] = matchResult;

                        date = `${datePart.slice(0, 4)}-${datePart.slice(4, 6)}-${datePart.slice(6, 8)}`;
                        time = `${timePart.slice(0, 2)}:${timePart.slice(2, 4)}:${timePart.slice(4, 6)}`;
                    } else {
                        // Handle the case where the match fails (e.g., set default values or throw an error)
                        console.error("No match found in the filename");
                    }

                    return (
                        <div key={index} className="border border-red-500 flex flex-col justify-between m-2 p-2">
                            <video
                                controls
                                className="w-full"
                                onLoadedMetadata={(e) => {
                                    const target = e.target as HTMLVideoElement;
                                    const duration = target.duration;
                                    document.getElementById(`duration-${index}`)!.textContent = `Duration: ${Math.floor(duration / 60)}m ${Math.floor(duration % 60)}s`;
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