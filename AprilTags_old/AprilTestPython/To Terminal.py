import subprocess
import time


command = 'gz topic -t "/world/link/wrench" -m gz.msgs.EntityWrench  -p "entity: {name: \'box\', type: MODEL}, wrench: {force: {z: 0}}" '
result = subprocess.call(command, shell=True)

time.sleep(1)
print("0")

command = 'gz topic -t "/world/link/wrench" -m gz.msgs.EntityWrench  -p "entity: {name: \'box\', type: MODEL}, wrench: {force: {z: 10000}}" '
result = subprocess.call(command, shell=True)

time.sleep(1)
print("1")
command = 'gz topic -t "/world/link/wrench" -m gz.msgs.EntityWrench  -p "entity: {name: \'box\', type: MODEL}, wrench: {force: {z: -10000}}" '
result = subprocess.call(command, shell=True)


time.sleep(1)
print("2")
command = 'gz topic -t "/world/link/wrench" -m gz.msgs.EntityWrench  -p "entity: {name: \'box\', type: MODEL}, wrench: {force: {z: -10000}}" '
result = subprocess.call(command, shell=True)

time.sleep(0.5)
print("3")
command = 'gz topic -t "/world/link/wrench" -m gz.msgs.EntityWrench  -p "entity: {name: \'box\', type: MODEL}, wrench: {force: {z: 10000}}" '
result = subprocess.call(command, shell=True)

print("4")
#result.stdout
#result.stdout.decode('utf-8')