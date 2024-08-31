from blacksheep import Request, json
from datetime import datetime
import uuid
from blacksheep.exceptions import BadRequest, HTTPException
from pathlib import Path
from blacksheep import Application
from essentials.folders import ensure_folder


# ensure_folder('Static/out')


class MaxBodyExceededError(HTTPException):
    def __init__(self, max_size: int):
        super().__init__(413, "The request body exceeds the maximum size.")
        self.max_size = max_size
    


async def read_stream(request: Request, max_body_size: int = 1500000):
    """
        Reads a request stream, up to a maximum body length (default to 1.5 MB).
    """
    current_length = 0
    async for chunk in request.stream():
        current_length += len(chunk)

        if max_body_size > -1 and current_length > max_body_size:
            raise MaxBodyExceededError(max_body_size)
        
        yield chunk


# Upload bank Account Docs
async def save_merchant_bank_doc(file, request: Request, max_size: int = 1000000):
    file_data = file

    for part in file_data:
        file_bytes = part.data
        original_file_name  = part.file_name.decode()
        file_size = len(file_bytes)


    if file_size > max_size:
        return 'File size exceeds the maximum allowed size'
    
    file_extension = original_file_name.split('.')[-1]

    file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4()}.{file_extension}"

    if not file_name:
        return BadRequest("File name is missing")

    file_path = Path("Static/MerchantBankDoc") / file_name

    try:
        with open(file_path, mode="wb") as user_files:
            user_files.write(file_bytes)

    except MaxBodyExceededError:
        file_path.unlink()
        raise
    
    return str(file_path.relative_to(Path("Static")))



# Upload merchant profile Picture by Merchant
async def upload_merchant_profile_Image(file, max_size: int = 2000000):

    file_data = file

    for part in file_data:
        file_bytes = part.data
        original_file_name  = part.file_name.decode()
        file_size = len(file_bytes)

    if file_size > max_size:
        return 'File size exceeds the maximum allowed size'
    
    file_extension = original_file_name.split('.')[-1]

    file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4()}.{file_extension}"

    if not file_name:
        return BadRequest("File name is missing")
    
    file_path = Path("Static/MerchantProfilePic") / file_name

    try:
        with open(file_path, mode="wb") as user_files:
            user_files.write(file_bytes)

    except MaxBodyExceededError:
        file_path.unlink()
        raise

    return str(file_path.relative_to(Path("Static")))



#Delete previously uploaded image
def delete_old_file(file_path: str):
    path = Path(file_path)
    if path.exists():
        path.unlink()



def configure_upload_file(app: Application):

    @app.exception_handler(413)
    async def handle_max_body_size(app, request, exc: MaxBodyExceededError):
        return json({"error": "Maximum body size exceeded", "max_size": exc.max_size})




# @app.exception_handler(413)
# async def handle_max_body_size(app, request, exc: MaxBodyExceededError):
#     return json({"error": "Maximum body size exceeded", "max_size": exc.max_size})



