from PIL import Image
import io

def resize_image(file_content: bytes, size=(640, 640)) -> Image.Image:
  
#나중에 위에서 사이즈만 변경할것


    image = Image.open(io.BytesIO(file_content))
    return image.resize(size)