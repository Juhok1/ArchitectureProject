import os
import multiprocessing
import sysv_ipc
import random

lock = multiprocessing.Lock()
NUM_CHILDREN = 4  # Amount of childprocesses
SHM_SIZE = NUM_CHILDREN * 8  # Memory space we need (8 tavua per int64)

def ftok():
    numberseries = ""
    for _ in range(6):
        numbers = [0,1,2,3,4,5,6,7,8,9]
        i = random.choice(numbers)
        numberseries += str(i)
    return int(numberseries)

SHM_KEY = ftok()

def scheduler(event):
    
    shm = sysv_ipc.SharedMemory(
        SHM_KEY, sysv_ipc.IPC_CREAT | sysv_ipc.IPC_EXCL, size=1024, mode=0o666
        )

        


    # Waiting for init -signal
    event.wait()

    # Reading from memory and decoding infromation
    shm.attach()
    data = shm.read(SHM_SIZE).decode('utf-8').strip('\x00')  # Raeding data
    numbers = list(map(int, data.split(',')))  # Converting list to numbers
    numbers = sorted(numbers)
    print("Scheduler received numbers:", numbers)

    # removing memory segment
    shm.detach()
    shm.remove()

def child_process(pipe):
    number = int(input("Give the number between 0-19: "))
    pipe.send(number)  # Lähetetään numero parent-prosessille
    pipe.close()       # Suljetaan putki lapsiprosessissa

def init(pipes, event):
    numbers = []
    i = 0
    # Creating childprocesses
    for i in range(NUM_CHILDREN):
        pid = os.fork()  # Let's use fork() rightly

        if pid == 0:  # Childprocess
            child_pipe = pipes[i][1]  # Child using pipe to send
            child_process(child_pipe)
            os._exit(0)  # Childprocess ending

    # Init process reading numbers from shared memory
    for i in range(NUM_CHILDREN):
        parent_pipe = pipes[i][0]  # init using pipe to receive 
        received_number = parent_pipe.recv()  # reading numbers from child process
        numbers.append(received_number)

    # Joining to shared memory
    try:
        shm = sysv_ipc.SharedMemory(SHM_KEY)
        shm.attach()
        shm.write(','.join(map(str, numbers)).encode('utf-8'))  # chanching numbers to map
        shm.detach()
    except Exception as e:
        print("Error writing to shared memory:", e)

    # Notifying to scheduler that init is ready
    event.set()

    
if __name__ == "__main__":
    # Creating pipe for each child process
    pipes = [multiprocessing.Pipe() for _ in range(NUM_CHILDREN)]

    # Creating synchronizing event
    event = multiprocessing.Event()
    

    # Creating scheduler process
    scheduler_process = multiprocessing.Process(target=scheduler, args=(event,))
    scheduler_process.start()

    # Calling init function
    init(pipes, event)

    # Waiting that scheduler is ready
    scheduler_process.join()