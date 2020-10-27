import distutils.dir_util
import glob
import hashlib
import os
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import urllib.request
from os import path

import certifi
import time

CAIRO_VERSION = "1.16.0"
CAIRO_TARBALL = "cairo-1.16.0.tar.xz"
PANGO_TARBALL = "pango-1.47.0.tar.xz"
PANGO_VERSION = "1.38.0"
GDKPIXBUF_VERSION = "2.25.0"

root_dir = "."
build_dir = path.join(root_dir, "build")
prefix_dir = path.abspath(path.join(build_dir, "local"))
lib_dir = path.join(prefix_dir, "lib")
build_dir_cairo = path.join(build_dir, CAIRO_TARBALL.split(".tar")[0], "build")
build_dir_pango = path.join(build_dir, PANGO_TARBALL.split(".tar")[0], "build")

distutils.dir_util.mkpath(build_dir)
distutils.dir_util.mkpath(prefix_dir)
distutils.dir_util.mkpath(build_dir_cairo)

BITS = sys.argv[1]


def shell(cmd, cwd=None):
    """Run a shell command specified by cmd string."""
    call = subprocess.Popen(
        cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    output, err = call.communicate()
    print(output.decode())
    if err:
        print(err.decode())
    return output.decode()


def download(url, target_path):
    """Download url to target_path."""
    print("Downloading {}...".format(url))
    # Create a custom context and fill in certifi CAs because GitHub Action's macOS CI
    # runners don't seem to have certificates installed, leading to a download
    # failure...
    context = ssl.create_default_context(
        ssl.Purpose.SERVER_AUTH, cafile=certifi.where()
    )
    with urllib.request.urlopen(url, context=context) as response, open(
        target_path, "wb"
    ) as f:
        shutil.copyfileobj(response, f)


def extract_zst(filename, target_dir):
    print(f"Extracting {filename} to {target_dir}...")
    filename = path.abspath(filename)
    shell(f"zstd -d {filename}", cwd=path.join(filename, os.pardir))
    tar_file = filename[:-4]
    with tarfile.open(tar_file, "r:*") as tb:
        tb.extractall(target_dir)


def extract_xz(filename, target_dir):
    print(f"Extracting {filename} to {target_dir}...")
    filename = path.abspath(filename)
    with tarfile.open(filename, "r:xz") as tb:
        tb.extractall(target_dir)


if sys.platform == "win32":
    print("Getting Required Dependency From Msys2")
    if BITS == 32:
        MSYSTEM = "i686"
        print("Getting 32-bit environment")
    else:
        MSYSTEM = "x86_64"
        print("Getting 64-bit environment")

    def get_files(lib):
        regexFile = re.compile(r'"https:\/\/repo\.msys2\.org\/mingw\/.*\.tar\.zst"')
        output = shell(f"pactree -uls mingw-w64-{MSYSTEM}-{lib}")
        packages = [i.strip() for i in output.split()]
        for package in packages:
            print(f"Getting {package}")
            url = f"https://packages.msys2.org/package/{package}"
            import urllib.request

            with urllib.request.urlopen(url) as response:
                res = str(response.read())

            fileUrlSearch = regexFile.search(res)
            if fileUrlSearch:
                fileUrl = fileUrlSearch.group(0)
            else:
                regexFile_xz = re.compile(
                    r'"https:\/\/repo\.msys2\.org\/mingw\/.*\.tar\.xz"'
                )
                fileUrlSearch = regexFile_xz.search(res)
                fileUrl = fileUrlSearch.group(0)
            fileUrl = fileUrl.split('"')[1]
            filename = fileUrl.split("/")[-1]
            download(fileUrl, path.join(build_dir, filename))
            if filename.endswith("xz"):
                extract_xz(
                    path.join(build_dir, filename), path.join(build_dir_cairo, package)
                )
            else:
                extract_zst(
                    path.join(build_dir, filename), path.join(build_dir_cairo, package)
                )
            file_dir = glob.glob(
                path.join(build_dir_cairo, package, f"mingw{BITS}", "bin", "*.dll")
            )
            for i in file_dir:
                shutil.move(i, prefix_dir)
        time.sleep(3)

    get_files("cairo")
    get_files("pango")
