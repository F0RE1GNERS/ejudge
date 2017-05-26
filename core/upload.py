from config import *
import shutil
import zipfile


def upload_data(pid, source_path):
    try:
        target_dir = os.path.join(DATA_DIR, pid)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.mkdir(target_dir)
        source_zip = zipfile.ZipFile(source_path)
        source_zip.extractall(target_dir)
        # Permission control for data
        for file in os.listdir(target_dir):
            os.chmod(os.path.join(target_dir, file), 0o400)
        source_zip.close()
        return True
    except Exception as e:
        print(e)
        return False
