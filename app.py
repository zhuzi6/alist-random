from flask import Flask, render_template, request, jsonify
import requests
import json
import random
from urllib import parse
import time

app = Flask(__name__)

class AlistDownload:
    def __init__(self):
        self.urls = {
            "images": [
                {"name": "动漫1",
                 "url": "https://alist.hloli.eu.org/115/%E5%9B%BE%E7%89%87/%E4%B8%89%E6%AC%A1%E5%85%83/%E5%A5%97%E5%9B%BE/%E4%B8%AD/%E7%88%86%E6%9C%BA%E5%B0%91%E5%A5%B3%E5%96%B5%E5%B0%8F%E5%90%89"},
                # 添加其他图片链接
            ],
            "videos": [
                {"name": "视频1",
                 "url": "https://alist.hloli.eu.org/115/%E6%9D%82/%E8%A7%86%E9%A2%91/%E5%9B%BD%E4%BA%A7/%E6%8A%96%E9%9F%B3%E9%97%AA%E7%8E%B0"},
                # 添加其他视频链接
            ]
        }
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }

    def post(self, url, data) -> (bool, dict):
        error_number = 0
        while True:
            status_code = 0
            try:
                req = requests.post(url=url, data=json.dumps(data), headers=self.headers, timeout=15)
                status_code = req.status_code
                req_json = req.json()
                req.close()
            except:
                pass

            if status_code == 200:
                return True, req_json
            elif error_number > 2:
                return False, {}
            else:
                error_number += 1
                time.sleep(1)

    def get_list(self, path, host):
        url = host + "/api/fs/list"
        data = {"path": path, "password": "", "page": 1, "per_page": 0, "refresh": False}
        file_list = []
        req_type, req_json = self.post(url=url, data=data)
        if not req_type or req_json.get("code") != 200:
            return []

        content = req_json.get("data").get("content", [])
        for file_info in content:
            if file_info["is_dir"]:
                file_list.append({"is_dir": True, "path": path + "/" + file_info["name"], "name": file_info["name"]})
            else:
                file_download_url = host + "/d" + path + "/" + file_info["name"]
                sign = file_info.get("sign")
                if sign:
                    file_download_url += "?sign=" + sign
                file_list.append({"is_dir": False, "url": file_download_url, "name": file_info["name"]})

        return file_list

    def get_random_from_link(self, category, name):
        if category not in self.urls:
            return {}, []

        chosen = None
        for link in self.urls[category]:
            if link["name"] == name:
                chosen = link
                break

        if not chosen:
            return {}, []

        parseresult = parse.urlparse(chosen["url"])
        scheme = parseresult.scheme
        netloc = parseresult.netloc
        path = parse.unquote(parseresult.path)
        host = f"{scheme}://{netloc}"

        last_level_name = None
        while True:
            file_list = self.get_list(path, host)
            if not file_list:
                return {}, []
            dirs = [f for f in file_list if f["is_dir"]]
            files = [f for f in file_list if not f["is_dir"]]
            if not dirs:
                if files:
                    last_level_name = path.split("/")[-1] if path != "/" else "Root"
                return {"name": last_level_name}, files

            path = random.choice(dirs)["path"]

@app.route('/')
def index():
    return render_template("index.html", urls=AlistDownload().urls)

@app.route('/random_files', methods=["GET"])
def random_files():
    category = request.args.get('category', 'images')
    name = request.args.get('name')
    ad = AlistDownload()
    last_level, files = ad.get_random_from_link(category, name)
    return jsonify({"last_level": last_level, "files": files})

if __name__ == '__main__':
    from gevent import pywsgi
    server = pywsgi.WSGIServer(('0.0.0.0', 5001), app)
    server.serve_forever()