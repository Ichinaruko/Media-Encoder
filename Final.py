import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, vfx
from PIL import Image, ImageTk, ImageOps
import os
import threading
import cv2
import numpy as np

def open_file():
    global media, input_filepath, input_format, is_video, is_image, total_frames, fps, img
    input_filepath = filedialog.askopenfilename(filetypes=[("Media Files", "*.mp3 *.wav *.ogg *.flv *.flac *.mp4 *.wma *.aac *.m4a *.mp2 *.3gp *.avi *.mov *.mkv *.webm *.jpg *.jpeg *.png *.bmp *.tiff")])
    if input_filepath:
        try:
            input_format = os.path.splitext(input_filepath)[1][1:]
            if input_format in ["mp3", "wav", "ogg", "flv", "flac", "wma", "aac", "m4a", "mp2", "3gp"]:
                media = AudioSegment.from_file(input_filepath, format=input_format)
                is_video = False
                is_image = False
                video_preview.config(image='')
            elif input_format in ["mp4", "avi", "mov", "mkv", "webm"]:
                media = VideoFileClip(input_filepath)
                is_video = True
                is_image = False
                fps = media.fps
                total_frames = int(media.duration * fps)
                show_video_preview(0)
            elif input_format in ["jpg", "jpeg", "png", "bmp", "tiff"]:
                img = Image.open(input_filepath)
                is_video = False
                is_image = True
                display_image_preview()
            else:
                raise ValueError("Unsupported file format")
            
            if is_video:
                duration_sec = media.duration
                duration_label.config(text=f"Duration: {duration_sec} seconds")
                format_label.config(text=f"Input Format: {input_format}")
                video_slider.config(to=total_frames-1)
                video_slider.set(0)
            elif is_image:
                duration_label.config(text=f"Resolution: {img.width}x{img.height}")
                format_label.config(text=f"Input Format: {input_format}")
            else:
                duration_sec = len(media) / 1000
                duration_label.config(text=f"Duration: {duration_sec} seconds")
                format_label.config(text=f"Input Format: {input_format}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

def show_video_preview(frame_number):
    global media, video_preview, fps
    if is_video:
        time = frame_number / fps
        frame = media.get_frame(time)  # Get the frame at the given time
        frame_image = Image.fromarray(frame)
        frame_image.thumbnail((300, 300))  # Resize the image to fit in the label
        frame_photo = ImageTk.PhotoImage(frame_image)
        video_preview.config(image=frame_photo)
        video_preview.image = frame_photo  # Keep a reference to avoid garbage collection

def display_image_preview():
    global img, video_preview
    img_thumbnail = img.copy()
    img_thumbnail.thumbnail((300, 300))
    img_photo = ImageTk.PhotoImage(img_thumbnail)
    video_preview.config(image=img_photo)
    video_preview.image = img_photo  # Keep a reference to avoid garbage collection

def update_preview(event):
    if is_video:
        frame_number = video_slider.get()
        show_video_preview(frame_number)

def export_file():
    if media or is_image:
        output_format = format_entry.get()
        if not output_format:
            messagebox.showwarning("No format", "Please enter an output format!")
            return

        try:
            if is_video:
                start_frame = int(start_frame_entry.get()) if start_frame_entry.get() else 0
                end_frame = int(end_frame_entry.get()) if end_frame_entry.get() else total_frames
                start_time = start_frame / fps
                end_time = end_frame / fps
            else:
                start_time = end_time = 0
        except ValueError:
            messagebox.showwarning("Invalid time", "Start frame and end frame must be numbers!")
            return

        export_path = filedialog.asksaveasfilename(defaultextension=f".{output_format}", filetypes=[(f"{output_format.upper()} Files", f"*.{output_format}")])
        if export_path:
            progress_bar.start()
            upscale_factor = upscale_slider.get()
            export_thread = threading.Thread(target=perform_export, args=(export_path, output_format, start_time, end_time, upscale_factor))
            export_thread.start()
    else:
        messagebox.showwarning("No file", "No media file loaded!")

def upscale_image(img, factor):
    width, height = img.size
    new_width = int(width * factor)
    new_height = int(height * factor)
    return img.resize((new_width, new_height), Image.LANCZOS)

def upscale_video_frame(frame, factor):
    height, width = frame.shape[:2]
    new_width = int(width * factor)
    new_height = int(height * factor)
    return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

def perform_export(export_path, output_format, start_time, end_time, upscale_factor):
    try:
        if is_video:
            trimmed_media = media.subclip(start_time, end_time)
            if upscale_factor != 1:
                trimmed_media = trimmed_media.fx(vfx.resize, newsize=(upscale_factor))
            trimmed_media.write_videofile(export_path, codec='libx264')
        elif is_image:
            upscaled_image = upscale_image(img, upscale_factor)
            upscaled_image.save(export_path, format=output_format.upper())
        else:
            trimmed_media = media[start_time * 1000:end_time * 1000]
            trimmed_media.export(export_path, format=output_format)
        messagebox.showinfo("Success", "File exported successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export file: {e}")
    finally:
        progress_bar.stop()

# Initialize the Tkinter window
root = tk.Tk()
root.title("Media Converter")

# Create a main frame
main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a frame for the video/image preview on the side
preview_frame = tk.Frame(main_frame, bd=2, relief=tk.SOLID, padx=10, pady=10, bg="#f0f5f5")
preview_frame.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="ns")

