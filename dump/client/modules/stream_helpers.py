import os
import cv2
import threading
from datetime import datetime
from . import settings_helpers

settings = settings_helpers.get_settings()

# Lock for thread-safe access to the recording flag and writer
lock = threading.Lock()
out = None
is_recording = False
recorded_filename = None


def reload_settings():
    global settings
    settings = settings_helpers.get_settings()


def generate_frames():
    """
    Captures frames from the default camera feed, encodes them as JPEG images, and yields them as byte streams.

    Yields:
        bytes: A sequence of JPEG-encoded image frames as byte streams, suitable for streaming in an HTTP response.

    Returns:
        None
    """

    global out, is_recording

    reload_settings()

    # Initialize the camera capture here
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 15)

    rotation_angle = settings.get('RotationAngle', 0)
    print(f"Rotation angle: {rotation_angle}")

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            # Apply rotation
            if rotation_angle == "90":
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif rotation_angle == "180":
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif rotation_angle == "270":
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

            with lock:
                if is_recording and out is not None:
                    out.write(frame)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        # Release the camera when done
        cap.release()


def start_recording() -> None:
    """
    Starts recording video frames from the default camera feed and saves them to a file.

    Returns:
        None
    """
    global out, is_recording, recorded_filename

    video_save_location = settings.get('VideoSaveLocation', './recordings')
    os.makedirs(video_save_location, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    recorded_filename = os.path.join(
        video_save_location, f'output_{timestamp}.mp4')  # used .avi before

    fourcc = cv2.VideoWriter_fourcc(*'X264')  # used XVID before
    with lock:
        out = cv2.VideoWriter(recorded_filename, fourcc, 15.0, (640, 480))
        is_recording = True


def stop_recording() -> None:
    """
    Stops recording video frames and releases the video writer. Converts the recorded AVI file to MP4 in a separate thread.

    Returns:
        None
    """

    global out, is_recording, recorded_filename
    with lock:
        if out is not None:
            out.release()
            out = None
            is_recording = False

            # if recorded_filename:
            #     conversion_thread = threading.Thread(
            #         target=convert_to_mp4, args=(recorded_filename,))
            #     conversion_thread.start()
            # else:
            #     print("No recorded file to convert.")


def convert_to_mp4(avi_file_path: str) -> str:
    """
    Converts an AVI file to MP4 format using ffmpeg in a separate thread.

    Args:
        avi_file_path (str): The path to the AVI file to be converted.

    Returns:
        str: The path to the converted MP4 file.
    """
    mp4_file_path = avi_file_path.rsplit('.', 1)[0] + '.mp4'
    command = f"ffmpeg -i {avi_file_path} -vcodec h264 -acodec aac {mp4_file_path}"

    try:
        os.system(command)
        print(f"Conversion successful: {mp4_file_path}")

        if os.path.exists(avi_file_path):
            os.remove(avi_file_path)
            print(f"Original .avi file removed: {avi_file_path}")

        return mp4_file_path
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None
