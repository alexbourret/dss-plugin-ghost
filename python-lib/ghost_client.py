import requests
import json
from mobiledoc import Mobiledoc
from ghost_auth import GhostAuth
from ghost_commons import get_instance_url_from_config
try:
    from BytesIO import BytesIO  # for Python 2
except ImportError:
    from io import BytesIO  # for Python 3


class GhostClient():
    def __init__(self, config):
        self.session = requests.Session
        self.session.auth = GhostAuth(config)
        self.server_url = get_instance_url_from_config(config)
    # upload_image(image_url, session, server_url, title)
    
    def upload_image_from_url(self, image_url, title):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            response = requests.get(image_url)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    tmp_file.write(chunk)
            
            with tempfile.NamedTemporaryFile(delete=True, suffix = ".jpg") as tmp_jpg_file:
                tmp_jpg_file = jpeg_compress(tmp_file, tmp_jpg_file)
                # could be that 2 files can't have the same name on the ghost side...
                # Keep that in mind where errors occur
                files = {'file': (slugify(title)+".jpg", open(tmp_jpg_file.name, 'rb'), 'image/jpeg')}
                response = self.session.post(
                    "{}/ghost/api/admin/images/upload/".format(self.server_url),
                    files=files
                )
                print("ALX:response.content={}".format(response.content))
                # {'images': [{'url': 'https://the-expert.in/content/images/2024/10/test.png', 'ref': None}]}
                json_response = response.json()
                images = json_response.get("images", [{}])
                url = images[0].get("url")
                print("ALX:response={}".format(response.json()))
                return url

    def upload_post(self, title, text, excerpt, image_url):
        mobiledoc = Mobiledoc()
        image_ghost_url = None
        if image_url:
            image_ghost_url = self.upload_image_from_url(image_url, title)
        mobiledoc.add_formatted_text(text)
        mobiledoc = mobiledoc.serialize()
        post = {
            "title": "{}".format(title),
            "mobiledoc": json.dumps(mobiledoc)
        }
        if excerpt:
            post["custom_excerpt"] = "{}".format(excerpt)
        if image_ghost_url:
            post['feature_image'] = image_ghost_url
        data = {
            "posts": [
                post
            ]
        }
        try:
            print("ALX:data={}".format(data))
            response = self.session.post(
                url="{}/ghost/api/admin/posts/".format(self.server_url),
                json=data
            )
        except Exception as error:
            raise Exception("Connection error: {}".format(error))
        answer = response.json()
        return answer.get("posts", [])[0]


def jpeg_compress(tmp_file, tmp_jpg_file):
    from PIL import Image
    tmp_file.flush()
    tmp_file.seek(0)
    raw_image = Image.open(tmp_file.name)
    buffer = BytesIO()
    raw_image.save(buffer, "JPEG", quality=95)
    tmp_jpg_file.write(buffer.getbuffer())
    tmp_jpg_file.flush()
    tmp_jpg_file.seek(0)
    return tmp_jpg_file


def slugify(title):
    VALID_CHAR = "abcdefghijklmnopqrstuvwxyz-0123456789"
    title = title.lower()
    slugified = ""
    for char in title:
        if char not in VALID_CHAR:
             slugified += '-'
        else:
            slugified += char
    return slugified