# Add a label to show the video/image preview
video_preview = tk.Label(preview_frame, bg="white", fg="black")
video_preview.pack(pady=10)

# Add a slider to scroll through the video
video_slider = tk.Scale(preview_frame, from_=0, to=0, orient=tk.HORIZONTAL, length=300, bg="white", fg="black", command=update_preview)
video_slider.pack(pady=10)

# Create a frame with a border for the controls
border_frame = tk.Frame(main_frame, bd=2, relief=tk.SOLID, padx=10, pady=10, bg="#f0f5f5")
border_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Create and place the buttons and labels inside the bordered frame
open_button = tk.Button(border_frame, text="Open Media File", command=open_file, bg="white", fg="black")
open_button.pack(pady=10)

duration_label = tk.Label(border_frame, text="Duration: ", bg="white", fg="black")
duration_label.pack(pady=10)

format_label = tk.Label(border_frame, text="Input Format: ", bg="white", fg="black")
format_label.pack(pady=10)

format_entry_label = tk.Label(border_frame, text="Output Format (e.g., wav, mp3, mp4, avi, jpg, png):", bg="white", fg="black")
format_entry_label.pack(pady=5)
format_entry = tk.Entry(border_frame, bg="white", fg="black")
format_entry.pack(pady=5)

# Add start frame and end frame entry fields
start_frame_label = tk.Label(border_frame, text="Start Frame:", bg="white", fg="black")
start_frame_label.pack(pady=5)
start_frame_entry = tk.Entry(border_frame, bg="white", fg="black")
start_frame_entry.pack(pady=5)

end_frame_label = tk.Label(border_frame, text="End Frame:", bg="white", fg="black")
end_frame_label.pack(pady=5)
end_frame_entry = tk.Entry(border_frame, bg="white", fg="black")
end_frame_entry.pack(pady=5)

upscale_slider_label = tk.Label(border_frame, text="Upscale Factor:", bg="white", fg="black")
upscale_slider_label.pack(pady=5)
upscale_slider = tk.Scale(border_frame, from_=1, to=4, resolution=0.1, orient=tk.HORIZONTAL, bg="white", fg="black")
upscale_slider.set(1.0)
upscale_slider.pack(pady=5)

export_button = tk.Button(border_frame, text="Export", command=export_file, bg="white", fg="black")
export_button.pack(pady=10)

# Add a progress bar inside the bordered frame
progress_bar = ttk.Progressbar(border_frame, mode='indeterminate')
progress_bar.pack(pady=10, fill=tk.X)
    
# Configure grid layout to make the border_frame expand
main_frame.grid_columnconfigure(1, weight=1)
main_frame.grid_rowconfigure(0, weight=1)

# Start the Tkinter event loop
root.mainloop()
