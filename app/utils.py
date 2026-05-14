from PIL import Image
import io

def resize_image(file_content: bytes, size=(640, 640)) -> Image.Image:
  
#나중에 위에서 사이즈만 변경할것 이미지를 ai가 인식할 수 있는 숫자모델(tensor)로 변환해야함. 이때 torch사용.


    image = Image.open(io.BytesIO(file_content))
    return image.resize(size)