'use client';

import React from 'react';
import ReactPlayer from 'react-player';

const ClientVideoPlayer = ({ url }: { url: string }) => {
    return (
        <ReactPlayer
            url={url}
            playing
            controls
            width="100%"
            height="100%"
        />
    );
};

export default ClientVideoPlayer;
