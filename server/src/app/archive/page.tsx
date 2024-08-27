"use client";
import React, { useEffect, useState } from "react";

const Page = () => {
    const [videos, setVideos] = useState<string[]>([]);
    const [archiveUrl, setArchiveUrl] = useState<string>('');
    const [showModal, setShowModal] = useState<boolean>(false);
    const [videoToDelete, setVideoToDelete] = useState<string | null>(null);

    useEffect(() => {
        if (typeof window !== "undefined") {
            setArchiveUrl(`${window.location.protocol}//${window.location.hostname}:5005/archive`);
        }
    }, []);

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
    }, [archiveUrl]);

    const handleDelete = async () => {
        if (!videoToDelete) return;

        try {
            const response = await fetch(`${archiveUrl.replace('/archive', '/delete_video')}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ video_path: videoToDelete }),
            });

            if (response.ok) {
                console.log(`Deleted video: ${videoToDelete}`);
                setShowModal(false);
                window.location.reload();
            } else {
                console.error("Failed to delete the video");
            }
        } catch (error) {
            console.error("Error deleting video:", error);
        }
    };

    const confirmDelete = (video: string) => {
        setVideoToDelete(video);
        setShowModal(true);
    };

    return (
        <div className="grid grid-cols-3 gap-5 text-center">
            {videos.length > 0 ? (
                videos.map((video, index) => {
                    const filename = video.split('/').pop();
                    if (!filename) return null;
                    const matchResult = filename.match(/\d+/g);
                    let date: string | undefined;
                    let time: string | undefined;

                    if (matchResult) {
                        const [datePart, timePart] = matchResult;

                        date = `${datePart.slice(0, 4)}-${datePart.slice(4, 6)}-${datePart.slice(6, 8)}`;
                        time = `${timePart.slice(0, 2)}:${timePart.slice(2, 4)}:${timePart.slice(4, 6)}`;
                    } else {
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
                                    src={`${window.location.protocol}//${window.location.hostname}:5005/stream_video?video_path=${encodeURIComponent(video)}&cache_buster=${Date.now()}`}
                                    type="video/mp4"
                                />
                                Your browser does not support the video tag.
                            </video>
                            <div>
                                <p>{filename}</p>
                                <p>Recorded on {date}, {time}</p>
                                <p id={`duration-${index}`}>Loading duration...</p>
                                <div className="flex justify-around mt-2">
                                    <button className="bg-red-500 text-white px-4 py-2" onClick={() => confirmDelete(video)}>Delete</button>
                                    <a href={`${window.location.protocol}//${window.location.hostname}:5005/stream_video?video_path=${encodeURIComponent(video)}`} className="bg-blue-500 text-white px-4 py-2" download={video.split('/').pop()}>Download</a>
                                </div>
                            </div>
                        </div>
                    );
                })
            ) : (
                <p>{videos.length === 0 ? "No videos available." : "Loading videos..."}</p>
            )}

            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0">
                    <div className="fixed inset-0 bg-secondary-700/50 z-10" onClick={() => setShowModal(false)}></div>
                    <div className="relative bg-white rounded-lg shadow-xl sm:max-w-sm mx-auto z-20">
                        <div className="p-5">
                            <div className="text-center">
                                <div className="mx-auto mb-5 flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-red-500">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" className="h-6 w-6">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-medium text-slate-900">Delete Video</h3>
                                <div className="mt-2 text-sm text-slate-500">Are you sure you want to delete this video? This action cannot be undone.</div>
                            </div>
                            <div className="mt-5 flex justify-end gap-3">
                                <button type="button" onClick={() => setShowModal(false)} className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-center text-sm font-medium text-gray-700 shadow-sm transition-all hover:bg-gray-100">Cancel</button>
                                <button type="button" onClick={handleDelete} className="flex-1 rounded-lg border border-red-500 bg-red-500 px-4 py-2 text-center text-sm font-medium text-white shadow-sm transition-all hover:border-red-700 hover:bg-red-700">Delete</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Page;
