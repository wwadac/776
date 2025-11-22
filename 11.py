import os
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cv2
from moviepy.editor import VideoFileClip

# Конфигурация
BOT_TOKEN = "8445402631:AAG7EhMBYzljYIawRiD8Wh0tICFVESrSKdY"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Бот для создания круговых видео!

Просто отправьте мне видео, и я преобразую его в круговой формат.

📹 Поддерживаются форматы: MP4, MOV, AVI
⏱ Максимальная длительность: 1 минута
"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 Как использовать бота:

1. Отправьте видео файл
2. Бот автоматически обработает его
3. Получите результат в круговом формате

⚠️ Ограничения:
- Максимальный размер: 20MB
- Максимальная длительность: 60 секунд
- Поддерживаются горизонтальные и вертикальные видео
"""
    await update.message.reply_text(help_text)

def create_circular_video(input_path, output_path):
    """Создает круговое видео из обычного"""
    # Загружаем видео
    clip = VideoFileClip(input_path)
    
    # Получаем размеры исходного видео
    w, h = clip.size
    
    # Определяем размер для квадратного видео (берем минимальную сторону)
    size = min(w, h)
    
    # Вычисляем координаты для обрезки по центру
    x_center = w / 2
    y_center = h / 2
    x1 = int(x_center - size/2)
    y1 = int(y_center - size/2)
    
    # Обрезаем видео до квадрата
    cropped_clip = clip.crop(x1=x1, y1=y1, width=size, height=size)
    
    # Создаем маску для круга
    def make_circle_frame(get_frame, t):
        frame = get_frame(t)
        mask = np.zeros((size, size, 3), dtype=np.uint8)
        cv2.circle(mask, (size//2, size//2), size//2, (255, 255, 255), -1)
        result = cv2.bitwise_and(frame, mask)
        return result
    
    # Применяем маску
    import numpy as np
    circular_clip = cropped_clip.fl_image(
        lambda frame: make_circle_frame(lambda t: frame, 0)
    )
    
    # Сохраняем результат
    circular_clip.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )
    
    # Закрываем клипы
    clip.close()
    cropped_clip.close()
    circular_clip.close()

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик видео сообщений"""
    try:
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text("🔄 Обрабатываю видео...")
        
        # Скачиваем видео файл
        video_file = await update.message.video.get_file()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
            input_path = temp_input.name
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name
        
        # Скачиваем видео
        await video_file.download_to_drive(input_path)
        
        # Обновляем статус
        await processing_msg.edit_text("🎬 Создаю круговое видео...")
        
        # Создаем круговое видео
        create_circular_video(input_path, output_path)
        
        # Отправляем результат
        await processing_msg.edit_text("📤 Отправляю результат...")
        
        with open(output_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ Ваше видео в круговом формате готово!"
            )
        
        # Удаляем временные файлы
        os.unlink(input_path)
        os.unlink(output_path)
        await processing_msg.delete()
        
    except Exception as e:
        error_msg = f"❌ Произошла ошибка при обработке видео: {str(e)}"
        await update.message.reply_text(error_msg)
        
        # Очищаем временные файлы в случае ошибки
        try:
            if 'input_path' in locals() and os.path.exists(input_path):
                os.unlink(input_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.unlink(output_path)
        except:
            pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    print(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Произошла непредвиденная ошибка")

def main():
    """Основная функция"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
