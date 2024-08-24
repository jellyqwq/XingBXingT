import io
from typing import Union
import zipfile
import json
import requests
from urllib.parse import urlparse
import os
import hashlib

def read_env(jar_file: Union[str, io.BytesIO]) -> dict:
    """
    从给定的 jar_file 中提取运行环境。
    
    :param jar_file: jar包路径或io
    :return: 环境结构
    """
    # 创建 ZipFile 对象
    with zipfile.ZipFile(jar_file, 'r') as jar_ref:
        with jar_ref.open('fabric.mod.json') as file:
            content = file.read()
            jsonP = json.loads(content.decode('utf-8'))
            env = jsonP['environment']
            if env == '*':
                return {
                    "server": "required",
                    "client": "required"
                }
            elif env == 'client':
                return {
                    "server": "unsupported",
                    "client": "required"
                }
            elif env == 'server':
                return {
                    "server": "required",
                    "client": "unsupported"
                }
            else:
                return {}

def extract_filename_from_url(url: str) -> str:
    """
    从给定的 URL 中提取文件名。
    
    :param url: 完整的 URL
    :return: 文件名
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)
    return filename

def calculate_sha1_and_sha512(byte_data: bytes) -> tuple:
    """
    计算 bytes 对象的 SHA-1 和 SHA-512 散列值。
    
    :param byte_data: bytes 对象
    :return: SHA-1 和 SHA-512 散列值的元组
    """
    sha1_hash = hashlib.sha1(byte_data).hexdigest()
    sha512_hash = hashlib.sha512(byte_data).hexdigest()
    return {
        "sha1": sha1_hash,
        "sha512": sha512_hash
    }

def calculate_stream_size(stream: io.IOBase) -> int:
    """
    计算文件流的大小。
    
    :param stream: 文件流对象
    :return: 文件流的大小（以字节为单位）
    """
    original_position = stream.tell()  # 记录当前的位置
    stream.seek(0, io.SEEK_END)  # 移动到文件末尾
    size = stream.tell()  # 获取当前位置，即文件大小
    stream.seek(original_position)  # 恢复原始位置
    return size

def generate_file_block(link) -> str:
    """
    从给定的 URL 中下载文件并返回文件计算信息。
    
    :param url: 完整的 URL
    :return: 文件块对象
    """
    res = requests.get(link)
    filename = extract_filename_from_url(link)
    file_obj = res.content
    return {
      "path": f"mods/{filename}",
      "hashes": calculate_sha1_and_sha512(file_obj),
      "env": read_env(io.BytesIO(res.content)),
      "downloads": [
        link
      ],
      "fileSize": len(file_obj)
    }

def merge_mods(versionId, name):
    with open('modrinth.index.json', 'r', encoding='utf-8') as f:
        modrinth_index_json = json.loads(f.read())
    files = modrinth_index_json['files']
    filenames = [os.path.basename(i['path']) for i in files]
    modrinth_index_json['name'] = name
    modrinth_index_json['versionId'] = versionId
    
    with open('modlist.txt', 'r', encoding='utf-8') as f:
        unmerge_files = [i.strip('\n') for i in f.readlines()]

    for unmerge_file in unmerge_files:
        unmerge_filename = extract_filename_from_url(unmerge_file)
        if unmerge_filename in filenames:
            print(f'{unmerge_filename} alrealy exist.')
            continue
        else:
            modrinth_index_json['files'].append(generate_file_block(unmerge_file))
            print(f'{unmerge_filename} add to cache of modrinth_index_json.')

    with open('modrinth.index.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(modrinth_index_json, indent=4, ensure_ascii=False))
    print('files merging completed.')

if __name__ == '__main__':
    merge_mods(
        versionId='v0.0.3-fabric-mc1.20.4',
        name='XingBXingT on Minecraft 1.20.4 (Fabric)'
    )