import dataiku
import pandas
import requests
import json
try:
    from BytesIO import BytesIO  # for Python 2
except ImportError:
    from io import BytesIO  # for Python 3

from dataiku.customrecipe import get_input_names_for_role
from dataiku.customrecipe import get_output_names_for_role
from dataiku.customrecipe import get_recipe_config

from ghost_commons import (get_instance_url_from_config)
from ghost_auth import GhostAuth
from mobiledoc import Mobiledoc
from ghost_client import GhostClient


def upload_image(image_url, session, server_url, title):
    import tempfile
    with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
        response = requests.get(image_url)
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                tmp_file.write(chunk)
        
        with tempfile.NamedTemporaryFile(delete=True, suffix = ".jpg") as tmp_jpg_file:
            tmp_jpg_file = jpeg_compress(tmp_file, tmp_jpg_file)
            print("ALX:file name ={}".format(tmp_jpg_file.name))
            # could be that 2 files can't have the same name on the ghost side...
            # Keep that in mind where errors occur
            files = {'file': (slugify(title)+".jpg", open(tmp_jpg_file.name, 'rb'), 'image/jpeg')}
            response = session.post(
                url="{}/ghost/api/admin/images/upload/".format(server_url),
                files=files
            )
            print("ALX:response.content={}".format(response.content))
            # {'images': [{'url': 'https://the-expert.in/content/images/2024/10/test.png', 'ref': None}]}
            json_response = response.json()
            images = json_response.get("images", [{}])
            url = images[0].get("url")
            print("ALX:response={}".format(response.json()))
            return url


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


input_A_names = get_input_names_for_role('input_A_role')
input_A_datasets = [dataiku.Dataset(name) for name in input_A_names]
output_A_names = get_output_names_for_role('main_output')
config = get_recipe_config()
prompts_df = input_A_datasets[0].get_dataframe()
server_url = get_instance_url_from_config(config)
output = dataiku.Dataset(output_A_names[0])

first_dataframe = True
prompt_source = config.get("prompt_source", "column")
prompt_source = config.get("prompt_source", "column")
title_column = config.get("title_column")
excerpt_column = config.get("excerpt_column")
text_column = config.get("text_column")
image_url_column = config.get("image_url_column")
image_ghost_url = None
session = requests.Session()
session.auth = GhostAuth(config)
# client = GhostClient(config)

with output.get_writer() as writer:
    unnested_items_rows = []
    for index, input_parameters_row in prompts_df.iterrows():
        row = input_parameters_row.to_dict()
        mobiledoc = Mobiledoc()
        title = row.get(title_column)
        text = row.get(text_column)
        excerpt = None
        if excerpt_column:
            excerpt = row.get(excerpt_column)
        image_url = None
        if image_url_column:
            image_url = row.get(image_url_column)
            image_ghost_url = upload_image(image_url, session, server_url, title)
        mobiledoc.add_formatted_text(text)
        mobiledoc = mobiledoc.serialize()
        post = {
            "title": "{}".format(title),
            "custom_excerpt": "{}".format(excerpt),
            "mobiledoc": json.dumps(mobiledoc)
        }
        if image_ghost_url:
            post['feature_image'] = image_ghost_url
        data = {
            "posts": [
                post
            ]
        }
        try:
            print("ALX:data={}".format(data))
            response = session.post(
                url="{}/ghost/api/admin/posts/".format(server_url),
                json=data
            )
        except Exception as error:
            raise Exception("Connection error: {}".format(error))
        answer = response.json()
        row['ghost_response'] = answer.get("posts", [])[0]
        # row['ghost_response'] = client.upload_post(title, text, excerpt, image_url)
        unnested_items_rows.append(row)
    unnested_items_rows = pandas.DataFrame(unnested_items_rows)
    if first_dataframe:
        output.write_schema_from_dataframe(unnested_items_rows)
        first_dataframe = False
    if not unnested_items_rows.empty:
        writer.write_dataframe(unnested_items_rows)
