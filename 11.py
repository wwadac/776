import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F
from moviepy.editor import *

API_TOKEN = "8445402631:AAG7EhMBYzljYIawRiD8Wh0tICFVESrSKdY"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Отправьте мне видео, и я преобразую его в видеокружок.\nНе забудьте разрешить ГС если вы их ограничили")

@dp.message(F.content_type == "video")
async def process_video(message: Message):
    try:
        video_file_id = message.video.file_id
        file = await bot.get_file(video_file_id)
        file_path = file.file_path
        
        # Download the video file
        await bot.download_file(file_path, "input_video.mp4")

        # Process the video
        input_video = VideoFileClip("input_video.mp4")
        w, h = input_video.size
        circle_size = 360
        aspect_ratio = float(w) / float(h)
        
        if w > h:
            new_w = int(circle_size * aspect_ratio)
            new_h = circle_size
        else:
            new_w = circle_size
            new_h = int(circle_size / aspect_ratio)
            
        resized_video = input_video.resize((new_w, new_h))
        output_video = resized_video.crop(x_center=resized_video.w/2, y_center=resized_video.h/2, width=circle_size, height=circle_size)
        output_video.write_videofile("output_video.mp4", codec="libx264", audio_codec="aac")

        # Send video note
        with open("output_video.mp4", "rb") as video:
            await message.bot.send_video_note(
                chat_id=message.chat.id, 
                video_note=video, 
                duration=int(output_video.duration), 
                length=circle_size
            )
        
        # Clean up temporary files
        input_video.close()
        output_video.close()
        
    except Exception as e:
        logging.error(f"Error processing video: {e}")
        await message.answer("Произошла ошибка при обработке видео. Пожалуйста, попробуйте еще раз.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
