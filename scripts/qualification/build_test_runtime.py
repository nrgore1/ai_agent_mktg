import json,subprocess
from pathlib import Path
p=Path.home()/'agentvire-wave-tests-20261101/runtime';p.mkdir(parents=True,exist_ok=True)
image=json.loads(subprocess.check_output(['docker','inspect','jodibana-web-1']))[0]['Image']
subprocess.run(['docker','tag',image,'agentvire-wave-jodi-base:20261101'],check=True)
(p/'Dockerfile').write_text('FROM agentvire-wave-jodi-base:20261101\nUSER root\nRUN pip install --no-cache-dir pytest==8.3.5 pytest-django==4.11.1\n')
subprocess.run(['docker','build','-t','agentvire-wave-jodi-tests:20261101','.'],cwd=p,check=True)
