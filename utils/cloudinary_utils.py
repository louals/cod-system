import cloudinary
import cloudinary.uploader
from config import settings

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True
)

def upload_image(file_content, folder="products"):
    """Uploads an image to Cloudinary and returns the URL."""
    upload_result = cloudinary.uploader.upload(
        file_content,
        folder=folder,
        resource_type="auto"
    )
    return upload_result.get("secure_url")

def delete_image(public_id):
    """Deletes an image from Cloudinary."""
    cloudinary.uploader.destroy(public_id)
