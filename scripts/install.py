import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

# check if we on raspberry pi
def is_raspi():
    try:
        with open('/proc/cpuinfo') as f:
            return 'Raspberry Pi' in f.read()
    except:
        return False

# check if we on BINDOWS 
def is_windows():
    return platform.system().lower() == 'windows'

# run le command
def run_command(command):
    try:
        if isinstance(command, str):
            command = command.split()

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        if process.returncode != 0:
            print("UH OHH STINKY ERROR:")
            print(process.stderr.read())
            return False
        return True
    except Exception as e:
        print(f"Error executing BRUH COMMAND: {e}")
        return False

# virtual environment function
def setup_venv():
    venv_path = 'venv'

    # create if no exist
    if not os.path.exists(venv_path):
        print("Making venv ...")
        try:
            subprocess.check_call([sys.executable, '-m', 'venv', venv_path])

            # set perms
            if not is_windows():
                for root, dirs, files in os.walk(venv_path):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o755)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o755)
        except subprocess.CalledProcessError:
            print("Failed to make dumb dumb imaginary environment")
            return False
        
    if is_windows():
        return os.path.join(venv_path, 'Scripts', 'python')
    else:
        return os.path.join(venv_path, 'bin', 'python')    

# now we install le package
def install(python_path):
    if is_raspi():
        req = [
            'gpiozero',
            'python-dotenv'
        ]
    else:
        req = [
            'opencv-python',
            'numpy',
            'Pillow',
            'python-dotenv'
        ]           

    with open('temp_reqs.txt', 'w') as f:
        f.write('\n'.join(req))

    # RUN
    print("Installing packages ...")
    success = run_command([python_path, '-m', 'pip', 'install', '-r', 'temp_reqs.txt'])

    # clean
    os.remove('temp_reqs.txt')
    return success

# create env file
def setup_env():
    if not os.path.exists('.env'):
        print("Creating env file ...")
        shutil.copy('.env.example', '.env')
        print("NOW EDIT IT BITCH!")

def main():
    print("=== BUCKSHIT TASER INSTALL SCRIPT ===")

    # make sure your dumbass got python
    if sys.version_info < (3, 8):
        print("Update yo python")
        sys.exit(1)

    # detect platform
    if is_raspi():
        print("Detected platform Raspberry Pi")
    elif is_windows():
        print("Detected platform Windows")
    else:
        print("Detected Unix platform!")

    # setup venv
    activate_script = setup_venv()
    if not activate_script:
        sys.exit(1)

    # install packages
    if not install(activate_script):
        print("Package installation failed!")
        sys.exit(1)

    # setup env file
    setup_env()

    print("\nInstallation success!")
    print("\nNext steps:")
    print("1. Edit env file")
    if is_raspi():
        print("2. Run receiver.py")
    else:
        print("2. Run bigbrother.py")

main()
