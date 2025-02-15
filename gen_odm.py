#!/usr/bin/python3
import os
import sys
import re
import time
from subprocess import run
from tqdm import tqdm
from pyodm import Node


# unset http_proxy https_proxy
# docker rm -v $(docker ps -aq)
# docker cp /home/user/cropper.py docker_id:/code/opendm/
# docker exec -u root -it docker_id /bin/bash
class Gen_Odm:
    datas = {"fast-orthophoto": True}

    def __init__(self, hostname="127.0.0.1", port=3000):
        self.n_odm = Node(hostname, port)
        self.docker_id = self.get_docker_id()
        assert self.docker_id != None, "未找到nodeodm容器，请确认是否启动"

    def get_docker_id(self):
        proc = run("docker ps",
                   shell=True,
                   capture_output=True,
                   universal_newlines=True)
        for txt in proc.stdout.split("\n"):
            result = re.search("(.*)opendronemap/nodeodm", txt)
            if result:
                return result.group(1).strip()
        return None

    def gen_orthophoto(self, image_dir):
        images = [
            os.path.join(image_dir, image) for image in os.listdir(image_dir)
        ]
        # print(images)
        self.task = self.n_odm.create_task(images, options=self.datas)
        print("创建任务%s" % self.task.uuid)
        print("正在处理任务......")
        pbar = tqdm(total=100, unit="%", colour='green', unit_scale=True)
        processing = 0
        while processing < 100:
            time.sleep(0.5)
            info = self.task.info()
            pbar.update(info.progress - processing)
            processing = info.progress
            if info.last_error:
                print("ERROR ", info.last_error)
        pbar.close()
        self.task.wait_for_completion()
        self.download_result(image_dir)

    def download_result(self, image_dir):
        print("处理完成,下载文件至%s......" % image_dir)
        dl_dir = os.path.join(image_dir, "result")
        if not os.path.exists(dl_dir):
            os.mkdir(dl_dir)
        resp = self.task.get("/task/%s/download/all.zip" % self.task.uuid,
                             stream=True)
        file_size = int(resp.headers.get('content-length', 0))
        p_bar = tqdm(total=file_size,
                     unit='iB',
                     colour='green',
                     unit_scale=True)
        with open(os.path.join(dl_dir, "result.zip"), 'wb') as file:
            for data in resp.iter_content(chunk_size=1024):
                p_bar.update(len(data))
                file.write(data)
        p_bar.close()
        proc = run(
            "docker cp %s:/var/www/data/%s/odm_orthophoto/odm_orthophoto.original.tif %s"
            % (self.docker_id, self.task.uuid, dl_dir),
            shell=True)


if __name__ == "__main__":
    node_odm = Gen_Odm()
    node_odm.gen_orthophoto(sys.argv[1])
