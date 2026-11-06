from typing import Optional, Tuple
import os
import uuid
from app.config import settings

# Initialize Supabase client if URL and KEY are configured
supabase_client = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY and "your-project" not in settings.SUPABASE_URL:
    try:
        from supabase import create_client, Client
        supabase_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
        )
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")

LOCAL_UPLOADS_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(LOCAL_UPLOADS_DIR, exist_ok=True)

class SupabaseStorageService:
    @staticmethod
    def upload_image(file_bytes: bytes, file_name: str, content_type: str = "image/jpeg") -> str:
        """
        Uploads image to Supabase Storage bucket.
        Falls back gracefully to local storage if Supabase credentials are not configured.
        Returns the accessible URI of the image.
        """
        file_ext = os.path.splitext(file_name)[1] or ".jpg"
        unique_file_name = f"{uuid.uuid4().hex}{file_ext}"

        if supabase_client:
            try:
                bucket_name = settings.SUPABASE_BUCKET_NAME
                # Attempt to upload to Supabase bucket
                res = supabase_client.storage.from_(bucket_name).upload(
                    path=unique_file_name,
                    file=file_bytes,
                    file_options={"content-type": content_type}
                )
                # Obtain public URL
                public_url = supabase_client.storage.from_(bucket_name).get_public_url(unique_file_name)
                return public_url
            except Exception as e:
                print(f"Supabase Storage upload warning: {e}. Falling back to local storage.")
        
        # Local storage fallback
        local_path = os.path.join(LOCAL_UPLOADS_DIR, unique_file_name)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        
        # Return URL pointing to API static endpoint
        return f"/api/v1/storage/file/{unique_file_name}"

