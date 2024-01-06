from utils.url import get_first_url
import subprocess
import json

def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    error = popen.stderr.read()
    yield "\n"+error+"\n"
    popen.stdout.close()
    popen.stderr.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)

async def get_url_probe_data(url: str) -> (tuple or None, str or None):
    """
    Returns probe data of url
    or None if not found
    :param url: str: url to probe
    :return: tuple(codec, bitrate), url or None, None
    """
    extracted_url = get_first_url(url)
    if extracted_url is None:
        return None, extracted_url

    # noinspection PyBroadException
    try:
        executable = 'ffmpeg'
        exe = executable[:2] + 'probe' if executable in ('ffmpeg', 'avconv') else executable
        args = [exe, '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'a:0', extracted_url]
        output = subprocess.check_output(args, timeout=20)
        codec = bitrate = None

        if output:
            data = json.loads(output)
            streamdata = data['streams'][0]

            codec = streamdata.get('codec_name')
            bitrate = int(streamdata.get('bit_rate', 0))
            bitrate = max(round(bitrate / 1000), 512)
    except Exception:
        codec, bitrate = None, None

    if codec and bitrate:
        return (codec, bitrate), extracted_url

    return None, extracted_url
