import threading
import subprocess
import os
import time
import signal

# import pyautogui


def thread_function():
    # Start a program using subprocess and os
    program_name = ["gz", "sim"]
    # subprocess.Popen(program_name, shell=False)
    os.system("gz main")


if __name__ == "__main__":
    # Start a new thread
    # thread = threading.Thread(target=thread_function)
    # thread.daemon = True
    # thread.start()
    #
    # # Wait for 5 seconds
    # print("dd")
    # time.sleep(1)
    # print("Ddd")
    # # Terminate the thread
    # thread.join()

    # Open a new terminal window and execute a command
    command = 'gz sim'
    terminal = subprocess.Popen(['x-terminal-emulator', '-e', 'bash', '-c', command])
    # terminal = subprocess.Popen(['x-terminal-emulator', '-e', 'bash', '-c', command], stdin=subprocess.PIPE)

    # Open a new terminal window and execute a command
    # terminal = subprocess.Popen(
    #     ['x-terminal-emulator', '-e', 'bash', '-c', (command +'; trap "kill -INT $$" INT; read')],
    #     preexec_fn=os.setsid)

    # p = subprocess.Popen(["gz", "sim"], shell=False)

    print("dd")
    time.sleep(5)
    print("Ddd")

    # Send Ctrl+C signal to the terminal process
    # terminal.send_signal(subprocess.signal.SIGINT)


    # Terminate the terminal process
    # os.killpg(os.getpgid(terminal.pid), signal.SIGINT)
    terminal.terminate()
    # Wait for the terminal to close
    terminal.wait()
    print("wAit done")



    #
    # pyautogui.hotkey('ctrl','c')
    # p.wait()
    #
    # print("cc")
    #
    # p.terminate()
    # p.wait()